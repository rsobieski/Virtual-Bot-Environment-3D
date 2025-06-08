from __future__ import annotations

import json
import math
from typing import List, Dict, Set, Optional, Tuple, TYPE_CHECKING, Any
from dataclasses import dataclass, field
from enum import Enum
from ursina import Vec3

from vbe_3d.engine.base import BaseEngine
from vbe_3d.core.robot import Robot, RobotState
from vbe_3d.core.static_element import StaticElement
from vbe_3d.brain.rl_brain import RLBrain
from vbe_3d.brain.rule_based import RuleBasedBrain

if TYPE_CHECKING:
    from vbe_3d.core.robot import Robot
    from vbe_3d.core.static_element import StaticElement
    from vbe_3d.brain.rl_brain import RLBrain
    from vbe_3d.brain.rule_based import RuleBasedBrain

class InteractionType(Enum):
    """Types of interactions that can occur between objects."""
    CONNECTION = "connection"
    RESOURCE_COLLECTION = "resource_collection"
    REPRODUCTION = "reproduction"

@dataclass
class Interaction:
    """Represents an interaction between objects in the world."""
    type: InteractionType
    source: Any
    target: Any
    strength: float = 1.0

@dataclass
class WorldStats:
    """Statistics tracking for the world."""
    steps: int = 0
    robots_created: int = 0
    robots_destroyed: int = 0
    resources_collected: int = 0
    connections_made: int = 0
    offspring_produced: int = 0

class World:
    """The main world container for robots and static elements."""
    
    def __init__(self, engine: BaseEngine):
        """Initialize the world.
        
        Args:
            engine: The visualization engine to use.
        """
        self.engine = engine
        self.robots: List[Robot] = []
        self.static_elements: List[StaticElement] = []
        self.stats = WorldStats()
        self.time_step = 0
        self._interaction_cache: Dict[Tuple[int, int], Interaction] = {}
        self._spatial_index: Dict[Tuple[int, int, int], Set[Any]] = {}
        
    def _update_spatial_index(self) -> None:
        """Update the spatial index for faster proximity queries."""
        self._spatial_index.clear()
        for obj in self.robots + self.static_elements:
            # Convert position to grid coordinates
            x, y, z = map(lambda p: int(p), obj.position)
            key = (x, y, z)
            if key not in self._spatial_index:
                self._spatial_index[key] = set()
            self._spatial_index[key].add(obj)
    
    def _get_nearby_objects(self, position: Tuple[float, float, float], radius: float) -> Set[Any]:
        """Get all objects within radius of the given position.
        
        Args:
            position: The center position to search around.
            radius: The search radius.
            
        Returns:
            Set of objects within the radius.
        """
        x, y, z = position
        nearby = set()
        # Check surrounding grid cells
        for dx in range(-int(radius), int(radius) + 1):
            for dy in range(-int(radius), int(radius) + 1):
                for dz in range(-int(radius), int(radius) + 1):
                    key = (int(x) + dx, int(y) + dy, int(z) + dz)
                    if key in self._spatial_index:
                        nearby.update(self._spatial_index[key])
        return nearby

    def add_robot(self, robot: Robot) -> None:
        """Add a robot to the world.
        
        Args:
            robot: The robot to add.
        """
        self.robots.append(robot)
        self.engine.add_object(robot)
        self.stats.robots_created += 1
        
    def remove_robot(self, robot: Robot) -> None:
        """Remove a robot from the world.
        
        Args:
            robot: The robot to remove.
        """
        if robot in self.robots:
            self.robots.remove(robot)
            self.engine.remove_object(robot)
            self.stats.robots_destroyed += 1
            
    def add_static(self, element: StaticElement) -> None:
        """Add a static element to the world.
        
        Args:
            element: The static element to add.
        """
        self.static_elements.append(element)
        self.engine.add_object(element)
        
    def remove_static(self, element: StaticElement) -> None:
        """Remove a static element from the world.
        
        Args:
            element: The static element to remove.
        """
        if element in self.static_elements:
            self.static_elements.remove(element)
            self.engine.remove_object(element)
            
    def step(self) -> None:
        """Advance the world simulation by one step."""
        self.stats.steps += 1
        
        # Update robots
        for robot in self.robots[:]:  # Copy list to allow removal during iteration
            if robot.state == RobotState.DEAD:
                self.remove_robot(robot)
                continue
                
            # Get robot's perception of the world
            obs = robot.perceive(self)
            
            # Get action from brain
            action = robot.brain.decide_action(obs)
            
            # Execute action
            robot.act(action)
            
            # Update visualization
            self.engine.update_object(robot)
            
            # Check for resource collection
            for element in self.static_elements:
                if math.dist(robot.position, element.position) < 1.0:
                    robot.collect_resource(element.resource_value)
                    self.stats.resources_collected += 1
                    self.engine.update_object(robot)
                    
            # Check for robot connections
            for other in self.robots:
                if other != robot and math.dist(robot.position, other.position) < 2.0:
                    robot.connect(other)
                    self.stats.connections_made += 1
                    
            # Check for reproduction
            for other in self.robots:
                if other != robot and math.dist(robot.position, other.position) < 1.0:
                    child = robot.reproduce(other)
                    if child:
                        self.add_robot(child)
                        self.stats.offspring_produced += 1
                        
    def to_dict(self) -> dict:
        """Convert world state to dictionary for serialization."""
        return {
            "robots": [robot.to_dict() for robot in self.robots],
            "static_elements": [
                {
                    "position": element.position,
                    "color": element.color,
                    "resource_value": element.resource_value
                }
                for element in self.static_elements
            ],
            "stats": {
                "steps": self.stats.steps,
                "robots_created": self.stats.robots_created,
                "robots_destroyed": self.stats.robots_destroyed,
                "resources_collected": self.stats.resources_collected,
                "connections_made": self.stats.connections_made,
                "offspring_produced": self.stats.offspring_produced
            }
        }
        
    @classmethod
    def from_dict(cls, data: dict, engine: BaseEngine) -> "World":
        """Create a world from serialized data."""
        from vbe_3d.core.robot import Robot
        
        world = cls(engine)
        
        # Restore robots
        for robot_data in data["robots"]:
            robot = Robot.from_dict(robot_data)
            world.add_robot(robot)
            
        # Restore static elements
        for element_data in data["static_elements"]:
            element = StaticElement(
                position=tuple(element_data["position"]),
                color=tuple(element_data["color"]),
                resource_value=element_data["resource_value"]
            )
            world.add_static(element)
            
        # Restore statistics
        stats = data.get("stats", {})
        world.stats = WorldStats(
            steps=stats.get("steps", 0),
            robots_created=stats.get("robots_created", 0),
            robots_destroyed=stats.get("robots_destroyed", 0),
            resources_collected=stats.get("resources_collected", 0),
            connections_made=stats.get("connections_made", 0),
            offspring_produced=stats.get("offspring_produced", 0)
        )
        
        return world

    def save_state(self, filepath: str) -> None:
        """Save the current world state to a JSON file.
        
        Args:
            filepath: Path to save the state file.
            
        Raises:
            IOError: If the file cannot be written.
        """
        try:
            data = {
                "time_step": self.time_step,
                "robots": [],
                "static": []
            }
            
            # Save robot data
            for r in self.robots:
                robot_data = {
                    "class": r.__class__.__name__,
                    "position": r.position,
                    "color": r.color,
                    "energy": getattr(r, "energy", None),
                    "connections": [r2.id for r2 in r.connections.keys()],
                    "brain_type": r.brain.__class__.__name__,
                    "brain_params": r.brain.export_params() if hasattr(r.brain, "export_params") else None
                }
                data["robots"].append(robot_data)
                
            # Save static element data
            for e in self.static_elements:
                elem_data = {
                    "class": e.__class__.__name__,
                    "position": e.position,
                    "color": e.color,
                    "resource_value": getattr(e, "resource_value", None)
                }
                data["static"].append(elem_data)
                
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            raise IOError(f"Failed to save world state: {e}")
    
    def load_state(self, filepath: str) -> None:
        """Load world state from a JSON file.
        
        Args:
            filepath: Path to the state file to load.
            
        Raises:
            IOError: If the file cannot be read.
            ValueError: If the file contains invalid data.
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            # Clear current world
            for r in list(self.robots):
                self.remove_robot(r)
            for e in list(self.static_elements):
                self.remove_static(e)
                
            self.robots = []
            self.static_elements = []
            self.time_step = data.get("time_step", 0)
            
            # Recreate static elements
            for elem_data in data.get("static", []):
                try:
                    cls_name = elem_data["class"]
                    if cls_name in ("StaticElement", "Resource"):
                        elem = StaticElement(
                            position=tuple(elem_data["position"]),
                            color=tuple(elem_data["color"]),
                            resource_value=elem_data.get("resource_value", 0)
                        )
                        self.add_static(elem)
                except Exception as e:
                    print(f"Error loading static element: {e}")
                    
            # Recreate robots
            id_to_robot: Dict[int, Robot] = {}
            for rdata in data.get("robots", []):
                try:
                    robot = Robot(
                        position=tuple(rdata["position"]),
                        color=tuple(rdata["color"])
                    )
                    
                    if rdata.get("energy") is not None:
                        robot.energy = rdata["energy"]
                        
                    brain_type = rdata.get("brain_type", "RuleBasedBrain")
                    if brain_type == "RLBrain":
                        robot.brain = RLBrain()
                    else:
                        robot.brain = RuleBasedBrain()
                    robot.brain.robot = robot
                    
                    self.add_robot(robot)
                    id_to_robot[robot.id] = robot
                except Exception as e:
                    print(f"Error loading robot: {e}")
                    
            # Reconstruct connections
            for r, rdata in zip(self.robots, data.get("robots", [])):
                if "connections" in rdata:
                    for conn_id in rdata["connections"]:
                        partner = id_to_robot.get(conn_id)
                        if partner:
                            r.connect(partner)
                            
        except Exception as e:
            raise IOError(f"Failed to load world state: {e}")
