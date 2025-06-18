"""Unit tests for the BaseElement class."""

import unittest
from unittest.mock import Mock
from vbe_3d.core.base_element import BaseElement


class TestBaseElement(unittest.TestCase):
    """Test cases for the BaseElement class."""

    def setUp(self):
        """Set up test fixtures."""
        self.position = (1.0, 2.0, 3.0)
        self.color = (0.5, 0.5, 0.5)
        self.element = BaseElement(self.position, self.color)

    def test_init(self):
        """Test BaseElement initialization."""
        self.assertEqual(self.element.position.x, 1.0)
        self.assertEqual(self.element.position.y, 2.0)
        self.assertEqual(self.element.position.z, 3.0)
        self.assertEqual(self.element.color, self.color)
        self.assertIsNone(self.element.world)

    def test_position_vector(self):
        """Test that position is stored as Vec3."""
        from ursina import Vec3
        self.assertIsInstance(self.element.position, Vec3)

    def test_color_storage(self):
        """Test that color is stored correctly."""
        self.assertEqual(self.element.color, (0.5, 0.5, 0.5))

    def test_world_assignment(self):
        """Test that world can be assigned."""
        mock_world = Mock()
        self.element.world = mock_world
        self.assertEqual(self.element.world, mock_world)


if __name__ == '__main__':
    unittest.main() 