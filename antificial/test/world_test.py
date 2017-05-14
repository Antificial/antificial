#! /usr/bin/env python

import unittest
from framework import World, Field, PheromoneType

class TestWorld(unittest.TestCase):

    def setUp(self):
        """minimum dimension in this test: 5 * 5 - the rest is dynamic"""
        self.width = 5
        self.height = 5
        self.player_count = 3
        self.ints_per_coordinate = 4 + self.player_count
        self.array_size = self.width * self.height * self.ints_per_coordinate
        self.world = World([self.width, self.height], self.player_count)
        self.world.reset()

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
        for index in ([self.world.ant_count_index, self.world.home_pheromone_index, self.world.food_pheromone_index] + list(self.world.player_food_indexes)):
            self.assertNotEqual(index, self.world.nest_index)

        for index in ([self.world.nest_index, self.world.home_pheromone_index, self.world.food_pheromone_index] + list(self.world.player_food_indexes)):
            self.assertNotEqual(index, self.world.ant_count_index)

        for index in ([self.world.nest_index, self.world.ant_count_index, self.world.food_pheromone_index] + list(self.world.player_food_indexes)):
            self.assertNotEqual(index, self.world.home_pheromone_index)

        for index in ([self.world.nest_index, self.world.ant_count_index, self.world.home_pheromone_index] + list(self.world.player_food_indexes)):
            self.assertNotEqual(index, self.world.food_pheromone_index)

        """make sure every player food index is unique (w/o other player indexes)"""
        for player_food_index in self.world.player_food_indexes:
            for index in [self.world.nest_index, self.world.ant_count_index, self.world.home_pheromone_index, self.world.food_pheromone_index]:
                self.assertNotEqual(index, player_food_index)

        """make sure every player food index is unique (comparing the player food indexes)"""
        player_food_indexes_copy = list(self.world.player_food_indexes) + []
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

        begin_index = self.world.get_field_begin_index(x, y)

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
        self.assertEqual(self.world.data[0], 0)
        self.assertEqual(self.world.data[self.width], 0)
        self.assertEqual(self.world.data[self.array_size - 1], 0)
        
        for index in range(self.array_size):
            self.world.data[index] = 99

        self.assertEqual(self.world.data[0], 99)
        self.assertEqual(self.world.data[self.width], 99)
        self.assertEqual(self.world.data[self.array_size - 1], 99)

        self.world.reset()

        self.assertEqual(self.world.data[0], 0)
        self.assertEqual(self.world.data[self.width], 0)
        self.assertEqual(self.world.data[self.array_size - 1], 0)

    def test_get_neighbours(self):
        """make sure the coordinate and smell range get checked"""
        self.assertIsNone(self.world.get_neighbours(-1, 0, 1))
        self.assertIsNone(self.world.get_neighbours(0, -1, 1))
        self.assertIsNone(self.world.get_neighbours(0, 0, -1))
        self.assertIsNone(self.world.get_neighbours(self.width, 0, 1))
        self.assertIsNone(self.world.get_neighbours(0, self.height, 1))

        field_count = 0
        for begin_index in range(0, (self.array_size - self.world.ints_per_coordinate), self.world.ints_per_coordinate):
            for relative_index in range(self.world.ints_per_coordinate):
                self.world.data[begin_index + relative_index] = field_count
            field_count += 1

        x = 2
        y = 2

        top_left_field = self.world.get(x - 1, y - 1)
        top_field = self.world.get(x, y - 1)
        top_right_field = self.world.get(x + 1, y - 1)

        left_field = self.world.get(x - 1, y)
        center_field = self.world.get(x, y)
        right_field = self.world.get(x + 1, y)

        bottom_left_field = self.world.get(x - 1, y + 1)
        bottom_field = self.world.get(x, y + 1)
        bottom_right_field = self.world.get(x + 1, y + 1)

        """check the fields are the correct ones"""
        self.assertEqual(top_left_field.ant_count, (self.width * (y - 1)) + (x - 1))
        self.assertEqual(top_field.ant_count, (self.width * (y - 1)) + x)
        self.assertEqual(top_right_field.ant_count, (self.width * (y - 1)) + (x + 1))

        self.assertEqual(left_field.ant_count, (self.width * y) + (x - 1))
        self.assertEqual(center_field.ant_count, (self.width * y) + x)
        self.assertEqual(right_field.ant_count, (self.width * y) + (x + 1))

        self.assertEqual(bottom_left_field.ant_count, (self.width * (y + 1)) + (x - 1))
        self.assertEqual(bottom_field.ant_count, (self.width * (y + 1)) + x)
        self.assertEqual(bottom_right_field.ant_count, (self.width * (y + 1)) + (x + 1))

        """check neighbours with smellrange=1"""
        neighbours = self.world.get_neighbours(x, y)
        self.assertIsNotNone(neighbours)
        self.assertEqual(len(neighbours), 3)
        self.assertEqual(len(neighbours[0]), 3)
        self.assertEqual(len(neighbours[1]), 3)
        self.assertEqual(len(neighbours[2]), 3)

        self.assertEqual(neighbours[0][0], top_left_field)
        self.assertEqual(neighbours[1][0], top_field)
        self.assertEqual(neighbours[2][0], top_right_field)

        self.assertEqual(neighbours[0][1], left_field)
        self.assertEqual(neighbours[1][1], center_field)
        self.assertEqual(neighbours[2][1], right_field)

        self.assertEqual(neighbours[0][2], bottom_left_field)
        self.assertEqual(neighbours[1][2], bottom_field)
        self.assertEqual(neighbours[2][2], bottom_right_field)

        """check neighbours with smell range=2"""
        neighbours = self.world.get_neighbours(x, y, 2)
        self.assertIsNotNone(neighbours)
        self.assertEqual(len(neighbours), 5)
        self.assertEqual(len(neighbours[0]), 5)
        self.assertEqual(len(neighbours[1]), 5)
        self.assertEqual(len(neighbours[2]), 5)
        self.assertEqual(len(neighbours[3]), 5)
        self.assertEqual(len(neighbours[4]), 5)

        self.assertEqual(neighbours[0][0], self.world.get(x - 2, y - 2))
        self.assertEqual(neighbours[1][0], self.world.get(x - 1, y - 2))
        self.assertEqual(neighbours[2][0], self.world.get(x    , y - 2))
        self.assertEqual(neighbours[3][0], self.world.get(x + 1, y - 2))
        self.assertEqual(neighbours[4][0], self.world.get(x + 2, y - 2))

        self.assertEqual(neighbours[0][1], self.world.get(x - 2, y - 1))
        self.assertEqual(neighbours[1][1], self.world.get(x - 1, y - 1))
        self.assertEqual(neighbours[2][1], self.world.get(x    , y - 1))
        self.assertEqual(neighbours[3][1], self.world.get(x + 1, y - 1))
        self.assertEqual(neighbours[4][1], self.world.get(x + 2, y - 1))

        self.assertEqual(neighbours[0][2], self.world.get(x - 2, y    ))
        self.assertEqual(neighbours[1][2], self.world.get(x - 1, y    ))
        self.assertEqual(neighbours[2][2], self.world.get(x    , y    ))
        self.assertEqual(neighbours[3][2], self.world.get(x + 1, y    ))
        self.assertEqual(neighbours[4][2], self.world.get(x + 2, y    ))

        self.assertEqual(neighbours[0][3], self.world.get(x - 2, y + 1))
        self.assertEqual(neighbours[1][3], self.world.get(x - 1, y + 1))
        self.assertEqual(neighbours[2][3], self.world.get(x    , y + 1))
        self.assertEqual(neighbours[3][3], self.world.get(x + 1, y + 1))
        self.assertEqual(neighbours[4][3], self.world.get(x + 2, y + 1))

        self.assertEqual(neighbours[0][4], self.world.get(x - 2, y + 2))
        self.assertEqual(neighbours[1][4], self.world.get(x - 1, y + 2))
        self.assertEqual(neighbours[2][4], self.world.get(x    , y + 2))
        self.assertEqual(neighbours[3][4], self.world.get(x + 1, y + 2))
        self.assertEqual(neighbours[4][4], self.world.get(x + 2, y + 2))

        """check endge case top left corner: x=0 y=0 smellrange=1"""
        x = 0
        y = 0
        neighbours = self.world.get_neighbours(x, y)
        self.assertIsNotNone(neighbours)
        self.assertEqual(len(neighbours), 2)
        self.assertEqual(len(neighbours[0]), 2)
        self.assertEqual(len(neighbours[1]), 2)

        self.assertEqual(neighbours[0][0], self.world.get(x    , y    ))
        self.assertEqual(neighbours[1][0], self.world.get(x + 1, y    ))

        self.assertEqual(neighbours[0][1], self.world.get(x    , y + 1))
        self.assertEqual(neighbours[1][1], self.world.get(x + 1, y + 1))

        """check endge case bottom right corner: x=width-1 y=height-1 smellrange=1"""
        x = self.width - 1
        y = self.height - 1
        neighbours = self.world.get_neighbours(x, y)
        self.assertIsNotNone(neighbours)
        self.assertEqual(len(neighbours), 2)
        self.assertEqual(len(neighbours[0]), 2)
        self.assertEqual(len(neighbours[1]), 2)

        self.assertEqual(neighbours[0][0], self.world.get(x - 1, y - 1))
        self.assertEqual(neighbours[1][0], self.world.get(x    , y - 1))

        self.assertEqual(neighbours[0][1], self.world.get(x - 1, y    ))
        self.assertEqual(neighbours[1][1], self.world.get(x    , y    ))

        """check endge case left border: x=0 y=2 smellrange=1"""
        x = 0
        y = 2
        neighbours = self.world.get_neighbours(x, y)
        self.assertIsNotNone(neighbours)
        self.assertEqual(len(neighbours), 2)
        self.assertEqual(len(neighbours[0]), 3)
        self.assertEqual(len(neighbours[1]), 3)

        self.assertEqual(neighbours[0][0], self.world.get(x    , y - 1))
        self.assertEqual(neighbours[1][0], self.world.get(x + 1, y - 1))

        self.assertEqual(neighbours[0][1], self.world.get(x    , y    ))
        self.assertEqual(neighbours[1][1], self.world.get(x + 1, y    ))

        self.assertEqual(neighbours[0][2], self.world.get(x    , y + 1))
        self.assertEqual(neighbours[1][2], self.world.get(x + 1, y + 1))

        """check endge case top border: x=2 y=0 smellrange=1"""
        x = 2
        y = 0
        neighbours = self.world.get_neighbours(x, y)
        self.assertIsNotNone(neighbours)
        self.assertEqual(len(neighbours), 3)
        self.assertEqual(len(neighbours[0]), 2)
        self.assertEqual(len(neighbours[1]), 2)
        self.assertEqual(len(neighbours[2]), 2)

        self.assertEqual(neighbours[0][0], self.world.get(x - 1, y    ))
        self.assertEqual(neighbours[1][0], self.world.get(x    , y    ))
        self.assertEqual(neighbours[2][0], self.world.get(x + 1, y    ))

        self.assertEqual(neighbours[0][1], self.world.get(x - 1, y + 1))
        self.assertEqual(neighbours[1][1], self.world.get(x    , y + 1))
        self.assertEqual(neighbours[2][1], self.world.get(x + 1, y + 1))

    def test_deposit_pheromone(self):
        """make sure the coordinate gets checked"""
        self.assertFalse(self.world.deposit_pheromone(-1, 1, PheromoneType.HOME, 1))
        self.assertFalse(self.world.deposit_pheromone(1, -1, PheromoneType.HOME, 1))
        self.assertFalse(self.world.deposit_pheromone(self.width, 1, PheromoneType.HOME, 1))
        self.assertFalse(self.world.deposit_pheromone(1, self.height, PheromoneType.HOME, 1))

        """make sure the pheromone type and strength get checked"""
        self.assertFalse(self.world.deposit_pheromone(1, 1, PheromoneType.HOME, -1))
        self.assertFalse(self.world.deposit_pheromone(1, 1, 999, 1))

        x = 2
        y = 2

        self.assertTrue(self.world.deposit_pheromone(x, y, PheromoneType.HOME, 1))

        field = self.world.get(x, y)
        self.assertEqual(field.home_pheromone_level, 1)
        self.assertEqual(field.food_pheromone_level, 0)

        self.assertTrue(self.world.deposit_pheromone(x, y, PheromoneType.HOME, 5))
        self.assertTrue(self.world.deposit_pheromone(x, y, PheromoneType.FOOD, 3))

        field = self.world.get(x, y)
        self.assertEqual(field.home_pheromone_level, 6)
        self.assertEqual(field.food_pheromone_level, 3)

    def test_decay_pheromones(self):
        """make sure decay gets checked"""
        self.assertFalse(self.world.decay_pheromones(-1, 1))
        self.assertFalse(self.world.decay_pheromones(1, -1))

        """make sure the pheromone levels don't drop below zero"""
        self.world.reset()
        self.assertTrue(self.world.decay_pheromones(100, 100))

        for x in range(self.width):
            for y in range(self.height):
                field = self.world.get(x, y)
                self.assertEqual(field.home_pheromone_level, 0)
                self.assertEqual(field.food_pheromone_level, 0)

                """after checking prepare them for the next check"""
                field.home_pheromone_level = 10
                field.food_pheromone_level = 20
                if not self.world.set(field):
                    self.fail("could not set field with modified pheromone levels")

        """make sure the different decays get applied properly"""
        self.world.decay_pheromones(5, 1)

        for x in range(self.width):
            for y in range(self.height):
                field = self.world.get(x, y)
                self.assertEqual(field.home_pheromone_level, 5)
                self.assertEqual(field.food_pheromone_level, 19)

        self.world.decay_pheromones(1, 5)

        for x in range(self.width):
            for y in range(self.height):
                field = self.world.get(x, y)
                self.assertEqual(field.home_pheromone_level, 4)
                self.assertEqual(field.food_pheromone_level, 14)

    def test_move_ant(self):
        """make sure coordinates get checked"""
        self.assertFalse(self.world.move_ant(-1, 0, 0, 0))
        self.assertFalse(self.world.move_ant(0, -1, 0, 0))
        self.assertFalse(self.world.move_ant(0, 0, -1, 0))
        self.assertFalse(self.world.move_ant(0, 0, 0, -1))

        self.assertFalse(self.world.move_ant(self.width, 0, 0, 0))
        self.assertFalse(self.world.move_ant(0, self.height, 0, 0))
        self.assertFalse(self.world.move_ant(0, 0, self.width, 0))
        self.assertFalse(self.world.move_ant(0, 0, 0, self.height))

        """make sure the ant count gets decreased in the source field and increased in the destionatin fiel"""
        source_x = 0
        source_y = 0
        destination_x = 4
        destination_y = 4

        source_field = self.world.get(source_x, source_y)
        destination_field = self.world.get(destination_x, destination_y)

        source_field.ant_count = 1
        self.world.set(source_field)

        destination_field.ant_count = 0
        self.world.set(destination_field)

        self.assertTrue(self.world.move_ant(source_x, source_y, destination_x, destination_y))
        self.assertEqual(self.world.get(source_x, source_y).ant_count, 0)
        self.assertEqual(self.world.get(destination_x, destination_y).ant_count, 1)
        
        """retry to make sure the source ant count does not get below zero"""
        self.assertTrue(self.world.move_ant(source_x, source_y, destination_x, destination_y))
        self.assertEqual(self.world.get(source_x, source_y).ant_count, 0)
        self.assertEqual(self.world.get(destination_x, destination_y).ant_count, 2)

    def test_get_field_begin_index(self):
        self.assertIsNone(self.world.get_field_begin_index(-1, 0))
        self.assertIsNone(self.world.get_field_begin_index(0, -1))

        self.assertEqual(self.world.get_field_begin_index(0, 0), 0)
        self.assertEqual(self.world.get_field_begin_index(1, 0), self.ints_per_coordinate)
        self.assertEqual(self.world.get_field_begin_index(2, 0), self.ints_per_coordinate * 2)

        x = self.width - 1
        y = self.height - 1
        expected_index = (x + (y * self.width)) * self.ints_per_coordinate
        self.assertEqual(self.world.get_field_begin_index(x, y), expected_index)

    def test_is_valid_coordinate(self):
        self.assertFalse(self.world.is_valid_coordinate(-1, 0))
        self.assertFalse(self.world.is_valid_coordinate(0, -1))
        self.assertFalse(self.world.is_valid_coordinate(0, self.height))
        self.assertFalse(self.world.is_valid_coordinate(0, self.height * 100))
        self.assertFalse(self.world.is_valid_coordinate(self.width, 0))
        self.assertFalse(self.world.is_valid_coordinate(self.width * 100, 0))

        self.assertTrue(self.world.is_valid_coordinate(0, 0))
        self.assertTrue(self.world.is_valid_coordinate(1, 1))
        self.assertTrue(self.world.is_valid_coordinate(self.width - 1, self.height - 1))

    def suite():
        return unittest.TestLoader().loadTestsFromTestCase(TestWorld)
