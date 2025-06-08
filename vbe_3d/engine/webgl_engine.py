from typing import Any, Dict, Optional
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
        
        # Create web server directory
        self.web_dir = Path("web_visualization")
        self.web_dir.mkdir(exist_ok=True)
        
        # Create necessary web files
        self._create_web_files()
        
        # Initialize WebSocket server
        self.ws_server = WebSocketServer(port=ws_port)
        
        # Start web server
        self.server_thread = threading.Thread(target=self._start_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Start WebSocket server
        self.ws_thread = threading.Thread(target=self._start_ws_server)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        # Open browser
        webbrowser.open(f"http://localhost:{port}")
    
    def _create_web_files(self):
        """Create the necessary HTML, CSS, and JavaScript files for the web visualization."""
        # Create index.html
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>VBE 3D Visualization</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            <style>
                body { margin: 0; }
                canvas { display: block; }
            </style>
        </head>
        <body>
            <script src="visualization.js"></script>
        </body>
        </html>
        """
        
        # Create visualization.js
        js_content = f"""
        let scene, camera, renderer, controls;
        let objects = new Map();

        function init() {{
            // Create scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x000000);

            // Create camera
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.z = 5;

            // Create renderer
            renderer = new THREE.WebGLRenderer();
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);

            // Add orbit controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;

            // Add ambient light
            const ambientLight = new THREE.AmbientLight(0x404040);
            scene.add(ambientLight);

            // Add directional light
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
            directionalLight.position.set(1, 1, 1);
            scene.add(directionalLight);

            // Handle window resize
            window.addEventListener('resize', onWindowResize, false);

            // Start animation loop
            animate();
        }}

        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }}

        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}

        // WebSocket connection
        const ws = new WebSocket('ws://' + window.location.hostname + ':{self.ws_port}');
        
        ws.onmessage = function(event) {{
            const data = JSON.parse(event.data);
            
            switch(data.type) {{
                case 'add':
                    addObject(data.id, data.position, data.color, data.model_type, data.scale);
                    break;
                case 'update':
                    updateObject(data.id, data.position, data.color, data.rotation, data.scale);
                    break;
                case 'remove':
                    removeObject(data.id);
                    break;
            }}
        }};

        function addObject(id, position, color, modelType, scale) {{
            let geometry;
            switch(modelType) {{
                case 'cube':
                    geometry = new THREE.BoxGeometry(scale[0], scale[1], scale[2]);
                    break;
                case 'sphere':
                    geometry = new THREE.SphereGeometry(scale[0], 32, 32);
                    break;
                default:
                    geometry = new THREE.BoxGeometry(1, 1, 1);
            }}

            const material = new THREE.MeshPhongMaterial({{ color: new THREE.Color(color[0], color[1], color[2]) }});
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.set(position[0], position[1], position[2]);
            
            scene.add(mesh);
            objects.set(id, mesh);
        }}

        function updateObject(id, position, color, rotation, scale) {{
            const mesh = objects.get(id);
            if (mesh) {{
                mesh.position.set(position[0], position[1], position[2]);
                mesh.material.color.setRGB(color[0], color[1], color[2]);
                if (rotation) {{
                    mesh.rotation.set(rotation[0], rotation[1], rotation[2]);
                }}
                if (scale) {{
                    mesh.scale.set(scale[0], scale[1], scale[2]);
                }}
            }}
        }}

        function removeObject(id) {{
            const mesh = objects.get(id);
            if (mesh) {{
                scene.remove(mesh);
                mesh.geometry.dispose();
                mesh.material.dispose();
                objects.delete(id);
            }}
        }}

        init();
        """
        
        # Write files
        with open(self.web_dir / "index.html", "w") as f:
            f.write(html_content)
        with open(self.web_dir / "visualization.js", "w") as f:
            f.write(js_content)
    
    def _start_server(self):
        """Start the web server."""
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", self.port), handler) as httpd:
            print(f"Serving at port {self.port}")
            httpd.serve_forever()
            
    def _start_ws_server(self):
        """Start the WebSocket server."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.ws_server.start())
        loop.run_forever()
    
    def add_object(self, obj: Any) -> None:
        """Create a visual entity for the object in the WebGL scene."""
        try:
            pos = obj.position
            col = obj.color
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

            # Send add message to client
            asyncio.create_task(self.ws_server.broadcast({
                'type': 'add',
                'id': id(obj),
                'position': pos,
                'color': col,
                'model_type': model_type,
                'scale': scale
            }))

        except Exception as e:
            raise RuntimeError(f"Failed to create entity for object: {e}")

    def remove_object(self, obj: Any) -> None:
        """Destroy the object's entity in the WebGL scene."""
        if obj in self.entities:
            # Send remove message to client
            asyncio.create_task(self.ws_server.broadcast({
                'type': 'remove',
                'id': id(obj)
            }))
            del self.entities[obj]

    def update_object(self, obj: Any) -> None:
        """Update the WebGL entity to match the object's state."""
        if obj not in self.entities:
            return

        try:
            entity_data = self.entities[obj]
            entity_data['position'] = obj.position
            entity_data['color'] = obj.color

            if hasattr(obj, 'rotation'):
                entity_data['rotation'] = obj.rotation

            if hasattr(obj, 'scale'):
                entity_data['scale'] = obj.scale

            # Send update message to client
            asyncio.create_task(self.ws_server.broadcast({
                'type': 'update',
                'id': id(obj),
                'position': obj.position,
                'color': obj.color,
                'rotation': getattr(obj, 'rotation', None),
                'scale': getattr(obj, 'scale', None)
            }))

        except Exception as e:
            print(f"Warning: Failed to update object visualization: {e}")

    def run(self, world: Any) -> None:
        """Start the visualization loop."""
        self.world_updater = world
        # The web server and WebSocket server are already running in separate threads 

    async def cleanup(self) -> None:
        """Clean up WebGL resources."""
        if self.ws_server:
            await self.ws_server.stop()
        # The web server thread will terminate when the program exits 