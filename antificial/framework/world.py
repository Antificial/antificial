#! /usr/bin/env python

from array import array
import util

#from util import *

class Field:
    def __init__(self, x, y, is_nest, ant_count, home_pheromone_level, food_pheromone_level, player_food_levels):
        self.x = x
        self.y = y
        self.is_nest = is_nest
        self.ant_count = ant_count
        self.home_pheromone_level = home_pheromone_level
        self.food_pheromone_level = food_pheromone_level
        self.player_food_levels = player_food_levels

    def iprint(self):
        util.iprint("[Field] x:{self.x} y:{self.y} is_nest:{self.is_nest} ant_count:{self.ant_count} home_pheromone_level:{self.home_pheromone_level} food_pheromone_level:{self.food_pheromone_level} player_food_levels:{self.player_food_levels}")


class World:
    def __init__(self, width, height, player_count):
        self.width = width
        self.height = height
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

        array_size = self.width * self.height * self.ints_per_coordinate
        self.data = array('i', range(array_size))

        for index in range(array_size):
            self.data[index] = 0

    def get(self, x, y):
        if (x >= self.width):
            return None

        if (y >= self.width):
            return None

        begin_index = x * y * self.ints_per_coordinate

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

        if (field.x >= self.width):
            return False

        if (field.y >= self.width):
            return False

        if (len(field.player_food_levels) != self.player_count):
            return False

        begin_index = field.x * field.y * self.ints_per_coordinate

        self.data[begin_index + self.nest_index] = field.is_nest
        self.data[begin_index + self.ant_count_index] = field.ant_count
        self.data[begin_index + self.home_pheromone_index] = field.home_pheromone_level
        self.data[begin_index + self.food_pheromone_index] = field.food_pheromone_level
        
        for player_no in range(self.player_count):
            food_index = self.player_food_indexes[player_no]
            self.data[begin_index + food_index] = field.player_food_levels[player_no]

        return True

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
                field.iprint()






# TODO: create/initialize empty coordinate system
# TODO: get_neigbours
# TODO: reset_pheromones
# TODO: get content/data/?
# TODO: set content/data/?