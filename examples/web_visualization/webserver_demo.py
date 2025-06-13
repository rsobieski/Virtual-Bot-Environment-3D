"""WebGL visualization demo with robots and static elements."""

import asyncio
import time
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from vbe_3d.engine.webgl_engine import WebGLEngine
from vbe_3d.engine.ursina_engine import UrsinaEngine
from vbe_3d.core.world import World
from vbe_3d.core.robot import Robot
from vbe_3d.core.static_element import StaticElement
from vbe_3d.brain.rl_brain import RLBrain

async def run_webgl_demo():
    """Run the WebGL visualization demo."""
    print("Starting WebGL demo...")
    
    # Initialize WebGL engine
    engine = WebGLEngine()
    world = World(engine)
    
    # Add static elements matching run_demo.py
    static1 = StaticElement(position=(5, 0, 0), color=(1, 0, 1), resource_value=40)
    static2 = StaticElement(position=(0, 0, 5), color=(1, 1, 0), resource_value=30)
    
    world.add_static(static1)
    world.add_static(static2)
    
    # Add robots matching run_demo.py
    robot1 = Robot(position=(0, 0, 0), color=(1, 0, 0))
    robot2 = Robot(position=(2, 0, 0), color=(0, 1, 0), brain=RLBrain())
    
    world.add_robot(robot1)
    world.add_robot(robot2)
    
    # Add objects to visualization
    engine.add_object(static1)
    engine.add_object(static2)
    engine.add_object(robot1)
    engine.add_object(robot2)
    
    try:
        # Run simulation continuously
        while True:
            world.step()
            
            # Update robot positions in visualization
            engine.update_object(robot1)
            engine.update_object(robot2)
            
            await asyncio.sleep(0.1)  # Add small delay between steps
            
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