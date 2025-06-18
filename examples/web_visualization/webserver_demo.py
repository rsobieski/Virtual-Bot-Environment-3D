"""WebGL visualization demo with robots and static elements."""

import asyncio
import time
import sys
import json
import os
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Add the examples directory to Python path for config_loader
examples_dir = str(Path(__file__).parent.parent)
if examples_dir not in sys.path:
    sys.path.append(examples_dir)

from vbe_3d.engine.webgl_engine import WebGLEngine
from config_loader import ConfigLoader

async def run_webgl_demo():
    """Run the WebGL visualization demo."""
    print("Starting WebGL demo...")
    
    # Get the path to the configuration file
    config_path = os.path.join(os.path.dirname(__file__), "..", "world_config.json")
    
    # Initialize WebGL engine
    engine = WebGLEngine()
    
    # Start the engine and wait for WebSocket server
    await engine.start()
    
    # Create world from configuration
    world = ConfigLoader.create_world_from_config(engine, config_path)
    
    try:
        # Run simulation continuously
        while True:
            # Step the world simulation
            world.step()
            
            # Update all objects in the visualization
            for obj in list(engine.entities.keys()):
                engine.update_object(obj)
            
            # Wait for messages to be processed
            await engine.message_queue.join()
            
            # Add small delay between steps
            await asyncio.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    finally:
        # Clean up resources
        await engine.cleanup()

def main():
    """Main entry point."""
    print("Starting WebGL demo...")
    asyncio.run(run_webgl_demo())

if __name__ == "__main__":
    main() 