from __future__ import annotations

import json
import math
from typing import List, Dict, Set, Optional, Tuple, TYPE_CHECKING, Any
from dataclasses import dataclass
from enum import Enum
from ursina import Vec3

from vbe_3d.engine.base import Engine
from vbe_3d.core.robot import Robot
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

class World:
    """Simulation world containing robots and static elements, and managing their interactions."""
    
    def __init__(self, engine: Engine):
        """Initialize the world with a rendering engine.
        
        Args:
            engine: The rendering/physics engine to use for visualization.
        """
        self.engine = engine
        self.robots: List[Robot] = []
        self.static_elements: List[StaticElement] = []
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
        """Add a robot to the world and spawn its visual representation.
        
        Args:
            robot: The robot to add to the world.
            
        Raises:
            ValueError: If the robot is already in the world.
        """
        if robot in self.robots:
            raise ValueError("Robot already exists in world")
        self.robots.append(robot)
        self.engine.add_object(robot)
        robot.world = self

    def add_static(self, element: StaticElement) -> None:
        """Add a static element (resource or obstacle) to the world.
        
        Args:
            element: The static element to add.
            
        Raises:
            ValueError: If the element is already in the world.
        """
        if element in self.static_elements:
            raise ValueError("Static element already exists in world")
        self.static_elements.append(element)
        self.engine.add_object(element)
        element.world = self

    def remove_robot(self, robot: Robot) -> None:
        """Remove a robot from the world.
        
        Args:
            robot: The robot to remove.
        """
        if robot in self.robots:
            self.robots.remove(robot)
            self.engine.remove_object(robot)
            # Clean up connections
            for r in self.robots:
                if robot in r.connections:
                    del r.connections[robot]

    def remove_static(self, element: StaticElement) -> None:
        """Remove a static element from the world.
        
        Args:
            element: The static element to remove.
        """
        if element in self.static_elements:
            self.static_elements.remove(element)
            self.engine.remove_object(element)

    def step(self) -> None:
        """Advance the simulation by one time step (tick)."""
        self.time_step += 1
        
        # Update spatial index for proximity queries
        self._update_spatial_index()
        
        # Process each robot's actions
        for robot in list(self.robots):
            try:
                observation = robot.perceive(self)
                action = robot.brain.decide_action(observation)
                robot.act(action)
            except Exception as e:
                print(f"Error processing robot {robot.id}: {e}")
                print(f"Robot position type: {type(robot.position)}")
                print(f"Robot position value: {robot.position}")
                print(f"Robot state: {robot.state}")
                print(f"Last action: {action}")
                import traceback
                print("Full traceback:")
                print(traceback.format_exc())
                
        # Handle interactions between objects
        self._handle_interactions()

    def _handle_interactions(self) -> None:
        """Handle interactions between objects: collisions, connections, resource usage, reproduction."""
        # Process robot-robot interactions
        for i, r1 in enumerate(self.robots):
            nearby = self._get_nearby_objects(r1.position, 1.1)
            for r2 in nearby:
                if isinstance(r2, Robot) and r2 != r1:
                    dist = math.dist(r1.position, r2.position)
                    if dist < 1.1:
                        r1.connect(r2)
                    else:
                        r1.disconnect(r2)
                        
        # Process robot-static interactions
        for robot in self.robots:
            nearby = self._get_nearby_objects(robot.position, 0.5)
            for elem in nearby:
                if isinstance(elem, StaticElement):
                    dist = math.dist(robot.position, elem.position)
                    if dist < 0.5:
                        if hasattr(elem, 'resource_value'):
                            robot.energy += elem.resource_value
                        self.remove_static(elem)
                        
        # Handle reproduction
        for r in list(self.robots):
            for partner, conn_level in r.connections.items():
                if conn_level >= 3 and self.time_step % 50 == 0:
                    try:
                        child = r.reproduce(partner)
                        if child:
                            # Create new Vec3 position offset from parent
                            child.position = Vec3(r.position.x + 1, r.position.y, r.position.z)
                            self.add_robot(child)
                            r.energy *= 0.5
                            partner.energy *= 0.5
                    except Exception as e:
                        print(f"Error during reproduction: {e}")

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
