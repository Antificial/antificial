from enum import IntEnum
import abc
import operator
import math
from random import getrandbits, randint

SEARCH_HOME_RANDOM_FACTOR = 10
SEARCH_FOOD_RANDOM_FACTOR = 15
HOME_DISTANCE_FACTOR = 4.07

HOME_PHEROMONE_STRENGTH = 200
FOOD_PHEROMONE_STRENGTH = 55

def distance(x1, y1, x2, y2):
    return math.sqrt((x2-x1)**2+(y2-y1)**2)

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
        pass

class Colony(GameObject):
    def __init__(self, world, home, antcount=100):
        self.world = WorldFacade(world)
        self.home = Home(home[0], home[1], world)
        self.antcount = antcount
        self.ants = []
        self.observers = []
        self.gamerules = None
        self.scores = [0 for x in range(2)]

        for i in range(antcount):
            ant = Ant(self)
            state = SearchFoodState(ant)
            ant.init_state(state)
            self.ants.append(ant)

    def drop_off_food(self, player):
        self.scores[player] += 1

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
        return self.scores

class Home(GameObject):
    def __init__(self, x, y, world):
        super().__init__(x, y)
        self.world = world
        world.set_home(x, y)

    def update():
        pass

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
        self.orientation = Orientation(randint(0, 7))
        self.state = None
        self.player = None
        self.foundFood = False
        self.lastX = None
        self.lastY = None

    def init_state(self, state):
        self.state = state

    def update(self):
        self.state.handle()

    def __str__(self):
        output = "{"
        output += "x: " + str(self.x)
        output += ", y: " + str(self.y)
        output += ", orientation: " + str(self.orientation)
        output += ", state: " + str(self.state)
        output += ", player: " + str(self.player)
        output += "}"

        return output

class AntState(abc.ABC):
    def __init__(self, ant):
        self.ant = ant

    @abc.abstractmethod
    def handle(self):
        pass

class SearchFoodState(AntState):
    def __init__(self, ant):
        super().__init__(ant)

    def __str__(self):
        return "SearchFoodState"

    def handle(self):
        # get world
        world = self.ant.colony.world

        # strategy 1: if ant is on food field, eat food
        food = world.get_food(self.ant.x, self.ant.y)
        if food != None:
            self.ant.player = food.player
            self.ant.foundFood = True
            self.ant.state = SearchHomeState(self.ant)
            return

        # get neighbours as list
        neighbours = world.get_neighbours_as_list(self.ant.x, self.ant.y)

        # strategy 2: if ant is close to food field, go there
        best_food = None
        for neighbour in neighbours:
            if neighbour is None:
                continue

            food = world.get_food(neighbour.x, neighbour.y)
            if food != None:
                if best_food != None:
                    if food.level > best_food.level:
                        best_food = food
                else:
                    best_food = food

        if best_food != None:
            self.move(self.ant.x, self.ant.y, best_food.x, best_food.y)
            return

        # strategy 3: if ant is close to food pheromone field, go there

        # if ant is not at home location, consider only the ant's neighbours relative to its orientation
        home = world.get_home(self.ant.x, self.ant.y)
        if home is None:
            neighbours = world.get_neighbours_by_orientation(self.ant.x, self.ant.y, self.ant.orientation)

        best_pheromone = None
        for field in neighbours:
            if field.food_pheromone_level > 0:
                if best_pheromone == None:
                    best_pheromone = field
                elif field.food_pheromone_level > best_pheromone.food_pheromone_level:
                    best_pheromone = field

        if best_pheromone != None and randint(0, 100) < 100 - SEARCH_FOOD_RANDOM_FACTOR:
            self.move(self.ant.x, self.ant.y, best_pheromone.x, best_pheromone.y)
            return

        # strategy 4: if possible, move randomly straight-left, straight or straight-right
        if len(neighbours) > 0:
            next_field = neighbours[randint(0, len(neighbours) - 1)]
            self.move(self.ant.x, self.ant.y, next_field.x, next_field.y)
            return

        # strategy 5: else turn randomly left or right
        if bool(getrandbits(1)) is True:
            self.ant.orientation = Orientation.right(self.ant.orientation)
        else:
            self.ant.orientation = Orientation.left(self.ant.orientation)

    def move(self, current_x, current_y, target_x, target_y):
        self.ant.colony.world.move_ant(current_x, current_y, target_x, target_y)

        self.ant.x = target_x
        self.ant.y = target_y
        self.ant.lastX = current_x
        self.ant.lastY = current_y

        self.ant.colony.world.deposit_pheromone(current_x, current_y, PheromoneType.HOME)

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

    def __str__(self):
        return "SearchHomeState"

    def handle(self):
        # get world
        world = self.ant.colony.world

        # strategy 1: if ant is on home field, deliver food
        home = world.get_home(self.ant.x, self.ant.y)
        if home != None:
            self.ant.player = None
            self.ant.foundFood = False
            self.ant.state = SearchFoodState(self.ant)
            return

        # if the ant found the food set the foundFood flag, so the ant begins to deposit pheromones
        food = world.get_food(self.ant.x, self.ant.y)
        if food != None:
            self.ant.foundFood = True

        # get neighbours as list
        neighbours = world.get_neighbours_as_list(self.ant.x, self.ant.y)

        # strategy 2: if ant is close to home field, go there
        homes_nearby = []
        for neighbour in neighbours:
            if neighbour is None:
                continue

            home = world.get_home(neighbour.x, neighbour.y)
            if home != None:
                homes_nearby.append(home)

        if len(homes_nearby) > 0:
            target = homes_nearby[randint(0, len(homes_nearby) - 1)]
            self.move(self.ant.x, self.ant.y, target.x, target.y, self.ant.foundFood)
            return

        # strategy 3: if ant is not at a food location, consider only the ant's neighbours relative to its orientation
        #food = world.get_food(self.ant.x, self.ant.y)
        #if food is None:
        #    neighbours = world.get_neighbours_as_list(self.ant.x, self.ant.y)

        # remove last position, so the ant does not endlessly walk back and forth
        for field in neighbours:
            if field.x == self.ant.lastX and field.y == self.ant.lastY:
                neighbours.remove(field)
                break

        attractivess = 0
        best_pheromone = None
        for field in neighbours:
            if field.home_pheromone_level <= 0:
                continue
            dist = distance(field.x, field.y, self.ant.colony.home.x, self.ant.colony.home.y)
            tmp_attractivess = (field.home_pheromone_level / 255) + (((128 - dist) / 128) * HOME_DISTANCE_FACTOR)

            if attractivess < tmp_attractivess:
                attractivess = tmp_attractivess
                best_pheromone = field

        if best_pheromone != None and randint(0, 100) < 100 - SEARCH_HOME_RANDOM_FACTOR:
            self.move(self.ant.x, self.ant.y, best_pheromone.x, best_pheromone.y, self.ant.foundFood)
            return

        # strategy 4: if possible, move randomly straight-left, straight or straight-right
        neighbours = world.get_neighbours_by_orientation(self.ant.x, self.ant.y, self.ant.orientation)

        if len(neighbours) > 0:
            next_field = neighbours[randint(0, len(neighbours) - 1)]
            if next_field != None:
                self.move(self.ant.x, self.ant.y, next_field.x, next_field.y, self.ant.foundFood)
                return

        # strategy 5: else turn randomly left or right
        if bool(getrandbits(1)) is True:
            self.ant.orientation = Orientation.right(self.ant.orientation)
        else:
            self.ant.orientation = Orientation.left(self.ant.orientation)

    def move(self, current_x, current_y, target_x, target_y, foundFood):
        if target_x == self.ant.colony.home.x and target_y == self.ant.colony.home.y:
            self.ant.colony.drop_off_food(self.ant.player)

        self.ant.colony.world.move_ant(current_x, current_y, target_x, target_y)

        self.ant.x = target_x
        self.ant.y = target_y
        self.ant.lastX = current_x
        self.ant.lastY = current_y

        if foundFood:
            self.ant.colony.world.deposit_pheromone(current_x, current_y, PheromoneType.FOOD)

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

class WorldFacade():
    def __init__(self, world):
        self.world = world

    def get_neighbours(self, x, y):
        return self.world.get_neighbours(x, y, 1)

    def get_neighbours_as_list(self, x, y, excludeBordersAndObstacles = True):
        neighbours = self.get_neighbours(x, y)

        # reorder them according to orientation
        neighbours = [
            neighbours[1][0],   # north
            neighbours[2][0],   # northeast
            neighbours[2][1],   # east
            neighbours[2][2],   # southeast
            neighbours[1][2],   # south
            neighbours[0][2],   # southwest
            neighbours[0][1],   # west
            neighbours[0][0]    # northwest
        ]

        if not excludeBordersAndObstacles:
            return neighbours

        # exclude borders and obstacles
        return [x for x in neighbours if x != None]

    def get_neighbours_by_orientation(self, x, y, orientation):
        orientation = Orientation(orientation)
        neighbours = self.get_neighbours_as_list(x, y, False)

        straight_left = orientation - 1
        if straight_left < 0:
            straight_left = 7

        straight_right = orientation + 1
        if straight_right > 7:
            straight_right = 0

        neighbours = [
            neighbours[straight_left],  # straight left
            neighbours[orientation],    # straight
            neighbours[straight_right]  # straight right
        ]

        # exclude borders and obstacles
        return [x for x in neighbours if x != None]

    def get_food(self, x, y):
        field = self.world.get(x, y)

        player, level = max(enumerate(field.player_food_levels), key=operator.itemgetter(1))

        if level > 0:
            return Food(x, y, player, level)

        return None

    def get_home(self, x, y):
        field = self.world.get(x, y)

        if field.is_nest > 0:
            return Home(x, y, self.world)

        return None

    def move_ant(self, source_x, source_y, destination_x, destination_y):
        self.world.move_ant(source_x, source_y, destination_x, destination_y)

    def deposit_pheromone(self, x, y, pheromone_type):
        if pheromone_type is PheromoneType.HOME:
            self.world.deposit_pheromone(x, y, pheromone_type, HOME_PHEROMONE_STRENGTH)
        else:
            self.world.deposit_pheromone(x, y, pheromone_type, FOOD_PHEROMONE_STRENGTH)
