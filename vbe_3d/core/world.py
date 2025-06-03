from __future__ import annotations

import json
import math
from typing import List, Dict, TYPE_CHECKING, Any

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

class World:
    """Simulation world containing robots and static elements, and managing their interactions."""
    def __init__(self, engine: Engine):
        self.engine = engine        # the rendering/physics engine used
        self.robots = []           # list of Robot objects in the world
        self.static_elements = []  # list of StaticElement objects in the world
        self.time_step = 0         # simulation step counter
    
    def add_robot(self, robot: Any) -> None:
        """Add a robot to the world and spawn its visual representation."""
        self.robots.append(robot)
        self.engine.add_object(robot)
        robot.world = self

    def add_static(self, element: Any) -> None:
        """Add a static element (resource or obstacle) to the world."""
        self.static_elements.append(element)
        self.engine.add_object(element)
        element.world = self

    def remove_robot(self, robot: Any) -> None:
        """Remove a robot from the world (e.g., if destroyed or consumed)."""
        if robot in self.robots:
            self.robots.remove(robot)
        # remove visual representation
        self.engine.remove_object(robot)
        for r in self.robots:
            if robot in r.connections:
                del r.connections[robot]

    def remove_static(self, element: Any) -> None:
        """Remove a static element from the world."""
        if element in self.static_elements:
            self.static_elements.remove(element)
        self.engine.remove_object(element)

    def step(self) -> None:
        """Advance the simulation by one time step (tick)."""
        self.time_step += 1
        # each robot decides and executes an action
        for robot in list(self.robots):  
            # get the robot's decided action via its brain, after perceiving the environment
            observation = robot.perceive(self)
            action = robot.brain.decide_action(observation)
            robot.act(action)  # execute the action (this could update robot.position or other state)
        self._handle_interactions()
        # visual updates will be handled by the engine in Engine.run loop after this step

    def _handle_interactions(self) -> None:
        """Handle interactions between objects: collisions, connections, resource usage, reproduction."""
        # check robot-robot proximity for connections
        for i, r1 in enumerate(self.robots):
            for r2 in self.robots[i+1:]:
                # compute distance between r1 and r2
                dx = r1.position[0] - r2.position[0]
                dy = r1.position[1] - r2.position[1]
                dz = r1.position[2] - r2.position[2]
                dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                if dist < 1.1:  # threshold for touching (assuming cubes of size ~1)
                    # they are very close, form or maintain a connection
                    r1.connect(r2)
                else:
                    # if too far, maybe break connection
                    r1.disconnect(r2)
        # check robot-static interactions (e.g., resource collection)
        for robot in self.robots:
            for elem in list(self.static_elements):
                # simple check: if robot is at same position (or very close) to a resource
                dx = robot.position[0] - elem.position[0]
                dy = robot.position[1] - elem.position[1]
                dz = robot.position[2] - elem.position[2]
                dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                if dist < 0.5:  # overlapping a resource
                    if hasattr(elem, 'resource_value'):
                        # robot "collects" the resource
                        robot.energy += elem.resource_value  # increase robot's energy
                    # remove the resource from world (consumed)
                    self.remove_static(elem)
        # check reproduction conditions (if robots connected strongly and other criteria)
            # in this simple logic, if two robots have a strong connection, create a child occasionally.
        for r in list(self.robots):
            # if robot has any strong connections:
            for partner, conn_level in r.connections.items():
                if conn_level >= 3:  # strong connection
                    # Simple rule: on strong connection, produce offspring at some interval
                    if self.time_step % 50 == 0:  # e.g., every 50 ticks while connected
                        child = r.reproduce(partner)
                        if child:
                            # Place child near the parents
                            px, py, pz = r.position
                            cx = px + 1  # offset new robot by 1 unit
                            cy = py
                            cz = pz
                            child.position = (cx, cy, cz)
                            self.add_robot(child)
                            # optionally reduce energy of parents as cost
                            r.energy *= 0.5
                            partner.energy *= 0.5

    def save_state(self, filepath: str) -> None:
        """Save the current world state to a JSON file."""
        data = {
            "time_step": self.time_step,
            "robots": [],
            "static": []
        }
        # save robot data
        for r in self.robots:
            robot_data = {
                "class": r.__class__.__name__,
                "position": r.position,
                "color": r.color,
                "energy": getattr(r, "energy", None),
                "connections": [r2.id for r2 in r.connections.keys()],
                # NOTE: not saving connection levels for simplicity, could be added
                "brain_type": r.brain.__class__.__name__,
                "brain_params": r.brain.export_params() if hasattr(r.brain, "export_params") else None
            }
            data["robots"].append(robot_data)
        # save static element data
        for e in self.static_elements:
            elem_data = {
                "class": e.__class__.__name__,
                "position": e.position,
                "color": e.color,
                "resource_value": getattr(e, "resource_value", None)
            }
            data["static"].append(elem_data)
        # write JSON to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_state(self, filepath: str) -> None:
        """Load world state from a JSON file (overwriting current world)."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        # clear current world
        for r in list(self.robots):
            self.remove_robot(r)
        for e in list(self.static_elements):
            self.remove_static(e)
        self.robots = []
        self.static_elements = []
        self.time_step = data.get("time_step", 0)
        # recreate static elements
        for elem_data in data.get("static", []):
            cls_name = elem_data["class"]
            # for now, we have maybe only one static class type
            if cls_name == "StaticElement" or cls_name == "Resource":
                elem = StaticElement(position=tuple(elem_data["position"]),
                                     color=tuple(elem_data["color"]),
                                     resource_value=elem_data.get("resource_value", 0))
            else:
                # unknown class; skip or handle accordingly
                continue
            self.add_static(elem)
        # recreate robots
        id_to_robot: Dict[int, Any] = {}
        for rdata in data.get("robots", []):
            # create robot (assuming Robot or subclass)
            robot = Robot(position=tuple(rdata["position"]), color=tuple(rdata["color"]))
            # restore energy if present
            if rdata.get("energy") is not None:
                robot.energy = rdata["energy"]
            # restore brain (for simplicity, we instantiate a similar type, without restoring internal trained params here)
            brain_type = rdata.get("brain_type", "RuleBasedBrain")
            if brain_type == "RLBrain":
                robot.brain = RLBrain()  # could load network weights if export_params provided data
            else:
                robot.brain = RuleBasedBrain()
            robot.brain.robot = robot  # link brain to robot
            # Add robot to world and mapping
            self.add_robot(robot)
            id_to_robot[robot.id] = robot
        # Reconstruct connections (note: we saved just connected IDs without level detail)
        # For simplicity, just connect any listed pairs at lowest level.
        for r, rdata in zip(self.robots, data.get("robots", [])):
            if "connections" in rdata:
                for conn_id in rdata["connections"]:
                    partner = id_to_robot.get(conn_id)
                    if partner:
                        r.connect(partner)
