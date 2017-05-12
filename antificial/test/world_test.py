#! /usr/bin/env python

import unittest
from framework import World, Field

class TestWorld(unittest.TestCase):

    def setUp(self):
        """minimum dimension in this test: 5 * 5 - the rest is dynamic"""
        self.width = 5
        self.height = 5
        self.player_count = 3
        self.ints_per_coordinate = 4 + self.player_count
        self.array_size = self.width * self.height * self.ints_per_coordinate
        self.world = World(self.width, self.height, self.player_count)

    def tearDown(self):
        self.width = None
        self.height = None
        self.player_count = None
        self.ints_per_coordinate = None
        self.world = None

    def test_init(self):
        self.assertEqual(self.world.width, self.width)
        self.assertEqual(self.world.height, self.height)
        self.assertEqual(self.world.player_count, self.player_count)
        self.assertEqual(len(self.world.player_food_indexes), self.player_count)
        self.assertEqual(self.world.ints_per_coordinate, self.ints_per_coordinate)
        self.assertEqual(self.world.array_size, self.array_size)

        """make sure every index is unique"""
        for index in ([self.world.ant_count_index, self.world.home_pheromone_index, self.world.food_pheromone_index] + self.world.player_food_indexes):
            self.assertNotEqual(index, self.world.nest_index)

        for index in ([self.world.nest_index, self.world.home_pheromone_index, self.world.food_pheromone_index] + self.world.player_food_indexes):
            self.assertNotEqual(index, self.world.ant_count_index)

        for index in ([self.world.nest_index, self.world.ant_count_index, self.world.food_pheromone_index] + self.world.player_food_indexes):
            self.assertNotEqual(index, self.world.home_pheromone_index)

        for index in ([self.world.nest_index, self.world.ant_count_index, self.world.home_pheromone_index] + self.world.player_food_indexes):
            self.assertNotEqual(index, self.world.food_pheromone_index)

        """make sure every player food index is unique (w/o other player indexes)"""
        for player_food_index in self.world.player_food_indexes:
            for index in [self.world.nest_index, self.world.ant_count_index, self.world.home_pheromone_index, self.world.food_pheromone_index]:
                self.assertNotEqual(index, player_food_index)

        """make sure every player food index is unique (comparing the player food indexes)"""
        player_food_indexes_copy = self.world.player_food_indexes + []
        while len(player_food_indexes_copy) > 0:
            current_index = player_food_indexes_copy.pop()
            for compare_index in player_food_indexes_copy:
                self.assertNotEqual(current_index, compare_index)

        """check data array size and values"""
        self.assertEqual(len(self.world.data), self.width * self.height * self.ints_per_coordinate)

        for value in self.world.data:
            self.assertEqual(value, 0)

    def test_get(self):
        """make sure boundaries get checked"""
        self.assertIsNone(self.world.get(-1, 0))
        self.assertIsNone(self.world.get(0, -1))
        self.assertIsNone(self.world.get(0, self.height))
        self.assertIsNone(self.world.get(self.width, 0))
        
        """make sure empty fields are empty"""
        field = self.world.get(0, 0)
        self.assertIsNotNone(field)
        self.assertIsInstance(field, Field)
        self.assertEqual(field.x, 0)
        self.assertEqual(field.y, 0)
        self.assertEqual(field.is_nest, 0)
        self.assertEqual(field.ant_count, 0)
        self.assertEqual(field.home_pheromone_level, 0)
        self.assertEqual(field.food_pheromone_level, 0)
        self.assertEqual(len(field.player_food_levels), self.player_count)

        for food_level in field.player_food_levels:
            self.assertEqual(food_level, 0)

        field = None

        """make sure fields are created correcly"""
        x = 1
        y = 2
        is_nest = 1
        ant_count = 2
        home_pheromone_level = 3
        food_pheromone_level = 4
        player_food_levels = []

        for player_index in range(self.player_count):
            player_food_levels.append(5 + player_index)

        field_with_values = Field(x, y, is_nest, ant_count, home_pheromone_level, food_pheromone_level, player_food_levels)
        self.assertTrue(self.world.set(field_with_values))

        field = self.world.get(x, y)
        self.assertIsNotNone(field)
        self.assertIsInstance(field, Field)
        self.assertEqual(field.x, x)
        self.assertEqual(field.y, y)
        self.assertEqual(field.is_nest, is_nest)
        self.assertEqual(field.ant_count, ant_count)
        self.assertEqual(field.home_pheromone_level, home_pheromone_level)
        self.assertEqual(field.food_pheromone_level, food_pheromone_level)
        self.assertEqual(field.player_food_levels, player_food_levels)

    def test_set(self):
        x = 3
        y = 4
        is_nest = 1
        ant_count = 2
        home_pheromone_level = 3
        food_pheromone_level = 4
        player_food_levels = []

        for player_index in range(self.player_count):
            player_food_levels.append(5 + player_index)

        field = Field(x, y, is_nest, ant_count, home_pheromone_level, food_pheromone_level, player_food_levels)

        """make sure Field type gets checked"""
        self.assertFalse(self.world.set("string"))
        self.assertFalse(self.world.set(5))
        self.assertFalse(self.world.set({}))
        self.assertFalse(self.world.set([]))

        """make sure boundaries get checked"""
        self.world.reset()
        self.assertTrue(self.world.set(field))
        self.world.reset()

        field.x = -1
        self.assertFalse(self.world.set(field))

        field.x = x
        field.y = -1
        self.assertFalse(self.world.set(field))

        field.x = self.width
        field.y = y
        self.assertFalse(self.world.set(field))

        field.x = x
        field.y = self.height
        self.assertFalse(self.world.set(field))

        """make sure the player food levels get checked"""
        self.world.reset()
        field.y = y
        field.player_food_levels += [9]
        self.assertFalse(self.world.set(field))

        field.player_food_levels.pop()
        field.player_food_levels.pop()
        self.assertFalse(self.world.set(field))

        """reset player food levels"""
        player_food_levels = []

        for player_index in range(self.player_count):
            player_food_levels.append(5 + player_index)

        field.player_food_levels = player_food_levels

        """make sure the values of a Field get stored on the correct places"""
        self.world.reset()
        self.assertTrue(self.world.set(field))

        begin_index = (x + (y * self.width)) * self.ints_per_coordinate

        index_of_is_nest = begin_index + self.world.nest_index
        index_of_ant_count = begin_index + self.world.ant_count_index
        index_of_home_pheromone_level = begin_index + self.world.home_pheromone_index
        index_of_food_pheromone_level = begin_index + self.world.food_pheromone_index
        indexes_of_player_food_levels = []
        for player_food_index in self.world.player_food_indexes:
            indexes_of_player_food_levels.append(begin_index + player_food_index)

        self.assertEqual(self.world.data[index_of_is_nest], is_nest)
        self.assertEqual(self.world.data[index_of_ant_count], ant_count)
        self.assertEqual(self.world.data[index_of_home_pheromone_level], home_pheromone_level)
        self.assertEqual(self.world.data[index_of_food_pheromone_level], food_pheromone_level)

        for index in range(self.player_count):
            player_food_index = indexes_of_player_food_levels[index]
            player_food_level = player_food_levels[index]
            self.assertEqual(self.world.data[player_food_index], player_food_level)

        """make sure the coordinates are calculated correctly

        Example:
            width = 5, height = 5, ints_per_coordinate = 1
            x = 2, y = 2 -> begin_index = 12
            x = 4, y = 2 -> begin_index = 14
            x = 2, y = 4 -> begin_index = 24
        """
        self.world.reset()
        self.assertTrue(self.world.set(field))

        """Note: x and y are swapped to check if other indexes get used"""
        new_x = y
        new_y = x
        new_is_nest = 0
        new_ant_count = 100
        new_home_pheromone_level = 101
        new_food_pheromone_level = 102
        new_player_food_levels = []

        for player_index in range(self.player_count):
            new_player_food_levels.append(103 + player_index)

        field2 = Field(new_x, new_y, new_is_nest, new_ant_count, new_home_pheromone_level, new_food_pheromone_level, new_player_food_levels)
        self.assertTrue(self.world.set(field2))

        """check if the new data got written"""
        new_begin_index = (new_x + (new_y * self.width)) * self.ints_per_coordinate

        new_index_of_is_nest = new_begin_index + self.world.nest_index
        new_index_of_ant_count = new_begin_index + self.world.ant_count_index
        new_index_of_home_pheromone_level = new_begin_index + self.world.home_pheromone_index
        new_index_of_food_pheromone_level = new_begin_index + self.world.food_pheromone_index
        new_indexes_of_player_food_levels = []
        for player_food_index in self.world.player_food_indexes:
            new_indexes_of_player_food_levels.append(new_begin_index + player_food_index)

        self.assertEqual(self.world.data[new_index_of_is_nest], new_is_nest)
        self.assertEqual(self.world.data[new_index_of_ant_count], new_ant_count)
        self.assertEqual(self.world.data[new_index_of_home_pheromone_level], new_home_pheromone_level)
        self.assertEqual(self.world.data[new_index_of_food_pheromone_level], new_food_pheromone_level)

        for index in range(self.player_count):
            player_food_index = new_indexes_of_player_food_levels[index]
            player_food_level = new_player_food_levels[index]
            self.assertEqual(self.world.data[player_food_index], player_food_level)

        """check if the indexes are indeed different"""
        self.assertNotEqual(begin_index, new_begin_index)
        self.assertNotEqual(index_of_is_nest, new_index_of_is_nest)
        self.assertNotEqual(index_of_ant_count, new_index_of_ant_count)
        self.assertNotEqual(index_of_home_pheromone_level, new_index_of_home_pheromone_level)
        self.assertNotEqual(index_of_food_pheromone_level, new_index_of_food_pheromone_level)

        for index in range(self.player_count):
            self.assertNotEqual(indexes_of_player_food_levels[index], new_indexes_of_player_food_levels[index])

    def test_reset(self):
        for index in range(self.array_size):
            self.world.data[index] = 99

        self.assertEqual(self.world.data[0], 99)
        self.assertEqual(self.world.data[self.width], 99)
        self.assertEqual(self.world.data[self.array_size - 1], 99)

        self.world.reset()

        self.assertEqual(self.world.data[0], 0)
        self.assertEqual(self.world.data[self.width], 0)
        self.assertEqual(self.world.data[self.array_size - 1], 0)

    def suite():
        tests = ['test_init', 'test_get', 'test_set', 'test_reset']
        return unittest.TestSuite(map(TestWorld, tests))
