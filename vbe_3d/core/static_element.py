from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum, auto

from vbe_3d.core.base_element import BaseElement


class ResourceType(Enum):
    """Types of resources that can exist in the world."""
    ENERGY = auto()
    MATERIAL = auto()
    SPECIAL = auto()


@dataclass
class ResourceProperties:
    """Properties of a resource element."""
    type: ResourceType
    value: float
    decay_rate: float = 0.0
    respawn_time: Optional[int] = None
    max_uses: Optional[int] = None
    current_uses: int = 0


class StaticElement(BaseElement):
    """A static world element, like a resource block or obstacle.
    
    Attributes:
        resource_value: The energy value this resource provides when collected
        resource_type: The type of resource this element represents
        properties: Additional properties of the resource
        is_obstacle: Whether this element blocks movement
        is_collectible: Whether this element can be collected
        respawn_timer: Timer for respawning after collection
    """
    
    def __init__(
        self,
        position: Tuple[float, float, float],
        color: Tuple[float, float, float] = (0.9, 0.6, 0.1),
        resource_value: float = 20.0,
        resource_type: ResourceType = ResourceType.ENERGY,
        decay_rate: float = 0.0,
        respawn_time: Optional[int] = None,
        max_uses: Optional[int] = None,
        is_obstacle: bool = False,
        is_collectible: bool = True
    ) -> None:
        super().__init__(position, color)
        self.resource_value = resource_value
        self.resource_type = resource_type
        self.properties = ResourceProperties(
            type=resource_type,
            value=resource_value,
            decay_rate=decay_rate,
            respawn_time=respawn_time,
            max_uses=max_uses
        )
        self.is_obstacle = is_obstacle
        self.is_collectible = is_collectible
        self.respawn_timer: Optional[int] = None

    def update(self) -> None:
        """Update the element's state (e.g., decay, respawn)."""
        if self.respawn_timer is not None:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.respawn()
                
        if self.properties.decay_rate > 0:
            self.resource_value = max(0.0, self.resource_value - self.properties.decay_rate)

    def collect(self) -> float:
        """Collect the resource and return its value.
        
        Returns:
            The resource value that was collected.
        """
        if not self.is_collectible:
            return 0.0
            
        value = self.resource_value
        
        if self.properties.max_uses is not None:
            self.properties.current_uses += 1
            if self.properties.current_uses >= self.properties.max_uses:
                self.is_collectible = False
                
        if self.properties.respawn_time is not None:
            self.respawn_timer = self.properties.respawn_time
            self.is_collectible = False
            
        return value

    def respawn(self) -> None:
        """Respawn the resource after being collected."""
        self.is_collectible = True
        self.respawn_timer = None
        self.resource_value = self.properties.value
        self.properties.current_uses = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert element state to dictionary for serialization."""
        return {
            "pos": self.position,
            "col": self.color,
            "val": self.resource_value,
            "type": self.resource_type.name,
            "properties": {
                "decay_rate": self.properties.decay_rate,
                "respawn_time": self.properties.respawn_time,
                "max_uses": self.properties.max_uses,
                "current_uses": self.properties.current_uses
            },
            "is_obstacle": self.is_obstacle,
            "is_collectible": self.is_collectible,
            "respawn_timer": self.respawn_timer
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StaticElement":
        """Create a static element from serialized data."""
        properties = data.get("properties", {})
        element = cls(
            position=tuple(data["pos"]),
            color=tuple(data["col"]),
            resource_value=data["val"],
            resource_type=ResourceType[data["type"]],
            decay_rate=properties.get("decay_rate", 0.0),
            respawn_time=properties.get("respawn_time"),
            max_uses=properties.get("max_uses"),
            is_obstacle=data.get("is_obstacle", False),
            is_collectible=data.get("is_collectible", True)
        )
        element.properties.current_uses = properties.get("current_uses", 0)
        element.respawn_timer = data.get("respawn_timer")
        return element
