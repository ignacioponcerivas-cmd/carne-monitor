"""Punto de entrada: inicia el servidor de monitoreo en http://localhost:8000"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import uvicorn

if __name__ == "__main__":
    print("=" * 50)
    print("  Carne Monitor — http://localhost:8000")
    print("=" * 50)
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
