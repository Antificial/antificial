#! /usr/bin/env python

from multiprocessing import Array
import util
from random import randint
from enum import Enum
from framework import PheromoneType

class Field:
    def __init__(self, x, y, is_nest, ant_count, home_pheromone_level, food_pheromone_level, player_food_levels):
        self.x = x
        self.y = y
        self.is_nest = is_nest
        self.ant_count = ant_count
        self.home_pheromone_level = home_pheromone_level
        self.food_pheromone_level = food_pheromone_level
        self.player_food_levels = player_food_levels

    def __str__(self):
        output = "["
        if self.x < 10:
            output += "x:  " + str(self.x)
        elif self.x < 100:
            output += "x: " + str(self.x)
        else:
            output += "x:" + str(self.x)

        output += " "
        if self.y < 10:
            output += "y:  " + str(self.y)
        elif self.y < 100:
            output += "y: " + str(self.y)
        else:
            output += "y:" + str(self.y)

        if self.is_nest > 0:
            output += " N"

        if self.ant_count > 0:
            output += " A:" + str(self.ant_count)

        if self.home_pheromone_level > 0:
            output += " H:" + str(self.home_pheromone_level)

        if self.food_pheromone_level > 0:
            output += " F:" + str(self.food_pheromone_level)

        for index in range(len(self.player_food_levels)):
            if (self.player_food_levels[index] > 0):
                output += " P" + str(index) + ":" + str(self.player_food_levels[index])

        output += "]"
        return output

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if other is None:
            return False

        if not isinstance(other, Field):
            return False

        if self.x != other.x or self.y != other.y:
            return False

        if self.is_nest != other.is_nest:
            return False

        if self.ant_count != other.ant_count:
            return False

        if self.home_pheromone_level != other.home_pheromone_level:
            return False

        if self.food_pheromone_level != other.food_pheromone_level:
            return False

        if len(self.player_food_levels) != len(other.player_food_levels):
            return False

        for index in range(len(self.player_food_levels)):
            if self.player_food_levels[index] != other.player_food_levels[index]:
                return False

        return True

class World:
    def __init__(self, grid_resolution, player_count):
        self.width = grid_resolution[0]
        self.height = grid_resolution[1]
        self.player_count = player_count

        # keep track of the food coordinates (x, y, player_no) to make the updates easier
        self.food_coordinates = []

        """Amount of integers per coordinate:
            1 to flag the nest (values: 0 - 1)
            1 for the ant count (values: 0 - max int)
            1 for home pheromone level (values: 0 - 100)
            1 for food pheromone level (values: 0 - 100)
            1 food flag / level per player (values: 0 - 1)
        """
        self.ints_per_coordinate = 4 + self.player_count

        # index (position) of integers
        self.nest_index = 0
        self.ant_count_index = 1
        self.home_pheromone_index = 2
        self.food_pheromone_index = 3
        self.player_food_indexes = range(4, 4 + self.player_count)

        self.array_size = self.width * self.height * self.ints_per_coordinate
        self.data = Array('i', [0 for i in range(self.array_size)])

    def get(self, x, y):
        if not self.is_valid_coordinate(x, y):
            return None

        begin_index = self.get_field_begin_index(x, y)

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

        if not self.is_valid_coordinate(field.x, field.y):
            return False

        if (len(field.player_food_levels) != self.player_count):
            return False

        begin_index = self.get_field_begin_index(field.x, field.y)

        self.data[begin_index + self.nest_index] = field.is_nest
        self.data[begin_index + self.ant_count_index] = field.ant_count
        self.data[begin_index + self.home_pheromone_index] = field.home_pheromone_level
        self.data[begin_index + self.food_pheromone_index] = field.food_pheromone_level

        for player_no in range(self.player_count):
            food_index = self.player_food_indexes[player_no]
            self.data[begin_index + food_index] = field.player_food_levels[player_no]
            if field.player_food_levels[player_no] > 0:
                self.food_coordinates.append([field.x, field.y, player_no])

        return True

    def reset(self):
        self.food_coordinates = []
        for index in range(self.array_size):
            self.data[index] = 0

    """Creates a matrix of fields depending on the smell_range.

    Examples:
        smell_range = 1 -> result = [
                                        [None, None, None],
                                        [None, None, None],
                                        [None, None, None]
                                    ]
        smell_range = 2 -> result = [
                                        [None, None, None, None, None],
                                        [None, None, None, None, None],
                                        [None, None, None, None, None],
                                        [None, None, None, None, None],
                                        [None, None, None, None, None]
                                    ]
        smell_range = 3 -> result = [
                                        [None, None, None, None, None, None, None],
                                        [None, None, None, None, None, None, None],
                                        [None, None, None, None, None, None, None],
                                        [None, None, None, None, None, None, None],
                                        [None, None, None, None, None, None, None],
                                        [None, None, None, None, None, None, None],
                                        [None, None, None, None, None, None, None]
                                    ]
    """
    def get_neighbours(self, x, y, smell_range = 1):
        if not self.is_valid_coordinate(x, y):
            return None

        if smell_range < 1:
            return None

        min_x = x - smell_range
        min_y = y - smell_range
        max_x = x + smell_range
        max_y = y + smell_range

        if min_x < 0:
            min_x = 0

        if min_y < 0:
            min_y = 0

        if max_x >= self.width:
            max_x = self.width - 1

        if max_y >= self.height:
            max_y = self.height - 1

        result = []
        for current_x in range(min_x, max_x + 1):
            result.append([])
            for current_y in range(min_y, max_y + 1):
                result[current_x - min_x].append(self.get(current_x, current_y))

        return result

    def deposit_pheromone(self, x, y, pheromone_type, pheromone_strength):
        if not self.is_valid_coordinate(x, y):
            return False

        if pheromone_strength < 0:
            return False

        begin_index = self.get_field_begin_index(x, y)

        if pheromone_type == PheromoneType.HOME:
            current_level = self.data[begin_index + self.home_pheromone_index]
            self.data[begin_index + self.home_pheromone_index] = current_level + pheromone_strength
        elif pheromone_type == PheromoneType.FOOD:
            current_level = self.data[begin_index + self.food_pheromone_index]
            self.data[begin_index + self.food_pheromone_index] = current_level + pheromone_strength
        else:
            return False

        return True

    def decay_pheromones(self, home_pheromone_decay_rate, food_pheromone_decay_rate):
        if home_pheromone_decay_rate < 0:
            return False

        if food_pheromone_decay_rate < 0:
            return False

        for x in range(self.width):
            for y in range(self.height):
                begin_index = self.get_field_begin_index(x, y)

                # update home pheromone level
                current_level = self.data[begin_index + self.home_pheromone_index]
                if current_level > 0:
                    updated_level = current_level - home_pheromone_decay_rate
                    if updated_level < 0:
                        updated_level = 0

                    self.data[begin_index + self.home_pheromone_index] = updated_level

                # update food pheromone level
                current_level = self.data[begin_index + self.food_pheromone_index]
                if current_level > 0:
                    updated_level = current_level - food_pheromone_decay_rate
                    if updated_level < 0:
                        updated_level = 0

                    self.data[begin_index + self.food_pheromone_index] = updated_level

        return True

    # TOOD: replace x and y by Ant / Field objects?
    def move_ant(self, source_x, source_y, destination_x, destination_y):
        if not self.is_valid_coordinate(source_x, source_y):
            return False

        if not self.is_valid_coordinate(destination_x, destination_y):
            return False

        if source_x == destination_x and source_y == destination_y:
            return True

        # decrease ant count in source field
        source_begin_index = self.get_field_begin_index(source_x, source_y)
        ant_count = self.data[source_begin_index + self.ant_count_index]
        if ant_count > 0:
            self.data[source_begin_index + self.ant_count_index] = ant_count - 1

        # increase ant count in destination field
        destination_begin_index = self.get_field_begin_index(destination_x, destination_y)
        ant_count = self.data[destination_begin_index + self.ant_count_index]
        self.data[destination_begin_index + self.ant_count_index] = ant_count + 1

        return True

    def update_food(self, new_food_coordinates):
        print(new_food_coordinates)
        # remove old food levels
        for (x, y, player_no) in self.food_coordinates:
            if not self.is_valid_coordinate(x, y):
                continue

            begin_index = self.get_field_begin_index(x, y)
            food_index = self.player_food_indexes[player_no]
            self.data[begin_index + food_index] = 0

        # set new food levels
        self.food_coordinates = new_food_coordinates

        for (x, y, player_no) in new_food_coordinates:
            if not self.is_valid_coordinate(x, y):
                continue

            begin_index = self.get_field_begin_index(x, y)
            food_index = self.player_food_indexes[player_no]
            self.data[begin_index + food_index] = 100

    def get_field_begin_index(self, x, y):
        if not self.is_valid_coordinate(x, y):
            return None

        return (x + (y * self.width)) * self.ints_per_coordinate

    def is_valid_coordinate(self, x, y):
        if x < 0 or x >= self.width:
            return False

        if y < 0 or y >= self.height:
            return False

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

        output = ""
        
        for x in range(self.width):
            for y in range(self.height):
                field = self.get(x, y)
                output += str(field)
            output += "\n"

        util.iprint(output)