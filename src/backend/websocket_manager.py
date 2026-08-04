"""
Gerenciador de transmissoes WebSocket para o terminal frontend em tempo real.
Suporta chamadas thread-safe a partir de worker threads.
"""

import asyncio
from typing import List, Optional
from fastapi import WebSocket


class WebSocketManager:
    """
    Gerencia conexoes ativas de WebSockets e transmite mensagens de log em tempo real.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.main_loop: Optional[asyncio.AbstractEventLoop] = None

    def set_main_loop(self, loop: asyncio.AbstractEventLoop):
        """
        Registra o event loop principal da aplicacao FastAPI.
        """
        self.main_loop = loop

    async def connect(self, websocket: WebSocket):
        if websocket not in self.active_connections:
            self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_log(self, message: str, level: str = "INFO"):
        """
        Envia uma linha de log formatada para todos os clientes conectados.
        """
        formatted = f"[{level}] {message}"
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(formatted)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    def send_log_threadsafe(self, message: str, level: str = "INFO"):
        """
        Envia logs de forma thread-safe a partir de qualquer thread secundária.
        """
        if self.main_loop and self.main_loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(
                    self.broadcast_log(message, level),
                    self.main_loop
                )
            except Exception:
                pass


# Instancia global compartilhada
ws_manager = WebSocketManager()
