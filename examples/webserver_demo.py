"""WebGL visualization demo with robots and static elements."""

import asyncio
import time
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
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
    
    # Add some static elements
    world.add_static(StaticElement((0, 0, 0), (1, 0, 0), 10))  # Red resource at origin
    world.add_static(StaticElement((5, 0, 5), (0, 1, 0), 15))  # Green resource
    world.add_static(StaticElement((-5, 0, -5), (0, 0, 1), 20))  # Blue resource
    
    # Add some robots
    robot1 = Robot((1, 0, 1), (1, 0, 0))
    robot2 = Robot((-1, 0, -1), (0, 1, 0))
    robot3 = Robot((0, 0, 3), (0, 0, 1))
    
    world.add_robot(robot1)
    world.add_robot(robot2)
    world.add_robot(robot3)
    
    try:
        # Run simulation for a few steps
        for _ in range(100):
            world.step()
            await asyncio.sleep(0.1)  # Add small delay between steps
            
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    finally:
        # Clean up resources
        await engine.cleanup()

def run_ursina_demo():
    """Run the demo using Ursina visualization."""
    print("\nStarting Ursina demo...")
    
    # Create the Ursina engine
    engine = UrsinaEngine()
    
    # Create the world
    world = World(engine)
    
    # Add some static elements
    world.add_static(StaticElement(position=(5, 0, 0), color=(1, 0, 1), resource_value=40))
    world.add_static(StaticElement(position=(0, 0, 5), color=(1, 1, 0), resource_value=30))
    world.add_static(StaticElement(position=(-5, 0, 0), color=(0, 1, 1), resource_value=20))
    
    # Add robots with different behaviors
    robot1 = Robot(position=(0, 0, 0), color=(1, 0, 0))
    robot2 = Robot(position=(2, 0, 0), color=(0, 1, 0), brain=RLBrain())
    robot3 = Robot(position=(-2, 0, 0), color=(0, 0, 1))
    
    world.add_robot(robot1)
    world.add_robot(robot2)
    world.add_robot(robot3)
    
    # Start the visualization
    engine.run(world)
    
    try:
        while True:
            # Move robots in different patterns
            robot1.position = (robot1.position[0] + 0.1, 0, robot1.position[2] + 0.1)
            robot2.position = (robot2.position[0] - 0.1, 0, robot2.position[2] - 0.1)
            robot3.position = (robot3.position[0], 0, robot3.position[2] + 0.2)
            
            # Update the world
            world.step()
            
            # Wait a bit
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nUrsina demo stopped by user")
    finally:
        engine.cleanup()

def main():
    """Main entry point."""
    print("Choose visualization engine:")
    print("1. WebGL (Browser-based)")
    print("2. Ursina (Native window)")
    
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == "1":
        asyncio.run(run_webgl_demo())
    elif choice == "2":
        run_ursina_demo()
    else:
        print("Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main()
