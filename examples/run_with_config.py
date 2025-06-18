"""Flexible demo script that can run with different configuration files."""

import os
import sys
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vbe_3d.engine.ursina_engine import UrsinaEngine
from config_loader import ConfigLoader

def main():
    """Main entry point with command line argument support."""
    parser = argparse.ArgumentParser(description='Run 3D Virtual Bot Environment demo')
    parser.add_argument(
        '--config', 
        type=str, 
        default='world_config.json',
        help='Path to configuration file (default: world_config.json)'
    )
    parser.add_argument(
        '--list-configs',
        action='store_true',
        help='List available configuration files'
    )
    
    args = parser.parse_args()
    
    # List available configs if requested
    if args.list_configs:
        config_dir = os.path.dirname(__file__)
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
    
    # Initialize engine
    engine = UrsinaEngine()
    
    # Create world from configuration
    world = ConfigLoader.create_world_from_config(engine, config_path)
    
    # Run the simulation
    engine.run(world)

if __name__ == "__main__":
    main() 