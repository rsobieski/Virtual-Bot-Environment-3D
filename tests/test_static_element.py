"""Unit tests for the StaticElement class."""

import unittest
from unittest.mock import Mock
from vbe_3d.core.static_element import StaticElement, ResourceType, ResourceProperties


class TestStaticElement(unittest.TestCase):
    """Test cases for the StaticElement class."""

    def setUp(self):
        """Set up test fixtures."""
        self.position = (1.0, 2.0, 3.0)
        self.color = (0.5, 0.5, 0.5)
        self.resource_value = 50.0
        self.element = StaticElement(
            position=self.position,
            color=self.color,
            resource_value=self.resource_value,
            resource_type=ResourceType.ENERGY
        )

    def test_init(self):
        """Test StaticElement initialization."""
        self.assertEqual(self.element.position.x, 1.0)
        self.assertEqual(self.element.position.y, 2.0)
        self.assertEqual(self.element.position.z, 3.0)
        self.assertEqual(self.element.color, self.color)
        self.assertEqual(self.element.resource_value, self.resource_value)
        self.assertEqual(self.element.resource_type, ResourceType.ENERGY)
        self.assertIsInstance(self.element.properties, ResourceProperties)
        self.assertFalse(self.element.is_obstacle)
        self.assertTrue(self.element.is_collectible)
        self.assertIsNone(self.element.respawn_timer)

    def test_default_values(self):
        """Test StaticElement with default values."""
        element = StaticElement(position=(0, 0, 0))
        self.assertEqual(element.color, (0.9, 0.6, 0.1))  # Default color
        self.assertEqual(element.resource_value, 20.0)  # Default resource value
        self.assertEqual(element.resource_type, ResourceType.ENERGY)  # Default type
        self.assertFalse(element.is_obstacle)
        self.assertTrue(element.is_collectible)

    def test_collect_resource(self):
        """Test resource collection."""
        initial_value = self.element.resource_value
        collected_value = self.element.collect()
        
        self.assertEqual(collected_value, initial_value)
        self.assertEqual(self.element.properties.current_uses, 1)

    def test_collect_non_collectible(self):
        """Test collecting from non-collectible resource."""
        self.element.is_collectible = False
        collected_value = self.element.collect()
        self.assertEqual(collected_value, 0.0)

    def test_collect_with_max_uses(self):
        """Test resource collection with max uses limit."""
        self.element.properties.max_uses = 2
        
        # First collection
        self.element.collect()
        self.assertTrue(self.element.is_collectible)
        
        # Second collection
        self.element.collect()
        self.assertFalse(self.element.is_collectible)

    def test_collect_with_respawn(self):
        """Test resource collection with respawn timer."""
        self.element.properties.respawn_time = 5
        
        collected_value = self.element.collect()
        self.assertEqual(collected_value, self.resource_value)
        self.assertFalse(self.element.is_collectible)
        self.assertEqual(self.element.respawn_timer, 5)

    def test_update_with_respawn(self):
        """Test update method with respawn timer."""
        self.element.respawn_timer = 1
        self.element.is_collectible = False
        
        self.element.update()
        
        # After update, respawn_timer should be 0 and respawn should be called
        # The respawn method sets respawn_timer to None
        self.assertIsNone(self.element.respawn_timer)
        self.assertTrue(self.element.is_collectible)

    def test_update_with_decay(self):
        """Test update method with decay rate."""
        self.element.properties.decay_rate = 5.0
        initial_value = self.element.resource_value
        
        self.element.update()
        self.assertEqual(self.element.resource_value, initial_value - 5.0)

    def test_respawn(self):
        """Test respawn method."""
        self.element.resource_value = 0.0
        self.element.properties.current_uses = 5
        self.element.is_collectible = False
        self.element.respawn_timer = 10
        
        self.element.respawn()
        
        self.assertEqual(self.element.resource_value, self.element.properties.value)
        self.assertEqual(self.element.properties.current_uses, 0)
        self.assertTrue(self.element.is_collectible)
        self.assertIsNone(self.element.respawn_timer)

    def test_to_dict(self):
        """Test serialization to dictionary."""
        data = self.element.to_dict()
        
        self.assertEqual(data["pos"], self.position)
        self.assertEqual(data["col"], self.color)
        self.assertEqual(data["val"], self.resource_value)
        self.assertEqual(data["type"], "ENERGY")
        self.assertFalse(data["is_obstacle"])
        self.assertTrue(data["is_collectible"])

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        original_data = self.element.to_dict()
        new_element = StaticElement.from_dict(original_data)
        
        self.assertEqual(new_element.position, self.element.position)
        self.assertEqual(new_element.color, self.element.color)
        self.assertEqual(new_element.resource_value, self.element.resource_value)
        self.assertEqual(new_element.resource_type, self.element.resource_type)


class TestResourceType(unittest.TestCase):
    """Test cases for the ResourceType enum."""

    def test_enum_values(self):
        """Test that ResourceType enum has expected values."""
        self.assertEqual(ResourceType.ENERGY.value, 1)
        self.assertEqual(ResourceType.MATERIAL.value, 2)
        self.assertEqual(ResourceType.SPECIAL.value, 3)


class TestResourceProperties(unittest.TestCase):
    """Test cases for the ResourceProperties dataclass."""

    def test_init(self):
        """Test ResourceProperties initialization."""
        props = ResourceProperties(
            type=ResourceType.ENERGY,
            value=100.0,
            decay_rate=1.0,
            respawn_time=10,
            max_uses=5
        )
        
        self.assertEqual(props.type, ResourceType.ENERGY)
        self.assertEqual(props.value, 100.0)
        self.assertEqual(props.decay_rate, 1.0)
        self.assertEqual(props.respawn_time, 10)
        self.assertEqual(props.max_uses, 5)
        self.assertEqual(props.current_uses, 0)


if __name__ == '__main__':
    unittest.main() 