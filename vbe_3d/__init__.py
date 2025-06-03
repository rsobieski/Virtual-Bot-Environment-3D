from importlib.metadata import version

__all__ = ["World", "Robot", "StaticElement", "UrsinaEngine"]
__version__ = version("vbe_3d")

from .core.world import World
from .core.robot import Robot
from .core.static_element import StaticElement
from .engine.ursina_engine import UrsinaEngine