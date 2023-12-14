from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)
        print("Connect new websocket", len(self.active_connections))

    async def disconnect(self, ws: WebSocket):
        self.active_connections.remove(ws)
        print("Connection removed", len(self.active_connections))

    async def broadcast(self, data):
        print(f'{data=}')
        for connection in self.active_connections:
            await connection.send_json(data)


manager = ConnectionManager()
