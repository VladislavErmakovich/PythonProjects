from fastapi import WebSocket
from typing import List

class Connection_Manager:
    def __init__(self):
        self.active_connections : List[WebSocket] = [] # список активных соединений

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    def get_count(self):
        return len(self.active_connections)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)

manager = Connection_Manager()
