#! /usr/bin/env python

from multiprocessing import Array
import util
from random import randint

class Field:
    def __init__(self, x, y, is_nest, ant_count, home_pheromone_level, food_pheromone_level, player_food_levels):
        self.x = x
        self.y = y
        self.is_nest = is_nest
        self.ant_count = ant_count
        self.home_pheromone_level = home_pheromone_level
        self.food_pheromone_level = food_pheromone_level
        self.player_food_levels = player_food_levels

    def print_small(self):
        output = "[x:" + str(self.x) + " y:" + str(self.y)
        if (self.is_nest > 0):
            output += " N"

        if (self.ant_count > 0):
            output += " A:" + str(self.ant_count)

        if (self.home_pheromone_level > 0):
            output += " H:" + str(self.home_pheromone_level)

        if (self.food_pheromone_level > 0):
            output += " F:" + str(self.food_pheromone_level)

        for index in range(len(self.player_food_levels)):
            if (self.player_food_levels[index] > 0):
                output += " P" + str(index) + ":" + str(self.player_food_levels[index])

        output += "]"
        util.iprint(output)

    def iprint(self):
        util.iprint("[Field] x:{self.x} y:{self.y} is_nest:{self.is_nest} ant_count:{self.ant_count} home_pheromone_level:{self.home_pheromone_level} food_pheromone_level:{self.food_pheromone_level} player_food_levels:{self.player_food_levels}")


class World:
    def __init__(self, grid_resolution, player_count):
        self.width = grid_resolution[0]
        self.height = grid_resolution[1]
        self.player_count = player_count

        """Amount of integers per coordinate:
            1 to flag the nest (values: 0 - 1)
            1 for the ant count (values: 0 - max int)
            1 for home pheromone level (values: 0 - 100)
            1 for food pheromone level (values: 0 - 100)
            1 food flag / level per player (values: 0 - 1)
        """
        self.ints_per_coordinate = 4 + self.player_count

        """Index (position) of integers"""
        self.nest_index = 0
        self.ant_count_index = 1
        self.home_pheromone_index = 2
        self.food_pheromone_index = 3
        self.player_food_indexes = range(4, 4 + self.player_count)

        self.array_size = self.width * self.height * self.ints_per_coordinate
        self.data = Array('i', [randint(1,256) for i in range(self.array_size)])

    def get(self, x, y):
        if (x >= self.width or x < 0):
            return None

        if (y >= self.height or y < 0):
            return None

        begin_index = (x + (y * self.width)) * self.ints_per_coordinate

        is_nest = self.data[begin_index + self.nest_index]
        ant_count = self.data[begin_index + self.ant_count_index]
        home_pheromone_level = self.data[begin_index + self.home_pheromone_index]
        food_pheromone_level = self.data[begin_index + self.food_pheromone_index]

        player_food_levels = []
        for food_index in self.player_food_indexes:
            player_food_levels.append(self.data[begin_index + food_index])

        field = Field(x, y, is_nest, ant_count, home_pheromone_level, food_pheromone_level, player_food_levels)
        return field

    def set(self, field):
        if (not isinstance(field, Field)):
            return False

        if (field.x >= self.width or field.x < 0):
            return False

        if (field.y >= self.height or field.y < 0):
            return False

        if (len(field.player_food_levels) != self.player_count):
            return False

        begin_index = (field.x + (field.y * self.width)) * self.ints_per_coordinate

        self.data[begin_index + self.nest_index] = field.is_nest
        self.data[begin_index + self.ant_count_index] = field.ant_count
        self.data[begin_index + self.home_pheromone_index] = field.home_pheromone_level
        self.data[begin_index + self.food_pheromone_index] = field.food_pheromone_level
        
        for player_no in range(self.player_count):
            food_index = self.player_food_indexes[player_no]
            self.data[begin_index + food_index] = field.player_food_levels[player_no]

        return True

    def reset(self):
        for index in range(self.array_size):
            self.data[index] = 0

    def iprint(self):

        util.iprint("[World] width: {self.width}")
        util.iprint("[World] height: {self.height}")
        util.iprint("[World] player_count: {self.player_count}")
        util.iprint("[World] ints_per_coordinate: {self.ints_per_coordinate}")

        util.iprint("[World] nest_index: {self.nest_index}")
        util.iprint("[World] ant_count_index: {self.ant_count_index}")
        util.iprint("[World] home_pheromone_index: {self.home_pheromone_index}")
        util.iprint("[World] food_pheromone_index: {self.food_pheromone_index}")
        util.iprint("[World] player_food_indexes: {self.player_food_indexes}")

        util.iprint("[World] data:")

        for x in range(self.width):
            for y in range(self.height):
                field = self.get(x, y)
                field.print_small()


# TODO: get_neigbours(self, x, y) / get_neigbours(self, field)
