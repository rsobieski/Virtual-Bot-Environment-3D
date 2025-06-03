from typing import Tuple

from vbe_3d.core.base_element import BaseElement


class StaticElement(BaseElement):
    """A static world element, like a resource block."""

    def __init__(
        self,
        position: Tuple[float, float, float],
        color: Tuple[float, float, float] = (0.9, 0.6, 0.1),
        resource_value: float = 20.0,
    ) -> None:
        super().__init__(position, color)
        self.resource_value = resource_value

    # serialization helpers
    def to_dict(self):
        return {"pos": self.position, "col": self.color, "val": self.resource_value}

    @classmethod
    def from_dict(cls, data: dict) -> "StaticElement":
        return cls(position=tuple(data["pos"]), color=tuple(data["col"]), resource_value=data["val"])
