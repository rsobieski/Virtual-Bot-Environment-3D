"""Unit tests for the Robot class."""

import unittest
from unittest.mock import Mock, patch
from vbe_3d.core.robot import Robot, RobotState, ConnectionLevel, RobotStats
from vbe_3d.brain.rule_based import RuleBasedBrain
from vbe_3d.brain.rl_brain import RLBrain


class TestRobot(unittest.TestCase):
    """Test cases for the Robot class."""

    def setUp(self):
        """Set up test fixtures."""
        self.position = (1.0, 2.0, 3.0)
        self.color = (0.5, 0.5, 0.5)
        self.brain = RuleBasedBrain()
        self.robot = Robot(
            position=self.position,
            color=self.color,
            brain=self.brain,
            max_energy=100.0,
            movement_cost=1.0,
            reproduction_threshold=20.0
        )

    def test_init(self):
        """Test Robot initialization."""
        self.assertEqual(self.robot.position.x, 1.0)
        self.assertEqual(self.robot.position.y, 2.0)
        self.assertEqual(self.robot.position.z, 3.0)
        self.assertEqual(self.robot.color, self.color)
        self.assertEqual(self.robot.energy, 100.0)
        self.assertEqual(self.robot.max_energy, 100.0)
        self.assertEqual(self.robot.movement_cost, 1.0)
        self.assertEqual(self.robot.reproduction_threshold, 20.0)
        self.assertEqual(self.robot.state, RobotState.IDLE)
        self.assertEqual(self.robot.connections, {})
        self.assertEqual(self.robot.brain, self.brain)
        self.assertEqual(self.robot.brain.robot, self.robot)

    def test_init_with_defaults(self):
        """Test Robot initialization with default values."""
        robot = Robot()
        self.assertEqual(robot.position.x, 0.0)
        self.assertEqual(robot.position.y, 0.0)
        self.assertEqual(robot.position.z, 0.0)
        self.assertEqual(robot.color, (0.2, 0.8, 0.2))  # Default green
        self.assertEqual(robot.energy, 100.0)
        self.assertEqual(robot.max_energy, 100.0)
        self.assertEqual(robot.movement_cost, 1.0)
        self.assertEqual(robot.reproduction_threshold, 20.0)
        self.assertIsInstance(robot.brain, RuleBasedBrain)

    def test_init_without_brain(self):
        """Test Robot initialization without providing a brain."""
        robot = Robot(position=(0, 0, 0))
        self.assertIsInstance(robot.brain, RuleBasedBrain)
        self.assertEqual(robot.brain.robot, robot)

    def test_act_no_op(self):
        """Test robot action with no-op."""
        initial_energy = self.robot.energy
        initial_position = self.robot.position
        initial_state = self.robot.state
        
        self.robot.act(0)
        
        self.assertEqual(self.robot.energy, initial_energy)
        self.assertEqual(self.robot.position, initial_position)
        self.assertEqual(self.robot.state, RobotState.IDLE)

    def test_act_movement(self):
        """Test robot movement actions."""
        # Test movement in +X direction
        initial_energy = self.robot.energy
        initial_position = self.robot.position
        
        self.robot.act(1)  # Move +X
        
        self.assertEqual(self.robot.position.x, initial_position.x + 1.0)
        self.assertEqual(self.robot.position.y, initial_position.y)
        self.assertEqual(self.robot.position.z, initial_position.z)
        self.assertEqual(self.robot.energy, initial_energy - self.robot.movement_cost)
        self.assertEqual(self.robot.state, RobotState.MOVING)

    def test_act_all_directions(self):
        """Test robot movement in all directions."""
        # Test -X
        self.robot.act(2)
        self.assertEqual(self.robot.position.x, 0.0)
        
        # Test +Z
        self.robot.act(3)
        self.assertEqual(self.robot.position.z, 4.0)
        
        # Test -Z
        self.robot.act(4)
        self.assertEqual(self.robot.position.z, 3.0)
        
        # Test +Y
        self.robot.act(5)
        self.assertEqual(self.robot.position.y, 3.0)
        
        # Test -Y
        self.robot.act(6)
        self.assertEqual(self.robot.position.y, 2.0)

    def test_act_death(self):
        """Test robot death when energy reaches zero."""
        self.robot.energy = 1.0
        
        self.robot.act(1)  # Move and consume energy
        
        self.assertEqual(self.robot.energy, 0.0)
        self.assertEqual(self.robot.state, RobotState.DEAD)

    def test_connect(self):
        """Test robot connection formation."""
        other_robot = Robot(position=(0, 0, 0))
        
        self.robot.connect(other_robot)
        
        self.assertEqual(self.robot.connections[other_robot], ConnectionLevel.WEAK.value)
        self.assertEqual(other_robot.connections[self.robot], ConnectionLevel.WEAK.value)
        self.assertEqual(self.robot.stats.connections_made, 1)

    def test_connect_strengthening(self):
        """Test connection strengthening."""
        other_robot = Robot(position=(0, 0, 0))
        
        # Initial connection
        self.robot.connect(other_robot)
        self.assertEqual(self.robot.connections[other_robot], ConnectionLevel.WEAK.value)
        
        # Strengthen connection
        self.robot.connect(other_robot)
        self.assertEqual(self.robot.connections[other_robot], ConnectionLevel.MEDIUM.value)

    def test_disconnect(self):
        """Test robot disconnection."""
        other_robot = Robot(position=(0, 0, 0))
        
        # Form connection
        self.robot.connect(other_robot)
        self.robot.connect(other_robot)  # Strengthen to medium
        
        # Weaken connection
        self.robot.disconnect(other_robot)
        self.assertEqual(self.robot.connections[other_robot], ConnectionLevel.WEAK.value)
        
        # Break connection
        self.robot.disconnect(other_robot)
        self.assertNotIn(other_robot, self.robot.connections)
        self.assertNotIn(self.robot, other_robot.connections)

    def test_disconnect_permanent(self):
        """Test that permanent connections cannot be broken."""
        other_robot = Robot(position=(0, 0, 0))
        
        # Form permanent connection
        self.robot.connections[other_robot] = ConnectionLevel.PERMANENT.value
        other_robot.connections[self.robot] = ConnectionLevel.PERMANENT.value
        
        # Try to disconnect
        self.robot.disconnect(other_robot)
        
        # Connection should remain permanent
        self.assertEqual(self.robot.connections[other_robot], ConnectionLevel.PERMANENT.value)

    def test_reproduce_insufficient_energy(self):
        """Test reproduction with insufficient energy."""
        other_robot = Robot(position=(0, 0, 0))
        self.robot.energy = 10.0  # Below threshold
        
        child = self.robot.reproduce(other_robot)
        
        self.assertIsNone(child)

    def test_reproduce_success(self):
        """Test successful reproduction."""
        other_robot = Robot(position=(0, 0, 0))
        other_robot.color = (1.0, 0.0, 0.0)  # Red
        self.robot.energy = 50.0  # Above threshold
        other_robot.energy = 50.0  # Above threshold
        
        child = self.robot.reproduce(other_robot)
        
        self.assertIsNotNone(child)
        self.assertIsInstance(child, Robot)
        self.assertEqual(child.position, self.robot.position)
        # Color should be averaged
        expected_color = tuple((a + b) / 2.0 for a, b in zip(self.robot.color, other_robot.color))
        self.assertEqual(child.color, expected_color)
        self.assertEqual(self.robot.state, RobotState.REPRODUCING)
        self.assertEqual(self.robot.stats.offspring_produced, 1)

    def test_collect_resource(self):
        """Test resource collection."""
        initial_energy = self.robot.energy
        resource_value = 25.0
        
        self.robot.collect_resource(resource_value)
        
        self.assertEqual(self.robot.energy, min(initial_energy + resource_value, self.robot.max_energy))
        self.assertEqual(self.robot.state, RobotState.COLLECTING)
        self.assertEqual(self.robot.stats.resources_collected, 1)

    def test_collect_resource_max_energy(self):
        """Test resource collection with energy cap."""
        self.robot.energy = 95.0
        resource_value = 25.0
        
        self.robot.collect_resource(resource_value)
        
        self.assertEqual(self.robot.energy, self.robot.max_energy)  # Should be capped

    @patch('vbe_3d.core.robot.math.dist')
    def test_perceive(self, mock_dist):
        """Test robot perception."""
        mock_world = Mock()
        mock_world.static_elements = []
        mock_world.robots = []
        mock_world._get_nearby_objects = Mock(return_value=[])  # Mock the spatial index method
        
        # Mock distance calculation
        mock_dist.return_value = 5.0
        
        observation = self.robot.perceive(mock_world)
        
        # Should return 9 observations: 3 for nearest resource, 3 for nearest robot, 
        # 1 for energy, 1 for connections, 1 for state
        self.assertEqual(len(observation), 9)
        self.assertEqual(observation[6], 1.0)  # Normalized energy (100/100)
        self.assertEqual(observation[7], 0.0)  # Normalized connections (0/10)

    def test_to_dict(self):
        """Test robot serialization."""
        data = self.robot.to_dict()
        
        self.assertEqual(data["id"], self.robot.id)
        self.assertEqual(data["pos"], self.position)
        self.assertEqual(data["col"], self.color)
        self.assertEqual(data["energy"], self.robot.energy)
        self.assertEqual(data["max_energy"], self.robot.max_energy)
        self.assertEqual(data["movement_cost"], self.robot.movement_cost)
        self.assertEqual(data["reproduction_threshold"], self.robot.reproduction_threshold)
        self.assertEqual(data["connections"], [])
        self.assertEqual(data["state"], "IDLE")
        self.assertIn("stats", data)
        self.assertIn("brain", data)

    def test_from_dict(self):
        """Test robot deserialization."""
        original_data = self.robot.to_dict()
        new_robot = Robot.from_dict(original_data)
        
        self.assertEqual(new_robot.id, self.robot.id)
        self.assertEqual(new_robot.position, self.robot.position)
        self.assertEqual(new_robot.color, self.robot.color)
        self.assertEqual(new_robot.energy, self.robot.energy)
        self.assertEqual(new_robot.max_energy, self.robot.max_energy)
        self.assertEqual(new_robot.state, self.robot.state)


class TestRobotState(unittest.TestCase):
    """Test cases for the RobotState enum."""

    def test_enum_values(self):
        """Test that RobotState enum has expected values."""
        self.assertEqual(RobotState.IDLE.value, 1)
        self.assertEqual(RobotState.MOVING.value, 2)
        self.assertEqual(RobotState.COLLECTING.value, 3)
        self.assertEqual(RobotState.REPRODUCING.value, 4)
        self.assertEqual(RobotState.DEAD.value, 5)


class TestConnectionLevel(unittest.TestCase):
    """Test cases for the ConnectionLevel enum."""

    def test_enum_values(self):
        """Test that ConnectionLevel enum has expected values."""
        self.assertEqual(ConnectionLevel.NONE.value, 0)
        self.assertEqual(ConnectionLevel.WEAK.value, 1)
        self.assertEqual(ConnectionLevel.MEDIUM.value, 2)
        self.assertEqual(ConnectionLevel.STRONG.value, 3)
        self.assertEqual(ConnectionLevel.PERMANENT.value, 4)


class TestRobotStats(unittest.TestCase):
    """Test cases for the RobotStats dataclass."""

    def test_init(self):
        """Test RobotStats initialization."""
        stats = RobotStats(
            distance_traveled=10.5,
            resources_collected=5,
            connections_made=3,
            offspring_produced=2,
            energy_consumed=25.0,
            lifetime=100
        )
        
        self.assertEqual(stats.distance_traveled, 10.5)
        self.assertEqual(stats.resources_collected, 5)
        self.assertEqual(stats.connections_made, 3)
        self.assertEqual(stats.offspring_produced, 2)
        self.assertEqual(stats.energy_consumed, 25.0)
        self.assertEqual(stats.lifetime, 100)

    def test_default_values(self):
        """Test RobotStats default values."""
        stats = RobotStats()
        
        self.assertEqual(stats.distance_traveled, 0.0)
        self.assertEqual(stats.resources_collected, 0)
        self.assertEqual(stats.connections_made, 0)
        self.assertEqual(stats.offspring_produced, 0)
        self.assertEqual(stats.energy_consumed, 0.0)
        self.assertEqual(stats.lifetime, 0)


if __name__ == '__main__':
    unittest.main() 