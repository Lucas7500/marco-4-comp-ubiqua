from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router: APIRouter = APIRouter(prefix="/api/v1/ws")


@router.websocket("/readings")
async def websocket(socket: WebSocket) -> None:
    await socket.accept()
    socket.app.state.live.sockets.add(socket)
    try:
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        socket.app.state.live.sockets.discard(socket)
