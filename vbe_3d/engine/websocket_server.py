import asyncio
import websockets
import json
from typing import Set, Dict, Any

class WebSocketServer:
    """WebSocket server for real-time communication with WebGL clients."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """Initialize the WebSocket server.
        
        Args:
            host: The host address to bind to.
            port: The port number to listen on.
        """
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        
    async def start(self):
        """Start the WebSocket server."""
        self.server = await websockets.serve(self._handle_client, self.host, self.port)
        print(f"WebSocket server started at ws://{self.host}:{self.port}")
        
    async def stop(self):
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
    async def _handle_client(self, websocket: websockets.WebSocketServerProtocol):
        """Handle a new WebSocket client connection.
        
        Args:
            websocket: The WebSocket connection.
        """
        print(f"New WebSocket client connected. Total clients: {len(self.clients) + 1}")
        self.clients.add(websocket)
        try:
            async for message in websocket:
                # Handle any incoming messages from clients if needed
                pass
        finally:
            self.clients.remove(websocket)
            print(f"WebSocket client disconnected. Remaining clients: {len(self.clients)}")
            
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast.
        """
        if not self.clients:
            print("No WebSocket clients connected")
            return
            
        message_str = json.dumps(message)
        print(f"Broadcasting to {len(self.clients)} clients: {message_str}")
        await asyncio.gather(
            *[client.send(message_str) for client in self.clients]
        ) 