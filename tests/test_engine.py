"""Unit tests for the engine module."""

import unittest
from unittest.mock import Mock, patch
from vbe_3d.engine.base import BaseEngine
from vbe_3d.core.robot import Robot
from vbe_3d.core.static_element import StaticElement


class MockEngine(BaseEngine):
    """Mock engine for testing."""
    
    def __init__(self):
        self.objects = []
        self.updated_objects = []
        self.removed_objects = []
        self.running = False
        
    def add_object(self, obj):
        self.objects.append(obj)
        
    def remove_object(self, obj):
        self.removed_objects.append(obj)
        if obj in self.objects:
            self.objects.remove(obj)
            
    def update_object(self, obj):
        self.updated_objects.append(obj)
        
    def run(self, world):
        self.running = True
        
    def cleanup(self):
        self.running = False


class TestBaseEngine(unittest.TestCase):
    """Test cases for the BaseEngine abstract class."""

    def test_base_engine_instantiation(self):
        """Test that BaseEngine cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            BaseEngine()


class TestMockEngine(unittest.TestCase):
    """Test cases for the MockEngine implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = MockEngine()
        self.robot = Robot(position=(0, 0, 0))
        self.static_element = StaticElement(position=(5, 0, 0))

    def test_init(self):
        """Test MockEngine initialization."""
        self.assertEqual(self.engine.objects, [])
        self.assertEqual(self.engine.updated_objects, [])
        self.assertEqual(self.engine.removed_objects, [])
        self.assertFalse(self.engine.running)

    def test_add_object(self):
        """Test adding objects to the engine."""
        self.engine.add_object(self.robot)
        self.engine.add_object(self.static_element)
        
        self.assertIn(self.robot, self.engine.objects)
        self.assertIn(self.static_element, self.engine.objects)
        self.assertEqual(len(self.engine.objects), 2)

    def test_remove_object(self):
        """Test removing objects from the engine."""
        self.engine.add_object(self.robot)
        self.engine.add_object(self.static_element)
        
        self.engine.remove_object(self.robot)
        
        self.assertNotIn(self.robot, self.engine.objects)
        self.assertIn(self.static_element, self.engine.objects)
        self.assertIn(self.robot, self.engine.removed_objects)

    def test_remove_nonexistent_object(self):
        """Test removing an object that doesn't exist."""
        self.engine.remove_object(self.robot)
        
        self.assertIn(self.robot, self.engine.removed_objects)
        self.assertEqual(len(self.engine.objects), 0)

    def test_update_object(self):
        """Test updating objects in the engine."""
        self.engine.add_object(self.robot)
        
        self.engine.update_object(self.robot)
        
        self.assertIn(self.robot, self.engine.updated_objects)
        self.assertEqual(len(self.engine.updated_objects), 1)

    def test_run(self):
        """Test running the engine."""
        world = Mock()
        
        self.engine.run(world)
        
        self.assertTrue(self.engine.running)

    def test_cleanup(self):
        """Test cleaning up the engine."""
        self.engine.running = True
        
        self.engine.cleanup()
        
        self.assertFalse(self.engine.running)


class TestEngineIntegration(unittest.TestCase):
    """Test cases for engine integration with world objects."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = MockEngine()
        self.robot = Robot(position=(0, 0, 0))
        self.static_element = StaticElement(position=(5, 0, 0))

    def test_engine_with_robot(self):
        """Test engine operations with robot objects."""
        # Add robot
        self.engine.add_object(self.robot)
        self.assertIn(self.robot, self.engine.objects)
        
        # Update robot
        self.robot.position = (1, 0, 0)
        self.engine.update_object(self.robot)
        self.assertIn(self.robot, self.engine.updated_objects)
        
        # Remove robot
        self.engine.remove_object(self.robot)
        self.assertNotIn(self.robot, self.engine.objects)
        self.assertIn(self.robot, self.engine.removed_objects)

    def test_engine_with_static_element(self):
        """Test engine operations with static element objects."""
        # Add static element
        self.engine.add_object(self.static_element)
        self.assertIn(self.static_element, self.engine.objects)
        
        # Update static element
        self.static_element.resource_value = 50.0
        self.engine.update_object(self.static_element)
        self.assertIn(self.static_element, self.engine.updated_objects)
        
        # Remove static element
        self.engine.remove_object(self.static_element)
        self.assertNotIn(self.static_element, self.engine.objects)
        self.assertIn(self.static_element, self.engine.removed_objects)

    def test_engine_multiple_objects(self):
        """Test engine operations with multiple objects."""
        # Add multiple objects
        self.engine.add_object(self.robot)
        self.engine.add_object(self.static_element)
        
        self.assertEqual(len(self.engine.objects), 2)
        
        # Update all objects
        self.engine.update_object(self.robot)
        self.engine.update_object(self.static_element)
        
        self.assertEqual(len(self.engine.updated_objects), 2)
        
        # Remove all objects
        self.engine.remove_object(self.robot)
        self.engine.remove_object(self.static_element)
        
        self.assertEqual(len(self.engine.objects), 0)
        self.assertEqual(len(self.engine.removed_objects), 2)


if __name__ == '__main__':
    unittest.main() 