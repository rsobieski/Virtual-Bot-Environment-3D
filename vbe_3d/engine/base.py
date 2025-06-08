from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

# Engine interface abstraction
class BaseEngine(ABC):
    """Base class for all visualization engines."""
    
    @abstractmethod
    def add_object(self, obj: Any) -> None:
        """Create a visual entity for the object in the scene.
        
        Args:
            obj: The object to visualize. Must have position and color attributes.
        """
        pass
    
    @abstractmethod
    def remove_object(self, obj: Any) -> None:
        """Destroy the object's entity in the scene.
        
        Args:
            obj: The object to remove.
        """
        pass
    
    @abstractmethod
    def update_object(self, obj: Any) -> None:
        """Update the visual entity to match the object's state.
        
        Args:
            obj: The object to update.
        """
        pass
    
    @abstractmethod
    def run(self, world: Any) -> None:
        """Start the visualization loop.
        
        Args:
            world: The world to visualize.
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources when the engine is no longer needed."""
        pass