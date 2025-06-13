"""Virtual Bot Environment 3D - A 3D visualization environment for robot simulation."""

from .engine import BaseEngine, UrsinaEngine, WebGLEngine
from .core.robot import Robot, RobotState
from .core.static_element import StaticElement
from .core.world import World, WorldStats
from .brain.rl_brain import RLBrain

__version__ = '0.1.0'

__all__ = [
    'BaseEngine',
    'UrsinaEngine',
    'WebGLEngine',
    'Robot',
    'RobotState',
    'StaticElement',
    'World',
    'WorldStats',
    'RLBrain',
]