from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from vbe_3d.core.world import World


class BaseElement:
    """Base class for any object in the world (robot or static element). """

    def __init__(self, position: Tuple[float, float, float], color: Tuple[float, float, float]) -> None:
        self.position = list(position)  # using list so it's mutable (x,y,z)
        self.color = color # color stored as (r,g,b) 0-1
        self.world: "World | None" = None # will be set when added to world

    