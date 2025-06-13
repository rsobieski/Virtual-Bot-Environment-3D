from typing import Any, Dict, Optional, Union, Tuple
import json
from pathlib import Path
import http.server
import socketserver
import threading
import webbrowser
import asyncio
from abc import ABC, abstractmethod
from .websocket_server import WebSocketServer
from .base import BaseEngine
import os
import time

def vec3_to_list(vec3_or_tuple):
    """Convert a Vec3 object or tuple to a list of coordinates."""
    if isinstance(vec3_or_tuple, (tuple, list)):
        return list(vec3_or_tuple)
    return [vec3_or_tuple.x, vec3_or_tuple.y, vec3_or_tuple.z]

class WebGLEngine(BaseEngine):
    """WebGL-based 3D visualization engine implementation using Three.js.
    
    This engine uses Three.js to provide 3D visualization capabilities
    for the simulation world in a web browser.
    """
    
    def __init__(self, port: int = 8000, ws_port: int = 8765, enable_camera_controls: bool = True):
        """Initialize the WebGL engine.
        
        Args:
            port: The port number to run the web server on.
            ws_port: The port number to run the WebSocket server on.
            enable_camera_controls: Whether to enable camera controls for user interaction.
        """
        self.port = port
        self.ws_port = ws_port
        self.enable_camera_controls = enable_camera_controls
        self.entities: Dict[Any, Dict] = {}
        self.world_updater: Optional[Any] = None
        self.loop = asyncio.get_event_loop()
        self.message_queue = asyncio.Queue()
        
        # Use the existing web visualization directory
        self.web_dir = Path("examples/web_visualization")
        if not self.web_dir.exists():
            raise RuntimeError(f"Web visualization directory not found at {self.web_dir}")
        
        # Initialize WebSocket server
        self.ws_server = WebSocketServer(port=ws_port)
        
        # Start web server
        self.server_thread = threading.Thread(target=self._start_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Start message processor
        self.loop.create_task(self._process_messages())
    
    async def start(self):
        """Start the engine and open the browser."""
        # Start WebSocket server
        await self._start_ws_server()
        
        # Wait a moment for the server to be ready
        await asyncio.sleep(1)
        
        # Open browser
        webbrowser.open(f"http://localhost:{self.port}")
        
        # Wait for a client to connect
        while not self.ws_server.clients:
            print("Waiting for WebSocket client to connect...")
            await asyncio.sleep(0.1)
        
        print("WebSocket client connected, starting simulation...")
    
    def _start_server(self):
        """Start the web server."""
        os.chdir(self.web_dir)  # Change to the web visualization directory
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", self.port), handler) as httpd:
            print(f"Serving at port {self.port}")
            httpd.serve_forever()
    
    async def _start_ws_server(self):
        """Start the WebSocket server."""
        await self.ws_server.start()
        print(f"WebSocket server started at ws://localhost:{self.ws_port}")
    
    async def _process_messages(self):
        """Process messages from the queue and send them to WebSocket clients."""
        while True:
            message = await self.message_queue.get()
            try:
                if self.ws_server.clients:
                    print(f"Sending WebSocket message: {message}")
                    await self.ws_server.broadcast(message)
                else:
                    print("No WebSocket clients connected, skipping message")
            except Exception as e:
                print(f"Warning: Failed to send message: {e}")
            finally:
                self.message_queue.task_done()
    
    def add_object(self, obj: Any) -> None:
        """Create a visual entity for the object in the WebGL scene."""
        try:
            pos = vec3_to_list(obj.position)
            col = vec3_to_list(obj.color)
        except AttributeError as e:
            raise AttributeError(f"Object must have position and color attributes: {e}")

        try:
            model_type = getattr(obj, 'model_type', 'cube')
            scale = getattr(obj, 'scale', (1, 1, 1))

            self.entities[obj] = {
                'id': id(obj),
                'position': pos,
                'color': col,
                'model_type': model_type,
                'scale': scale
            }

            # Queue add message
            message = {
                'type': 'add',
                'id': id(obj),
                'position': pos,
                'color': col,
                'model_type': model_type,
                'scale': scale
            }
            print(f"Adding object: {message}")
            self.loop.call_soon_threadsafe(
                self.message_queue.put_nowait,
                message
            )

        except Exception as e:
            raise RuntimeError(f"Failed to create entity for object: {e}")

    def remove_object(self, obj: Any) -> None:
        """Destroy the object's entity in the WebGL scene."""
        if obj in self.entities:
            # Queue remove message
            message = {
                'type': 'remove',
                'id': id(obj)
            }
            print(f"Removing object: {message}")
            self.loop.call_soon_threadsafe(
                self.message_queue.put_nowait,
                message
            )
            del self.entities[obj]

    def update_object(self, obj: Any) -> None:
        """Update the WebGL entity to match the object's state."""
        if obj not in self.entities:
            return

        try:
            entity_data = self.entities[obj]
            entity_data['position'] = vec3_to_list(obj.position)
            entity_data['color'] = vec3_to_list(obj.color)

            if hasattr(obj, 'rotation'):
                entity_data['rotation'] = vec3_to_list(obj.rotation)

            if hasattr(obj, 'scale'):
                entity_data['scale'] = obj.scale

            # Queue update message
            message = {
                'type': 'update',
                'id': id(obj),
                'position': entity_data['position'],
                'color': entity_data['color'],
                'rotation': entity_data.get('rotation'),
                'scale': entity_data.get('scale')
            }
            print(f"Updating object: {message}")
            self.loop.call_soon_threadsafe(
                self.message_queue.put_nowait,
                message
            )

        except Exception as e:
            print(f"Warning: Failed to update object visualization: {e}")

    def run(self, world: Any) -> None:
        """Start the visualization loop."""
        self.world_updater = world
        # The web server and WebSocket server are already running

    async def cleanup(self) -> None:
        """Clean up WebGL resources."""
        if self.ws_server:
            await self.ws_server.stop()
        # The web server thread will terminate when the program exits 