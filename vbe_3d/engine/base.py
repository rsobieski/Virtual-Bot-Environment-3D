from abc import ABC, abstractmethod
from typing import Any, Dict

# Engine interface abstraction
class Engine(ABC):
    """Abstract Engine for 3D visualization and simulation."""
    @abstractmethod
    def add_object(self, obj: Any) -> None:
        """Add a visual representation of the object to the scene."""
        pass

    @abstractmethod
    def remove_object(self, obj: Any) -> None:
        """Remove the object's visualization from the scene."""
        pass

    @abstractmethod
    def update_object(self, obj: Any) -> None:
        """Update the visual representation (position/color) of the object."""
        pass

    @abstractmethod
    def run(self, world: Any) -> None:
        """Start the real-time rendering loop (if applicable)."""
        pass