from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from vbe_3d.core.robot import Robot


class RobotBrain(ABC):
    """Strategy interface – one per robot."""

    def __init__(self) -> None:
        self.robot: "Robot | None" = None

    @abstractmethod
    def decide_action(self, observation):
        """Choose an action for the robot based on observation."""
        pass

    def clone(self) -> "RobotBrain":
        """Return a deep copy of the brain (for reproduction)."""
        import copy

        cloned = copy.deepcopy(self)
        cloned.robot = None
        return cloned

    def export(self) -> dict:
        """Serialize parameters for save_state."""
        return {"type": self.__class__.__name__}
