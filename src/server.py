"""FastAPI server — dashboard de monitoreo del scraper de carnes."""
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.scraper_runner import ScraperRunner
from src.utils.helpers import setup_logging

setup_logging("INFO")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
CONFIG_PATH = BASE_DIR / "config" / "sites.json"

app = FastAPI(title="Carne Monitor")
runner = ScraperRunner()

# Serve static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ #
# HTTP endpoints
# ------------------------------------------------------------------ #

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/api/status")
async def get_status():
    return JSONResponse(runner.get_status())


@app.get("/api/products")
async def get_products():
    return JSONResponse({"products": runner.get_products()})


@app.get("/api/config")
async def get_config():
    cfg = _load_config()
    return JSONResponse({
        "sites": list(cfg["sites"].keys()),
        "site_names": {k: v["name"] for k, v in cfg["sites"].items()},
        "categories": cfg["categories"],
    })


@app.post("/api/scrape/start")
async def start_scrape(body: dict = None):
    body = body or {}
    config = _load_config()
    loop = asyncio.get_event_loop()

    started = runner.start(
        config=config,
        sites=body.get("sites") or None,
        categories=body.get("categories") or None,
        headless=body.get("headless", True),
        loop=loop,
    )
    if started:
        logger.info("Scraping iniciado desde dashboard")
        return JSONResponse({"ok": True, "message": "Scraping iniciado"})
    return JSONResponse({"ok": False, "message": "Ya hay un scraping en curso"}, status_code=409)


@app.post("/api/scrape/stop")
async def stop_scrape():
    runner.stop()
    return JSONResponse({"ok": True, "message": "Señal de stop enviada"})


@app.post("/api/fresqui/reload")
async def reload_fresqui():
    count = runner.reload_fresqui()
    return JSONResponse({"ok": True, "count": count, "message": f"{count} productos Fresqui recargados"})


# ------------------------------------------------------------------ #
# WebSocket
# ------------------------------------------------------------------ #

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()
    runner.add_listener(queue)

    # Send current status on connect
    await websocket.send_text(json.dumps({"type": "status", **runner.get_status()}))

    try:
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_text(msg)
            except asyncio.TimeoutError:
                # Heartbeat to keep connection alive
                await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        pass
    finally:
        runner.remove_listener(queue)


# ------------------------------------------------------------------ #
# Entry point
# ------------------------------------------------------------------ #

def main():
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
