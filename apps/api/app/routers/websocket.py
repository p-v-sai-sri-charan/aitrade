from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws_manager import order_updates_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/orders")
async def orders_ws(websocket: WebSocket) -> None:
    """Pushes an ORDER_UPDATE message whenever an order is confirmed or
    cancelled. Clients that only need polling can ignore this and use
    GET /api/v1/orders instead -- this is a live-update convenience layer.
    """
    await order_updates_manager.connect(websocket)
    try:
        while True:
            # We don't expect client -> server messages, but reading keeps
            # the connection alive and lets us detect disconnects promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        order_updates_manager.disconnect(websocket)
