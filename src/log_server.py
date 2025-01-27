import asyncio
import websockets
import sys
from io import StringIO

# Global set to keep track of connected clients
clients = set()

async def register(websocket):
    clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        clients.remove(websocket)

async def broadcast_message(message):
    if clients:
        await asyncio.gather(
            *[client.send(message) for client in clients]
        )

class WebSocketLogHandler(StringIO):
    def write(self, message):
        if message.strip():  # Only send non-empty messages
            asyncio.run(broadcast_message(message))
        return super().write(message)

async def main():
    # Redirect stdout to our custom handler
    sys.stdout = WebSocketLogHandler()
    
    # Start the WebSocket server
    async with websockets.serve(register, "0.0.0.0", 8501):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main()) 