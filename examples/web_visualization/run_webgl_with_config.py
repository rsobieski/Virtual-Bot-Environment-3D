"""Flexible WebGL demo script that can run with different configuration files."""

import asyncio
import os
import sys
import argparse
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

async def run_webgl_demo(config_path: str):
    """Run the WebGL visualization demo with specified configuration."""
    print(f"Starting WebGL demo with config: {config_path}")
    
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
    """Main entry point with command line argument support."""
    parser = argparse.ArgumentParser(description='Run WebGL 3D Virtual Bot Environment demo')
    parser.add_argument(
        '--config', 
        type=str, 
        default='../world_config.json',
        help='Path to configuration file (default: ../world_config.json)'
    )
    parser.add_argument(
        '--list-configs',
        action='store_true',
        help='List available configuration files'
    )
    
    args = parser.parse_args()
    
    # List available configs if requested
    if args.list_configs:
        config_dir = os.path.join(os.path.dirname(__file__), '..')
        config_files = [f for f in os.listdir(config_dir) if f.endswith('_config.json')]
        print("Available configuration files:")
        for config_file in config_files:
            print(f"  - {config_file}")
        return
    
    # Get the path to the configuration file
    if os.path.isabs(args.config):
        config_path = args.config
    else:
        config_path = os.path.join(os.path.dirname(__file__), args.config)
    
    # Check if config file exists
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.")
        print("Use --list-configs to see available configuration files.")
        return
    
    print(f"Loading configuration from: {config_path}")
    
    # Run the async demo
    asyncio.run(run_webgl_demo(config_path))

if __name__ == "__main__":
    main() 