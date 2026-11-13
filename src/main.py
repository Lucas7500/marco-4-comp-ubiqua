from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from config import Settings
from models.live import Live
from routers import channels, health, readings

HTTP_TIMEOUT_SECONDS: int = 10


def create_app(
    settings: Settings | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = settings if settings is not None else Settings.load()
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT_SECONDS, transport=transport
        ) as client:
            app.state.http = client
            app.state.live = Live(app.state.settings)
            try:
                app.state.live.start()
                yield
            finally:
                await app.state.live.stop()

    app: FastAPI = FastAPI(
        title="Jacaré Alecrim",
        description=(
            "API de leitura dos sensores e atuadores. "
            "Teste /health e /api/v1/channels sem credenciais. "
            "Para consultar canais privados, configure as Read API Keys no .env. "
            "WebSocket disponível em /api/v1/ws/readings; teste com um cliente WebSocket."
        ),
        swagger_ui_parameters={"tryItOutEnabled": True},
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(channels.router)
    app.include_router(readings.router)
    return app


app: FastAPI = create_app()
