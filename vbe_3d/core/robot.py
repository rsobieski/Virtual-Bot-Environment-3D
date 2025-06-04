from __future__ import annotations

import math
from typing import Dict, List, Tuple, Optional, Set, TYPE_CHECKING
import itertools
from enum import Enum, auto
from dataclasses import dataclass
from ursina import Vec3

from vbe_3d.utils.id_manager import next_id
from vbe_3d.core.base_element import BaseElement
from vbe_3d.brain.base_brain import RobotBrain
from vbe_3d.brain.rl_brain import RLBrain
from vbe_3d.brain.rule_based import RuleBasedBrain
from vbe_3d.utils.geometry import add_vec

if TYPE_CHECKING:
    from vbe_3d.core.world import World

class RobotState(Enum):
    """Possible states a robot can be in."""
    IDLE = auto()
    MOVING = auto()
    COLLECTING = auto()
    REPRODUCING = auto()
    DEAD = auto()

class ConnectionLevel(Enum):
    """Connection strength levels between robots."""
    NONE = 0
    WEAK = 1    
    MEDIUM = 2
    STRONG = 3
    PERMANENT = 4

@dataclass
class RobotStats:
    """Statistics tracking for a robot."""
    distance_traveled: float = 0.0
    resources_collected: int = 0
    connections_made: int = 0
    offspring_produced: int = 0
    energy_consumed: float = 0.0
    lifetime: int = 0

# global counter for robot IDs
_robot_id_counter = itertools.count()

class Robot(BaseElement):
    """A robot (active agent) in the world.
    
    Attributes:
        id: Unique identifier for the robot
        energy: Current energy level
        connections: Dictionary mapping connected robots to connection strength
        brain: The robot's decision-making system
        state: Current state of the robot
        stats: Statistics tracking for the robot
        max_energy: Maximum energy capacity
        movement_cost: Energy cost per movement
        reproduction_threshold: Minimum energy required for reproduction
    """
    
    def __init__(
        self,
        position: Tuple[float, float, float] = (0, 0, 0),
        color: Tuple[float, float, float] = (0.2, 0.8, 0.2),
        brain: Optional[RobotBrain] = None,
        max_energy: float = 100.0,
        movement_cost: float = 1.0,
        reproduction_threshold: float = 20.0
    ):
        super().__init__(position, color)
        self.id = next(_robot_id_counter)
        self.energy = max_energy
        self.max_energy = max_energy
        self.movement_cost = movement_cost
        self.reproduction_threshold = reproduction_threshold
        self.connections: Dict[Robot, int] = {}
        self.state = RobotState.IDLE
        self.stats = RobotStats()
        
        # Initialize brain
        if brain is None:
            self.brain = RuleBasedBrain()
        else:
            self.brain = brain
        self.brain.robot = self

    def perceive(self, world: 'World') -> List[float]:
        """Gather observations about the world to feed into the brain.
        
        Args:
            world: The world to perceive.
            
        Returns:
            List of observations including:
            - Relative position to nearest resource
            - Relative position to nearest robot
            - Current energy level (normalized)
            - Number of connections
            - Current state
        """
        obs = []
        
        # Find nearest resource using spatial indexing if available
        nearest_res = None
        min_dist = float('inf')
        
        if hasattr(world, '_get_nearby_objects'):
            nearby = world._get_nearby_objects(self.position, 10.0)  # Look within 10 units
            for e in nearby:
                if hasattr(e, 'resource_value'):
                    dist = math.dist(self.position, e.position)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_res = e
        else:
            for e in world.static_elements:
                if hasattr(e, 'resource_value'):
                    dist = math.dist(self.position, e.position)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_res = e
                        
        if nearest_res:
            obs.extend([
                nearest_res.position[0] - self.position[0],
                nearest_res.position[1] - self.position[1],
                nearest_res.position[2] - self.position[2]
            ])
        else:
            obs.extend([0.0, 0.0, 0.0])
            
        # Find nearest robot
        nearest_bot = None
        min_dist = float('inf')
        
        if hasattr(world, '_get_nearby_objects'):
            nearby = world._get_nearby_objects(self.position, 10.0)
            for r in nearby:
                if isinstance(r, Robot) and r is not self:
                    dist = math.dist(self.position, r.position)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_bot = r
        else:
            for r in world.robots:
                if r is not self:
                    dist = math.dist(self.position, r.position)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_bot = r
                        
        if nearest_bot:
            obs.extend([
                nearest_bot.position[0] - self.position[0],
                nearest_bot.position[1] - self.position[1],
                nearest_bot.position[2] - self.position[2]
            ])
        else:
            obs.extend([0.0, 0.0, 0.0])
            
        # Add additional observations
        obs.extend([
            self.energy / self.max_energy,  # Normalized energy
            len(self.connections) / 10.0,   # Normalized connection count
            self.state.value / len(RobotState)  # Normalized state
        ])
        
        return obs

    def act(self, action: int) -> None:
        """Execute an action based on the brain's decision.
        
        Args:
            action: Integer representing the action to take.
                  0: no-op
                  1-6: movement in ±x, ±y, ±z directions
        """
        if action == 0:
            self.state = RobotState.IDLE
            return
            
        self.state = RobotState.MOVING
        step = 1.0
        
        # Store old position as tuple instead of Vec3
        old_pos = (self.position[0], self.position[1], self.position[2])
        
        # Movement actions
        if action == 1:
            self.position.x += step
        elif action == 2:
            self.position.x -= step
        elif action == 3:
            self.position.z += step
        elif action == 4:
            self.position.z -= step
        elif action == 5:
            self.position.y += step
        elif action == 6:
            self.position.y -= step
            
        # Update statistics
        self.stats.distance_traveled += math.dist(old_pos, (self.position[0], self.position[1], self.position[2]))
        self.stats.energy_consumed += self.movement_cost
        self.stats.lifetime += 1
        
        # Consume energy
        self.energy = max(0.0, self.energy - self.movement_cost)
        
        # Check for death
        if self.energy <= 0:
            self.state = RobotState.DEAD

    def connect(self, other: 'Robot') -> None:
        """Form or strengthen connection with another robot.
        
        Args:
            other: The robot to connect with.
        """
        if other not in self.connections:
            self.connections[other] = ConnectionLevel.WEAK.value
            other.connections[self] = ConnectionLevel.WEAK.value
            self.stats.connections_made += 1
        else:
            level = self.connections[other]
            if level < ConnectionLevel.PERMANENT.value:
                new_level = level + 1
                self.connections[other] = new_level
                other.connections[self] = new_level

    def disconnect(self, other: 'Robot') -> None:
        """Weaken or break connection with another robot.
        
        Args:
            other: The robot to disconnect from.
        """
        if other in self.connections:
            level = self.connections[other]
            if level == ConnectionLevel.PERMANENT.value:
                return
            if level > ConnectionLevel.WEAK.value:
                new_level = level - 1
                self.connections[other] = new_level
                other.connections[self] = new_level
            else:
                del self.connections[other]
                if self in other.connections:
                    del other.connections[self]

    def reproduce(self, partner: 'Robot') -> Optional['Robot']:
        """Attempt to create a new robot by combining traits with a partner.
        
        Args:
            partner: The robot to reproduce with.
            
        Returns:
            A new Robot instance or None if reproduction doesn't occur.
        """
        if self.energy < self.reproduction_threshold or partner.energy < self.reproduction_threshold:
            return None
            
        self.state = RobotState.REPRODUCING
        self.stats.offspring_produced += 1
        
        # Create child with mixed properties
        child_color = tuple((a+b)/2.0 for a, b in zip(self.color, partner.color))
        
        # Handle brain inheritance
        if isinstance(self.brain, RLBrain) and isinstance(partner.brain, RLBrain):
            child_brain = RLBrain()
            # Average the neural network parameters
            self_params = self.brain.model.state_dict()
            partner_params = partner.brain.model.state_dict()
            child_params = {
                k: (self_params[k] + partner_params[k]) / 2.0
                for k in self_params.keys()
            }
            child_brain.model.load_state_dict(child_params)
        else:
            child_brain = RuleBasedBrain()
            
        child = Robot(
            position=self.position,
            color=child_color,
            brain=child_brain,
            max_energy=self.max_energy,
            movement_cost=self.movement_cost,
            reproduction_threshold=self.reproduction_threshold
        )
        
        return child

    def collect_resource(self, value: float) -> None:
        """Collect a resource and update energy.
        
        Args:
            value: The energy value of the collected resource.
        """
        self.state = RobotState.COLLECTING
        self.energy = min(self.max_energy, self.energy + value)
        self.stats.resources_collected += 1

    def to_dict(self) -> dict:
        """Convert robot state to dictionary for serialization."""
        return {
            "id": self.id,
            "pos": self.position,
            "col": self.color,
            "energy": self.energy,
            "max_energy": self.max_energy,
            "movement_cost": self.movement_cost,
            "reproduction_threshold": self.reproduction_threshold,
            "connections": [p.id for p in self.connections],
            "state": self.state.name,
            "stats": {
                "distance_traveled": self.stats.distance_traveled,
                "resources_collected": self.stats.resources_collected,
                "connections_made": self.stats.connections_made,
                "offspring_produced": self.stats.offspring_produced,
                "energy_consumed": self.stats.energy_consumed,
                "lifetime": self.stats.lifetime
            },
            "brain": self.brain.export()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Robot":
        """Create a robot from serialized data."""
        from vbe_3d.brain.factory import brain_from_export

        brain = brain_from_export(data["brain"])
        robot = cls(
            position=tuple(data["pos"]),
            color=tuple(data["col"]),
            brain=brain,
            max_energy=data.get("max_energy", 100.0),
            movement_cost=data.get("movement_cost", 1.0),
            reproduction_threshold=data.get("reproduction_threshold", 20.0)
        )
        
        robot.id = data["id"]
        robot.energy = data["energy"]
        robot.state = RobotState[data["state"]]
        
        # Restore statistics
        stats = data.get("stats", {})
        robot.stats = RobotStats(
            distance_traveled=stats.get("distance_traveled", 0.0),
            resources_collected=stats.get("resources_collected", 0),
            connections_made=stats.get("connections_made", 0),
            offspring_produced=stats.get("offspring_produced", 0),
            energy_consumed=stats.get("energy_consumed", 0.0),
            lifetime=stats.get("lifetime", 0)
        )
        
        return robot
