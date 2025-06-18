"""Unit tests for the utils module."""

import unittest
from vbe_3d.utils.geometry import add_vec
from vbe_3d.utils.id_manager import next_id


class TestGeometry(unittest.TestCase):
    """Test cases for the geometry utility functions."""

    def test_add_vec(self):
        """Test vector addition."""
        a = (1.0, 2.0, 3.0)
        b = (4.0, 5.0, 6.0)
        
        result = add_vec(a, b)
        
        self.assertEqual(result, [5.0, 7.0, 9.0])

    def test_add_vec_negative(self):
        """Test vector addition with negative values."""
        a = (1.0, -2.0, 3.0)
        b = (-4.0, 5.0, -6.0)
        
        result = add_vec(a, b)
        
        self.assertEqual(result, [-3.0, 3.0, -3.0])

    def test_add_vec_zero(self):
        """Test vector addition with zero vectors."""
        a = (0.0, 0.0, 0.0)
        b = (1.0, 2.0, 3.0)
        
        result = add_vec(a, b)
        
        self.assertEqual(result, [1.0, 2.0, 3.0])

    def test_add_vec_float(self):
        """Test vector addition with float values."""
        a = (1.5, 2.7, 3.2)
        b = (4.1, 5.3, 6.8)
        
        result = add_vec(a, b)
        
        self.assertEqual(result, [5.6, 8.0, 10.0])


class TestIdManager(unittest.TestCase):
    """Test cases for the ID manager."""

    def test_next_id_sequential(self):
        """Test that IDs are generated sequentially."""
        id1 = next_id()
        id2 = next_id()
        id3 = next_id()
        
        self.assertEqual(id2, id1 + 1)
        self.assertEqual(id3, id2 + 1)

    def test_next_id_unique(self):
        """Test that IDs are unique."""
        ids = set()
        for _ in range(100):
            new_id = next_id()
            self.assertNotIn(new_id, ids)
            ids.add(new_id)

    def test_next_id_type(self):
        """Test that IDs are integers."""
        new_id = next_id()
        self.assertIsInstance(new_id, int)

    def test_next_id_positive(self):
        """Test that IDs are non-negative."""
        new_id = next_id()
        self.assertGreaterEqual(new_id, 0)


if __name__ == '__main__':
    unittest.main() 