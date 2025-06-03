"""Minimal live demo – run and move two robots."""

from vbe_3d.engine.ursina_engine import UrsinaEngine
from vbe_3d.core.world import World
from vbe_3d.core.robot import Robot
from vbe_3d.core.static_element import StaticElement
from vbe_3d.brain.rl_brain import RLBrain

if __name__ == "__main__":
    engine = UrsinaEngine()
    world = World(engine)

    world.add_static(StaticElement(position=(5, 0, 0), resource_value=40))
    world.add_static(StaticElement(position=(0, 0, 5), resource_value=30))

    world.add_robot(Robot(position=(0, 0, 0)))
    world.add_robot(Robot(position=(2, 0, 0), brain=RLBrain()))

    engine.run(world)
