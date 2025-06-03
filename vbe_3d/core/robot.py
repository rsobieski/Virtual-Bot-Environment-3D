from __future__ import annotations

import math
from typing import Dict, List, Tuple, TYPE_CHECKING
import itertools
from enum import Enum

from vbe_3d.utils.id_manager import next_id
from vbe_3d.core.base_element import BaseElement
from vbe_3d.brain.base_brain import RobotBrain
from vbe_3d.brain.rl_brain import RLBrain
from vbe_3d.brain.rule_based import RuleBasedBrain
from vbe_3d.utils.geometry import add_vec

if TYPE_CHECKING:
    from vbe_3d.core.world import World

# simple enum for connection strength levels
class ConnectionLevel(Enum):
    NONE = 0
    WEAK = 1    
    MEDIUM = 2
    STRONG = 3
    PERMANENT = 4

# global counter for robot IDs
_robot_id_counter = itertools.count()

class Robot(BaseElement):
    """A robot (active agent) in the world."""
    def __init__(self, position=(0,0,0), color=(0.2, 0.8, 0.2), brain=None):
        super().__init__(position, color)
        self.id = next(_robot_id_counter)     # unique ID
        # Robot properties
        self.energy = 100.0   # example property: energy level
        self.connections: Dict[Robot, int] = {}  # connections to other robots and their strength level (int 0-4)
        # Initialize brain
        if brain is None:
            # Default to a simple rule-based brain if none provided
            self.brain = RuleBasedBrain()
        else:
            self.brain = brain
        self.brain.robot = self  # link brain to this robot

    def perceive(self, world: 'World'):
        """Gather observations about the world to feed into the brain. 
        For simplicity, returns a vector of important relative positions and states."""
        # example observation: vector to nearest resource and nearest robot, plus current energy.
        obs = []
        # find nearest static element (resource)
        nearest_res = None
        min_dist = float('inf')
        for e in world.static_elements:
            dx = e.position[0] - self.position[0]
            dy = e.position[1] - self.position[1]
            dz = e.position[2] - self.position[2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist < min_dist:
                min_dist = dist
                nearest_res = e
        if nearest_res:
            # relative position of nearest resource
            obs += [nearest_res.position[0] - self.position[0],
                    nearest_res.position[1] - self.position[1],
                    nearest_res.position[2] - self.position[2]]
        else:
            # no resource found, use zeros
            obs += [0.0, 0.0, 0.0]
        # nearest other robot
        nearest_bot = None
        min_dist = float('inf')
        for r in world.robots:
            if r is self: 
                continue
            dx = r.position[0] - self.position[0]
            dy = r.position[1] - self.position[1]
            dz = r.position[2] - self.position[2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist < min_dist:
                min_dist = dist
                nearest_bot = r
        if nearest_bot:
            obs += [nearest_bot.position[0] - self.position[0],
                    nearest_bot.position[1] - self.position[1],
                    nearest_bot.position[2] - self.position[2]]
        else:
            obs += [0.0, 0.0, 0.0]
        # add its own energy level (normalized perhaps)
        obs.append(self.energy / 100.0)  # energy scaled
        return obs

    def act(self, action):
        """Execute an action (e.g., move or other operation). 
        for simplicity, actions might be movement in one of six directions or no-op."""
        # define an action space, for example:
        # 0: no action, 1: move +x, 2: move -x, 3: move +z, 4: move -z, 5: move +y, 6: move -y
        if action == 0:
            return  # no-op
        step = 1.0  # movement step size
        if action == 1:
            self.position[0] += step
        elif action == 2:
            self.position[0] -= step
        elif action == 3:
            self.position[2] += step
        elif action == 4:
            self.position[2] -= step
        elif action == 5:
            self.position[1] += step
        elif action == 6:
            self.position[1] -= step
        # could add actions like connecting or disconnecting explicitly, but here movement + proximity triggers connection.

        # decrease energy for moving, to simulate consumption
        if action != 0:
            self.energy -= 1.0
        # ensure energy doesn't drop below 0
        if self.energy < 0:
            self.energy = 0
        # if energy hits 0, we might consider the robot "dead" and remove it (not implemented here, but could be)

    def connect(self, other: 'Robot'):
        """Form or strengthen connection with another robot."""
        if other not in self.connections:
            # Initialize a connection at weak level
            self.connections[other] = ConnectionLevel.WEAK.value
            other.connections[self] = ConnectionLevel.WEAK.value
        else:
            # Increase connection strength if not permanent
            level = self.connections[other]
            if level < ConnectionLevel.PERMANENT.value:
                new_level = level + 1
                self.connections[other] = new_level
                other.connections[self] = new_level

    def disconnect(self, other: 'Robot'):
        """Weaken or break connection with another robot if not permanent."""
        if other in self.connections:
            level = self.connections[other]
            if level == ConnectionLevel.PERMANENT.value:
                # permanent connection: do not break (could have special logic to break if certain conditions)
                return
            if level > ConnectionLevel.WEAK.value:
                # just reduce connection one level if above weak
                new_level = level - 1
                self.connections[other] = new_level
                other.connections[self] = new_level
            else:
                # if at weakest level, remove the connection entirely
                del self.connections[other]
                if self in other.connections:
                    del other.connections[self]

    def reproduce(self, partner: 'Robot'):
        """Attempt to create a new robot by combining traits with a partner.
        returns a new Robot instance or None if reproduction doesn't occur."""
        # check basic conditions: both have enough energy perhaps
        if self.energy < 20 or partner.energy < 20:
            return None  # not enough energy to reproduce
        # create child with mixed properties
        child_color = tuple((a+b)/2.0 for a, b in zip(self.color, partner.color))
        # for brain: combine or choose one parent's brain type
        if isinstance(self.brain, RLBrain) and isinstance(partner.brain, RLBrain):
            # if both have RLBrain, we could mix weights (not implemented fully here)
            child_brain = RLBrain()
            # optionally, average the neural network parameters:
            child_brain.model.load_state_dict(self.brain.model.state_dict())  # start with one parent's weights
            # (in practice, one might average the weights or randomly mix layers)
        else:
            # default to a simple brain for the child
            child_brain = RuleBasedBrain()
        child = Robot(position=(0,0,0), color=child_color, brain=child_brain)
        return child
    
    # ––– helpers –––
    def _nearest_vector(self, elems: List[BaseElement]):
        min_dist, vec = math.inf, None
        for e in elems:
            dvec = (e.position[0] - self.position[0], e.position[1] - self.position[1], e.position[2] - self.position[2])
            dist = math.dist(self.position, e.position)
            if dist < min_dist:
                min_dist, vec = dist, dvec
        return vec

    # ––– (de)serialization –––
    def to_dict(self):
        return {
            "id": self.id,
            "pos": self.position,
            "col": self.color,
            "energy": self.energy,
            "connections": [p.id for p in self.connections],
            "brain": self.brain.export(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Robot":
        from vbe_3d.brain.factory import brain_from_export  # lazy import

        brain = brain_from_export(data["brain"])
        robot = cls(position=tuple(data["pos"]), color=tuple(data["col"]), brain=brain)
        robot.id = data["id"]  # restore exact id
        robot.energy = data["energy"]
        return robot
