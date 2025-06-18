"""Minimal live demo – run and move two robots."""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vbe_3d.engine.ursina_engine import UrsinaEngine
from config_loader import ConfigLoader

if __name__ == "__main__":
    # Get the path to the configuration file
    config_path = os.path.join(os.path.dirname(__file__), "world_config.json")
    
    # Initialize engine
    engine = UrsinaEngine()
    
    # Create world from configuration
    world = ConfigLoader.create_world_from_config(engine, config_path)
    
    # Run the simulation
    engine.run(world)
