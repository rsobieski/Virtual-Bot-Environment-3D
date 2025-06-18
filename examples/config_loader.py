"""Configuration loader for world and robot settings."""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

from vbe_3d.core.world import World
from vbe_3d.core.robot import Robot
from vbe_3d.core.static_element import StaticElement, ResourceType
from vbe_3d.brain.factory import brain_from_export
from vbe_3d.brain.rl_brain import RLBrain
from vbe_3d.brain.rule_based import RuleBasedBrain


class ConfigLoader:
    """Loads world configuration from JSON files."""
    
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """Load configuration from a JSON file.
        
        Args:
            config_path: Path to the JSON configuration file.
            
        Returns:
            Dictionary containing the configuration data.
        """
        with open(config_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def create_brain(brain_type: str):
        """Create a brain instance from brain type string.
        
        Args:
            brain_type: String identifier for the brain type.
            
        Returns:
            Brain instance.
        """
        if brain_type == "RLBrain":
            return RLBrain()
        elif brain_type == "RuleBasedBrain":
            return RuleBasedBrain()
        else:
            # Default to rule-based brain
            return RuleBasedBrain()
    
    @staticmethod
    def create_static_element(element_config: Dict[str, Any]) -> StaticElement:
        """Create a static element from configuration.
        
        Args:
            element_config: Configuration dictionary for the static element.
            
        Returns:
            StaticElement instance.
        """
        return StaticElement(
            position=tuple(element_config["position"]),
            color=tuple(element_config["color"]),
            resource_value=element_config["resource_value"],
            resource_type=ResourceType[element_config["resource_type"]],
            decay_rate=element_config.get("decay_rate", 0.0),
            respawn_time=element_config.get("respawn_time"),
            max_uses=element_config.get("max_uses"),
            is_obstacle=element_config.get("is_obstacle", False),
            is_collectible=element_config.get("is_collectible", True)
        )
    
    @staticmethod
    def create_robot(robot_config: Dict[str, Any]) -> Robot:
        """Create a robot from configuration.
        
        Args:
            robot_config: Configuration dictionary for the robot.
            
        Returns:
            Robot instance.
        """
        brain = ConfigLoader.create_brain(robot_config["brain_type"])
        
        return Robot(
            position=tuple(robot_config["position"]),
            color=tuple(robot_config["color"]),
            brain=brain,
            max_energy=robot_config.get("max_energy", 100.0),
            movement_cost=robot_config.get("movement_cost", 1.0),
            reproduction_threshold=robot_config.get("reproduction_threshold", 20.0)
        )
    
    @staticmethod
    def setup_world_from_config(world: World, config_path: str) -> None:
        """Set up a world with robots and static elements from configuration.
        
        Args:
            world: The world instance to populate.
            config_path: Path to the JSON configuration file.
        """
        config = ConfigLoader.load_config(config_path)
        
        # Add static elements
        for element_config in config["static_elements"]:
            element = ConfigLoader.create_static_element(element_config)
            world.add_static(element)
        
        # Add robots
        for robot_config in config["robots"]:
            robot = ConfigLoader.create_robot(robot_config)
            world.add_robot(robot)
    
    @staticmethod
    def create_world_from_config(engine, config_path: str) -> World:
        """Create a complete world from configuration.
        
        Args:
            engine: The engine instance to use.
            config_path: Path to the JSON configuration file.
            
        Returns:
            World instance populated with robots and static elements.
        """
        world = World(engine)
        ConfigLoader.setup_world_from_config(world, config_path)
        return world 