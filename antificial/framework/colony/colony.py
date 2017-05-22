from enum import IntEnum
import abc
import operator
from random import getrandbits, randint

class Orientation(IntEnum):
    NORTH = 0
    NORTHEAST = 1
    EAST = 2
    SOUTHEAST = 3
    SOUTH = 4
    SOUTHWEST = 5
    WEST = 6
    NORTHWEST = 7

    @staticmethod
    def right(orientation):
        orientation = Orientation(orientation)

        if orientation + 1 > 7:
            return Orientation(0)
        else:
            return Orientation(orientation + 1)

    @staticmethod
    def left(orientation):
        orientation = Orientation(orientation)

        if orientation - 1 < 0:
            return Orientation(7)
        else:
            return Orientation(orientation - 1)

class PheromoneType(IntEnum):
    HOME = 0
    FOOD = 1

class GameObject(abc.ABC):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @abc.abstractmethod
    def update():
        print('GameObject.update()')

class Colony(GameObject):
    def __init__(self, world, home, antcount=100):
        self.world = WorldFacade(world)
        self.home = Home(home[0], home[1])
        self.antcount = antcount
        self.ants = []
        self.observers = []
        self.gamerules = None

        for i in range(antcount):
            ant = Ant(self)
            state = SearchFoodState(ant)
            ant.init_state(state)
            self.ants.append(ant)

    def init_gamerules(self, gamerules):
        self.gamerules = gamerules

    def register(self, observer):
        if not observer in self.observers:
            self.observers.append(observer)

    def unregister(self, observer):
        if observer in self.observers:
            self.observers.remove(observer)

    def unregister_all(self):
        if self.observers:
            del self.observers[:]

    def update_observers(self, *args, **kwargs):
        for observer in self.observers:
            observer.update(*args, **kwargs)

    def update(self):
        for ant in self.ants:
            ant.update()

class Home(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        # write into gameworld

    def update():
        print('Home.update()')

class Food(GameObject):
    def __init__(self, x, y, player, level = 100):
        super().__init__(x, y)
        self.player = player
        self.level = level

    def update(self):
        pass

    def __str__(self):
        output = "{"
        output += "x: " + str(self.x)
        output += ", y: " + str(self.y)
        output += ", player: " + str(self.player)
        output += ", level: " + str(self.level) 
        output += "}"
        return output

class Ant(GameObject):
    def __init__(self, colony):
        super().__init__(colony.home.x, colony.home.y)
        self.colony = colony
        self.orientation = Orientation.SOUTH
        self.state = None
        self.player = None
        # write into gameworld

    def init_state(self, state):
        self.state = state

    def update(self):
        self.state.handle()

class AntState(abc.ABC):
    def __init__(self, ant):
        self.ant = ant

    @abc.abstractmethod
    def handle(self):
        print('AntState.update()')

class SearchFoodState(AntState):
    def __init__(self, ant):
        super().__init__(ant)

    def handle(self):
        # get world
        world = self.ant.colony.world

        # strategy 1: if ant is on food field, eat food
        food = world.get_food(self.ant.x, self.ant.y)
        if food != None:
            self.ant.food = food
            self.ant.state = SearchHomeState(self.ant)
            return

        # get a map of the ant's neighbours
        neighbours = world.get_neighbours(self.ant.x, self.ant.y)

        # strategy 2: if ant is close to food field, go there
        best_food = None
        for row in neighbours:
            for field in row:
                if field is None:
                    continue

                food = world.get_food(field.x, field.y)
                if food != None:
                    if best_food != None:
                        if food.level > best_food.level:
                            best_food = food
                    else:
                        best_food = food

        if best_food != None:
            self.move(self.ant.x, self.ant.y, best_food.x, best_food.y)
            self.ant.x = best_food.x
            self.ant.y = best_food.y
            return

        # get the ant's neighbours relative to its orientation
        neighbours_by_orientation = world.get_neighbours_by_orientation(self.ant.x, self.ant.y, self.ant.orientation)

        # exclude borders and obstacles
        neighbours_by_orientation = [x for x in neighbours_by_orientation if x != None]

        # strategy 3: if ant is close to food pheromone field, go there
        best_pheromone = None
        for field in neighbours_by_orientation:
            if field.food_pheromone_level > 0:
                if best_pheromone == None:
                    best_pheromone = field
                else:
                    a = field.food_pheromone_level * randint(80, 100)/100
                    b = best_pheromone.food_pheromone_level

                    if a > b:
                        best_pheromone = field

        if best_pheromone != None:
            self.move(self.ant.x, self.ant.y, best_pheromone.x, best_pheromone.y)
            self.ant.x = best_pheromone.x
            self.ant.y = best_pheromone.y
            return

        # strategy 4: if possible, move randomly straight-left, straight or straight-right
        if len(neighbours_by_orientation) > 0:
            next_field = neighbours_by_orientation[randint(0, len(neighbours_by_orientation) - 1)]
            self.move(self.ant.x, self.ant.y, next_field.x, next_field.y)
            self.ant.x = next_field.x
            self.ant.y = next_field.y
            return

        # strategy 5: else turn randomly left or right
        if bool(getrandbits(1)) is True:
            self.ant.orientation = Orientation.right(self.ant.orientation)
        else:
            self.ant.orientation = Orientation.left(self.ant.orientation)

    def move(self, current_x, current_y, target_x, target_y):
        self.ant.colony.world.move_ant(current_x, current_y, target_x, target_y)

        self.ant.colony.world.deposit_pheromone(current_x, current_y, PheromoneType.HOME, 255)

        # calculate new orientation
        if current_x - target_x == 0:
            if current_y - target_y > 0:
                self.ant.orientation = Orientation.NORTH
            elif current_y - target_y < 0:
                self.ant.orientation = Orientation.SOUTH
        elif current_x - target_x > 0:
            if current_y - target_y > 0:
                self.ant.orientation = Orientation.NORTHWEST
            elif current_y - target_y == 0:
                self.ant.orientation = Orientation.WEST
            elif current_y - target_y < 0:
                self.ant.orientation = Orientation.SOUTHWEST
        elif current_x - target_x < 0:
            if current_y - target_y > 0:
                self.ant.orientation = Orientation.NORTHEAST
            elif current_y - target_y == 0:
                self.ant.orientation = Orientation.EAST
            elif current_y - target_y < 0:
                self.ant.orientation = Orientation.SOUTHEAST

class SearchHomeState(AntState):
    def __init__(self, ant):
        super().__init__(ant)

    def handle(self):
        #self.ant.state = SearchFoodState(self.ant)
        pass

class WorldFacade():
    def __init__(self, world):
        self.world = world
        self.neighbours_cache = None

    def get_neighbours(self, x, y):
        self.neighbours_cache = self.world.get_neighbours(x, y, 1)
        return self.neighbours_cache

    def get_neighbours_by_orientation(self, x, y, orientation):
        orientation = Orientation(orientation)

        if self.neighbours_cache is None:
            self.world.get_neighbours(x, y)

        if orientation == Orientation.NORTH:
            neighbours_by_orientation = [
                self.neighbours_cache[0][0],
                self.neighbours_cache[1][0],
                self.neighbours_cache[2][0]
            ]
        elif orientation == Orientation.NORTHEAST:
            neighbours_by_orientation = [
                self.neighbours_cache[1][0],
                self.neighbours_cache[2][0],
                self.neighbours_cache[2][1]
            ]
        elif orientation == Orientation.EAST:
            neighbours_by_orientation = [
                self.neighbours_cache[2][0],
                self.neighbours_cache[2][1],
                self.neighbours_cache[2][2]
            ]
        elif orientation == Orientation.SOUTHEAST:
            neighbours_by_orientation = [
                self.neighbours_cache[2][1],
                self.neighbours_cache[2][2],
                self.neighbours_cache[1][2]
            ]
        elif orientation == Orientation.SOUTH:
            neighbours_by_orientation = [
                self.neighbours_cache[2][2],
                self.neighbours_cache[1][2],
                self.neighbours_cache[0][2]
            ]
        elif orientation == Orientation.SOUTHWEST:
            neighbours_by_orientation = [
                self.neighbours_cache[1][2],
                self.neighbours_cache[0][2],
                self.neighbours_cache[0][1]
            ]
        elif orientation == Orientation.WEST:
            neighbours_by_orientation = [
                self.neighbours_cache[0][2],
                self.neighbours_cache[0][1],
                self.neighbours_cache[0][0]
            ]
        elif orientation == Orientation.NORTHWEST:
            neighbours_by_orientation = [
                self.neighbours_cache[0][1],
                self.neighbours_cache[0][0],
                self.neighbours_cache[1][0]
            ]

        return neighbours_by_orientation

    def get_food(self, x, y):
        field = self.world.get(x, y)

        player, level = max(enumerate(field.player_food_levels), key=operator.itemgetter(1))

        if level > 0:
            return Food(x, y, player, level)

        return None

    def move_ant(self, source_x, source_y, destination_x, destination_y):
        self.world.move_ant(source_x, source_y, destination_x, destination_y)

    def deposit_pheromone(self, x, y, type, strength):
        self.world.deposit_pheromone(x, y, type, strength)
