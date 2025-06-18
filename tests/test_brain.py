"""Unit tests for the brain modules."""

import unittest
from unittest.mock import Mock, patch
import torch
import numpy as np
from vbe_3d.brain.base_brain import RobotBrain
from vbe_3d.brain.rule_based import RuleBasedBrain
from vbe_3d.brain.rl_brain import RLBrain
from vbe_3d.brain.factory import brain_from_export


class TestRobotBrain(unittest.TestCase):
    """Test cases for the RobotBrain base class."""

    def test_init(self):
        """Test RobotBrain initialization."""
        # Use RuleBasedBrain as a concrete implementation
        brain = RuleBasedBrain()
        self.assertIsNone(brain.robot)

    def test_clone(self):
        """Test brain cloning."""
        # Use RuleBasedBrain as a concrete implementation
        brain = RuleBasedBrain()
        brain.robot = Mock()
        
        cloned = brain.clone()
        
        self.assertIsInstance(cloned, RuleBasedBrain)
        self.assertIsNone(cloned.robot)  # Robot reference should not be cloned

    def test_export(self):
        """Test brain export."""
        # Use RuleBasedBrain as a concrete implementation
        brain = RuleBasedBrain()
        export_data = brain.export()
        
        self.assertEqual(export_data["type"], "RuleBasedBrain")


class TestRuleBasedBrain(unittest.TestCase):
    """Test cases for the RuleBasedBrain class."""

    def setUp(self):
        """Set up test fixtures."""
        self.brain = RuleBasedBrain()
        self.robot = Mock()
        self.brain.robot = self.robot

    def test_init(self):
        """Test RuleBasedBrain initialization."""
        self.assertIsInstance(self.brain, RuleBasedBrain)
        self.assertIsInstance(self.brain, RobotBrain)

    def test_decide_action_with_resource_nearby(self):
        """Test decision making when resource is nearby."""
        # Resource at (5, 0, 0) - robot should move +X
        observation = [5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        
        action = self.brain.decide_action(observation)
        
        self.assertEqual(action, 1)  # Move +X

    def test_decide_action_with_resource_negative_x(self):
        """Test decision making when resource is in negative X direction."""
        # Resource at (-5, 0, 0) - robot should move -X
        observation = [-5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        
        action = self.brain.decide_action(observation)
        
        self.assertEqual(action, 2)  # Move -X

    def test_decide_action_with_resource_in_z(self):
        """Test decision making when resource is in Z direction."""
        # Resource at (0, 0, 5) - robot should move +Z
        observation = [0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        
        action = self.brain.decide_action(observation)
        
        self.assertEqual(action, 3)  # Move +Z

    def test_decide_action_with_resource_in_y(self):
        """Test decision making when resource is in Y direction."""
        # Resource at (0, 5, 0) - robot should move +Y
        observation = [0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        
        action = self.brain.decide_action(observation)
        
        self.assertEqual(action, 5)  # Move +Y

    def test_decide_action_no_resource(self):
        """Test decision making when no resource is nearby."""
        # No significant resource nearby
        observation = [0.05, 0.05, 0.05, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        
        # Set up the mock robot with proper energy attribute
        self.robot.energy = 50.0  # Set energy to a value > 10
        
        action = self.brain.decide_action(observation)
        
        # Should be random choice from [0,1,2,3,4] (no vertical movement)
        self.assertIn(action, [0, 1, 2, 3, 4])

    def test_decide_action_low_energy(self):
        """Test decision making when energy is low."""
        self.robot.energy = 5.0  # Low energy
        
        observation = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.05, 0.0, 0.0]
        
        action = self.brain.decide_action(observation)
        
        self.assertEqual(action, 0)  # Should do nothing to conserve energy

    def test_export(self):
        """Test RuleBasedBrain export."""
        export_data = self.brain.export()
        
        self.assertEqual(export_data["type"], "RuleBasedBrain")


class TestRLBrain(unittest.TestCase):
    """Test cases for the RLBrain class."""

    def setUp(self):
        """Set up test fixtures."""
        self.brain = RLBrain(observation_dim=9, action_dim=7)
        self.robot = Mock()
        self.brain.robot = self.robot

    def test_init(self):
        """Test RLBrain initialization."""
        self.assertIsInstance(self.brain, RLBrain)
        self.assertIsInstance(self.brain, RobotBrain)
        self.assertEqual(self.brain.observation_dim, 9)
        self.assertEqual(self.brain.action_dim, 7)
        self.assertIsInstance(self.brain.model, torch.nn.Module)
        self.assertIsInstance(self.brain.optimizer, torch.optim.Adam)
        self.assertEqual(len(self.brain.memory), 0)

    def test_decide_action(self):
        """Test RLBrain decision making."""
        observation = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 0.5, 0.1, 0.2]
        
        action = self.brain.decide_action(observation)
        
        # Should return a valid action index
        self.assertIsInstance(action, int)
        self.assertGreaterEqual(action, 0)
        self.assertLess(action, 7)

    def test_decide_action_wrong_dimension(self):
        """Test RLBrain with wrong observation dimension."""
        observation = [1.0, 2.0, 3.0]  # Wrong dimension
        
        with self.assertRaises(ValueError):
            self.brain.decide_action(observation)

    def test_learn(self):
        """Test RLBrain learning."""
        obs = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 0.5, 0.1, 0.2]
        action = 1
        reward = 10.0
        next_obs = [1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 0.6, 0.2, 0.3]
        
        self.brain.learn(obs, action, reward, next_obs)
        
        # Memory should contain the experience
        self.assertEqual(len(self.brain.memory), 1)
        self.assertEqual(self.brain.memory[0]["obs"], obs)
        self.assertEqual(self.brain.memory[0]["action"], action)
        self.assertEqual(self.brain.memory[0]["reward"], reward)
        self.assertEqual(self.brain.memory[0]["next_obs"], next_obs)

    def test_learn_memory_limit(self):
        """Test RLBrain memory limit."""
        # Add more experiences than memory limit
        for i in range(self.brain.max_memory_size + 10):
            obs = [float(i)] * 9
            self.brain.learn(obs, 0, 1.0, obs)
        
        # Memory should be limited
        self.assertEqual(len(self.brain.memory), self.brain.max_memory_size)

    def test_update_network(self):
        """Test neural network update."""
        # Add enough experiences to trigger learning
        for i in range(32):
            obs = [float(i)] * 9
            self.brain.learn(obs, 0, 1.0, obs)
        
        # Network should be updated
        initial_params = {name: param.clone() for name, param in self.brain.model.named_parameters()}
        
        # Trigger another learning step
        self.brain.learn([1.0] * 9, 0, 1.0, [1.0] * 9)
        
        # Parameters should have changed
        current_params = {name: param.clone() for name, param in self.brain.model.named_parameters()}
        
        # At least some parameters should have changed
        param_changed = False
        for name in initial_params:
            if not torch.equal(initial_params[name], current_params[name]):
                param_changed = True
                break
        
        self.assertTrue(param_changed)

    def test_export_params(self):
        """Test RLBrain parameter export."""
        params = self.brain.export_params()
        
        self.assertEqual(params["type"], "RLBrain")
        self.assertEqual(params["observation_dim"], 9)
        self.assertEqual(params["action_dim"], 7)
        self.assertIn("weights", params)

    def test_from_params(self):
        """Test RLBrain creation from parameters."""
        params = self.brain.export_params()
        new_brain = RLBrain.from_params(params)
        
        self.assertEqual(new_brain.observation_dim, 9)
        self.assertEqual(new_brain.action_dim, 7)
        
        # Test that the networks produce similar outputs
        test_input = torch.randn(1, 9)
        with torch.no_grad():
            output1 = self.brain.model(test_input)
            output2 = new_brain.model(test_input)
        
        # Outputs should be identical since weights are the same
        self.assertTrue(torch.equal(output1, output2))


class TestBrainFactory(unittest.TestCase):
    """Test cases for the brain factory."""

    def test_brain_from_export_rl(self):
        """Test factory with RLBrain export."""
        brain = RLBrain()
        export_data = brain.export()
        
        created_brain = brain_from_export(export_data)
        
        self.assertIsInstance(created_brain, RLBrain)

    def test_brain_from_export_rule_based(self):
        """Test factory with RuleBasedBrain export."""
        brain = RuleBasedBrain()
        export_data = brain.export()
        
        created_brain = brain_from_export(export_data)
        
        self.assertIsInstance(created_brain, RuleBasedBrain)

    def test_brain_from_export_unknown_type(self):
        """Test factory with unknown brain type."""
        export_data = {"type": "UnknownBrain"}
        
        created_brain = brain_from_export(export_data)
        
        # Should default to RuleBasedBrain
        self.assertIsInstance(created_brain, RuleBasedBrain)


if __name__ == '__main__':
    unittest.main() 