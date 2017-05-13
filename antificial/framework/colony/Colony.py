from enum import Enum
import abc

class Orientation(Enum):
    NORTH = 1
    EAST = 2
    SOUTH = 3
    WEST = 4
    NORTHEAST = 5
    SOUTHEAST = 6
    SOUTHWEST = 7
    NORTHWEST = 8

class PheromoneType(Enum):
    HOME = 1
    FOOD = 2

class GameObject(abc.ABC):
    def __init__(self, x, y):
        self._x = x
        self._y = y

    @abc.abstractmethod
    def update():
        pass

class Colony(GameObject):
    def __init__(self, gameworld, home, antcount=100):
        self.gameworld = gameworld
        self.antcount = antcount
        self.home = Home(home[0], home[1])
        self.ants = []
        self.observers = []
        self.gamerules = None
        # init ants

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
        pass

class Home(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        # write into gameworld

    def update():
        pass

class Food(GameObject):
    def __init__(self, x, y, player):
        super().__init__(self, x, y)
        self.player = player

class Ant(GameObject):
    def __init__(self, state, colony):
        super().__init__(self, colony.home.x, colony.home.y)
        self._state = state
        self._orientation = Orientation.NORTH
        self.colony = colony
        self.player = None
        # write into gameworld

    def update():
        _state.handle()

class AntState(abc.ABC):
    def __init__(self, ant):
        self._ant = ant

    @abc.abstractmethod
    def handle():
        pass

class SearchFoodState(AntState):
    def __init__(self, ant):
        super().__init__(self, ant)

    def handle():
        pass

class SearchHomeState(AntState):
    def __init__(self, ant):
        super().__init__(self, ant)

    def handle():
        pass
