import abc

class Observer(object):
    @abc.abstractmethod
    def update(self, *args, **kwargs):
        pass

class GameRules(Observer):
    def __init__(self, colony):
        self.colony = colony

    def update(self, *args, **kwargs):
        pass

class Player(object):
    def __init__(self, radius):
        self.food = []