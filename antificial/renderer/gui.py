#! /usr/bin/env python

import util
import time, math, os, datetime
from random import randint

# TODO: replace this with push through queue?
from framework import handler

PROJECTOR_MODE = False

from kivy.config import Config
Config.set("kivy", "log_level", "warning") # one of: trace, debug, info, warning, error, critical
if PROJECTOR_MODE:
    Config.set("graphics", "fullscreen", 0) # can be 0, 1 or 'auto'
    Config.set("graphics", "borderless", 1) # can be 0 or 1
    Config.set("graphics", "width", 1920) # can be 0 or 1
    Config.set("graphics", "height", 1080) # can be 0 or 1
    Config.set("graphics", "resizable", 0) # can be 0 or 1
    Config.set("graphics", "maxfps", 30) # speaks for itself, i guess
else:
    Config.set("graphics", "fullscreen", 0) # can be 0, 1 or 'auto'
    Config.set("graphics", "borderless", 0) # can be 0 or 1
    Config.set("graphics", "width", 800) # can be 0 or 1
    Config.set("graphics", "height", 600) # can be 0 or 1
    Config.set("graphics", "resizable", 1) # can be 0 or 1
    Config.set("graphics", "maxfps", 30) # speaks for itself, i guess
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition, RiseInTransition
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.image import Image, AsyncImage
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty
from kivy.graphics.vertex_instructions import Line, Rectangle, RoundedRectangle
from kivy.graphics import Color, InstructionGroup
from kivy.clock import Clock
from kivy.vector import Vector

def interpolate_color(c1, c2, ratio):
    def intr_clr_ch(c1, c2, ratio):
        return c2 + ratio * (c1 - c2)
    return [intr_clr_ch(c1[0], c2[0], ratio),intr_clr_ch(c1[1], c2[1], ratio),intr_clr_ch(c1[2], c2[2], ratio), 1.0]

class SplashWidget(Widget):
    title = ObjectProperty(None)
    subtitle = ObjectProperty(None)
    splash = ObjectProperty(None)
    scale = NumericProperty(0.25)

    def __init__(self, **kwargs):
        super(SplashWidget, self).__init__(**kwargs)
        self.splash.source = os.path.join(ROOT_PATH, "splashscreen.png")

class StartWidget(Widget):
    title = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(StartWidget, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        pass

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        global CURRENT_SCREEN, DEBUG
        if keycode[0] == 276: # left arrow
            CURRENT_SCREEN = (CURRENT_SCREEN - 1) % len(SCREEN_LIST)
            change_screen(SCREEN_LIST[CURRENT_SCREEN].name)
        elif keycode[0] == 275: # right arrow
            CURRENT_SCREEN = (CURRENT_SCREEN + 1) % len(SCREEN_LIST)
            change_screen(SCREEN_LIST[CURRENT_SCREEN].name)
        else:
            FW_CC_QUEUE.put("[KEY] %d" % keycode[0])
        if keycode[0] == 100: # D
            DEBUG = not DEBUG

class SimulationWidget(Widget):
    fps = ObjectProperty(None)
    p1_time_label = ObjectProperty(None)
    p2_time_label = ObjectProperty(None)
    p1_score_label = ObjectProperty(None)
    p2_score_label = ObjectProperty(None)
    bar_width = NumericProperty(20)
    p1_ratio = NumericProperty(0)
    p2_ratio = NumericProperty(0)
    meter_width = NumericProperty(0)
    meter_height = NumericProperty(100)
    p1_color = [244/255, 77/255, 27/255]
    p2_color = [28/255, 188/255, 40/255]
    meter_indicator = ObjectProperty(None)
    meter_backdrop = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SimulationWidget, self).__init__(**kwargs)
        self.nest_radius = 3
        self.old_window_size_x = 0
        self.old_window_size_y = 0
        self.cells = [[0 for y in range(HEIGHT)] for x in range(WIDTH+1)]
        x, y = Window.size
        self.spacing_x = x / WIDTH
        self.spacing_y = y / HEIGHT
        self.meter_width = x / 2
        self.meter_bar = InstructionGroup()
        self.meter_bar.add(Color(1,1,1))
        self.meter_bar.add(RoundedRectangle(pos=[x / 2 - self.meter_width / 2,y - self.meter_height * 0.9], size=[self.meter_width,self.meter_height / 3]))
        self.meter_indicator.source = os.path.join(ROOT_PATH, "indicator.png")
        self.meter_backdrop.source = os.path.join(ROOT_PATH, "indicator_backdrop.png")
        self.meter_backdrop.pos = [x / 2 - self.meter_backdrop.size[0] / 2,y - self.meter_height * 1.2]
        self.meter_indicator.pos = [x / 2 - self.meter_indicator.size[0] / 2,y - self.meter_height * 1.2]
        self.meter_backdrop.size = [self.meter_height,self.meter_height]
        self.meter_indicator.size = [self.meter_height,self.meter_height]
        self.meter_backdrop.color = interpolate_color(self.p1_color, self.p2_color, 0.5)
        self.sides = InstructionGroup()
        self.sides.add(Color(rgb=self.p1_color))
        self.sides.add(Rectangle(pos=[0,0], size=[self.bar_width,y]))
        self.sides.add(Color(rgb=self.p2_color))
        self.sides.add(Rectangle(pos=[x-self.bar_width,0], size=[self.bar_width,y]))
        x = 0
        y = -1
        count = 0
        for i in range(0, len(WORLD_DATA), INTS_PER_FIELD):
            x = (i - (count * INTS_PER_FIELD) + count) % WIDTH
            count += 1
            if x % WIDTH == 0:
                y += 1
            y_inverted = HEIGHT - y - 1
            g = InstructionGroup()
            g.add(Color(0, 0, 0, 1)) # black
            g.add(Rectangle(pos=(x * self.spacing_x, y_inverted * self.spacing_y), size=(self.spacing_x, self.spacing_y)))
            self.ids["grid_layout"].canvas.add(g)
            self.cells[x][y_inverted] = g
        self.ids["grid_layout"].canvas.add(self.sides)
        self.ids["grid_layout"].canvas.add(self.meter_bar)

    def update_data(self, dt):
        global DEBUG, TIME, SCORE, GAME_DURATION
        x, y = Window.size
        if GAME_STATE == GAME_RUNNING:
            TIME += 1
            seconds_to_display = GAME_DURATION - TIME
            if seconds_to_display < 0:
                seconds_to_display = 0
            display_time = str(datetime.timedelta(seconds=seconds_to_display))
            self.p1_time_label.text = display_time
            self.p1_score_label.text = "Score: %04d" % SCORES[0]
            self.p2_time_label.text = display_time
            self.p2_score_label.text = "Score: %04d" % SCORES[1]
        if DEBUG and GAME_STATE == GAME_RUNNING:
            self.fps.text = "%d FPS : RES: (%d, %d)" % (round(Clock.get_fps()), x, y)
        else:
            self.fps.text = ""

    def update(self, dt):
        global BLACK, WHITE, RED, GREEN, BLUE, GRAY
        maximum = SCORES[0] + SCORES[1] + 1
        self.ratio = SCORES[0] / maximum
        with self.canvas:
            x, y = Window.size
            self.spacing_x = x / WIDTH
            self.spacing_y = y / HEIGHT
            R, G, B = 0, 0, 0
            if GAME_STATE == GAME_RUNNING and self.ratio > 0:
                self.meter_backdrop.color = interpolate_color(self.p1_color, self.p2_color, self.ratio)
                self.meter_backdrop.pos = [(x / 2 - self.meter_width / 2) + (x / 2) - self.meter_width * self.ratio - self.meter_backdrop.size[0] / 2, y - self.meter_height * 1.2]
                self.meter_indicator.pos = [(x / 2 - self.meter_width / 2) + (x / 2) - self.meter_width * self.ratio - self.meter_indicator.size[0] / 2, y - self.meter_height * 1.2]
            if self.old_window_size_x != x or self.old_window_size_y != y:
                self.old_window_size_x = x
                self.old_window_size_y = y
                self.sides.children[2].size = [self.bar_width,y]
                self.sides.children[5].pos = [x-self.bar_width,0]
                self.sides.children[5].size = [self.bar_width,y]
                self.meter_width = x / 2
                self.meter_backdrop.pos = [x / 2 - self.meter_backdrop.size[0] / 2,y - self.meter_height * 1.2]
                self.meter_indicator.pos = [x / 2 - self.meter_indicator.size[0] / 2,y - self.meter_height * 1.2]
                self.meter_backdrop.color = interpolate_color(self.p1_color, self.p2_color, 0.5)
                self.meter_bar.children[2].pos = [x / 2 - self.meter_width / 2,y - self.meter_height * 0.9]
                self.meter_bar.children[2].size = [self.meter_width,self.meter_height / 3]
                for x in range(WIDTH):
                    for y in range(HEIGHT):
                        val = self.cells[x][y]
                        if val != 0:
                            val.children[2].pos = (x * self.spacing_x, y * self.spacing_y)
                            val.children[2].size = (self.spacing_x, self.spacing_y)
            x = 0
            y = -1
            count = 0
            nest_coordinates = (0, 0)
            for i in range(0, len(WORLD_DATA), INTS_PER_FIELD):
                x = (i - (count * INTS_PER_FIELD) + count) % WIDTH
                count += 1
                if x % WIDTH == 0:
                    y += 1
                y_inverted = HEIGHT - y - 1

                is_nest = WORLD_DATA[i] > 0
                if is_nest:
                    nest_coordinates = (x, y_inverted)
                ant_count = WORLD_DATA[i + 1]
                home_pheromone_level = WORLD_DATA[i + 2]
                food_pheromone_level = WORLD_DATA[i + 3]

                self.cells[x][y_inverted].children[0].rgb = [0, 0, 0]

                has_food = False
                for player_index in range(PLAYER_COUNT):
                    if WORLD_DATA[i + 4 + player_index] > 0:
                        has_food = True
                        break
                if not has_food:
                    display_home_pheromone = SHOW_HOME_PHEROMONES and home_pheromone_level > 0
                    display_food_pheromone = SHOW_FOOD_PHEROMONES and food_pheromone_level > 0
                    if display_home_pheromone and display_food_pheromone:
                        alpha = (((food_pheromone_level / 255) + (home_pheromone_level / 255)) / 2)
                        self.cells[x][y_inverted].children[0].rgba = [0, 1, 1, alpha]
                    elif display_home_pheromone:
                        self.cells[x][y_inverted].children[0].rgba = [0, 0, 1, home_pheromone_level / 255 * ALPHA_DAMPEN]
                    elif display_food_pheromone:
                        self.cells[x][y_inverted].children[0].rgba = [0, 1, 0, food_pheromone_level / 255 * ALPHA_DAMPEN]
                if ant_count > 0:
                    self.cells[x][y_inverted].children[0].rgb = [1, 1, 1]
                for player_index in range(PLAYER_COUNT):
                    food_level = WORLD_DATA[i + 4 + player_index]
                    if food_level > 0:
                        has_food = True
                        if player_index == 0:
                            self.cells[x][y_inverted].children[0].rgba = [1, 0, 0, food_level / 255]
                        elif player_index == 1:
                            self.cells[x][y_inverted].children[0].rgba = [0, 1, 0, food_level / 255]
                        else:
                            self.cells[x][y_inverted].children[0].rgba = [0, 0, 1, food_level / 255]
            nest_x = nest_coordinates[0]
            nest_y = nest_coordinates[1]
            if nest_coordinates != (0,0):
                self.cells[nest_x][nest_y].children[0].rgb = [0.5, 0.5, 0.5]
                half_nest_radius = math.ceil(self.nest_radius / 2)
                for radius_x in range(nest_x-half_nest_radius, nest_x+half_nest_radius):
                    for radius_y in range(nest_y-half_nest_radius, nest_y+half_nest_radius):
                        self.cells[radius_x][radius_y].children[0].rgb = [237/255, 217/255, 2/255]

class EndWidget(Widget):
    color_win = ListProperty([28/255,188/255,40/255,0.75])
    color_lose = ListProperty([244/255,77/255,27/255,0.75])
    color_1 = ListProperty([0,0,0,1])
    color_2 = ListProperty([0,0,0,1])
    winner_image = ObjectProperty(None)
    scale = NumericProperty(1.5)
    winner_rotation = NumericProperty(-90)
    winner_pos = ListProperty([0,0])

    def __init__(self, **kwargs):
        super(EndWidget, self).__init__(**kwargs)
        self.winner_image.source = os.path.join(ROOT_PATH, "winner.zip")
        self.winner_image.color = [0,0,0,0]

    def update(self):
        x, y = Window.size
        if SCORES[0] > SCORES[1]:
            self.winner_image.reload()
            self.winner_rotation = -90
            self.winner_image.color = [1,1,1,1]
            self.winner_pos = [x/4, y/2]
            self.color_1 = self.color_win
            self.color_2 = self.color_lose
        elif SCORES[0] < SCORES[1]:
            self.winner_image.reload()
            self.winner_rotation = 90
            self.winner_image.color = [1,1,1,1]
            self.winner_pos = [(x/4)*3, y/2]
            self.color_1 = self.color_lose
            self.color_2 = self.color_win
        else:
            self.winner_image.color = [0,0,0,0]
            self.color_1.rgb = [0.5, 0.5, 0.5]
            self.color_2.rgb = [0.5, 0.5, 0.5]

class MenuWidget(Widget):
    btn_quit = ObjectProperty(None)
    tick_slider = ObjectProperty(None)
    game_duration_slider = ObjectProperty(None)
    home_trail_slider = ObjectProperty(None)
    food_trail_slider = ObjectProperty(None)
    ant_count_slider = ObjectProperty(None)
    btn_count = NumericProperty(1)

    def __init__(self, **kwargs):
        super(MenuWidget, self).__init__(**kwargs)
        self.btn_quit.on_press = self.quit
        self.btn_count = len([widget for widget in self.walk(restrict=True) if type(widget) is Button])
        self.tick_slider.bind(value=self.on_tick_slider_change)
        self.game_duration_slider.bind(value=self.on_game_duration_slider_change)
        self.home_trail_slider.bind(value=self.on_home_trail_slider_change)
        self.food_trail_slider.bind(value=self.on_food_trail_slider_change)
        self.ant_count_slider.bind(value=self.on_ant_count_slider_change)
        self.tick_slider.value = IPS
        self.ant_count_slider.value = ANT_COUNT

    def on_tick_slider_change(self, instance, value):
        FW_CC_QUEUE.put("[IPS] %d" % value)

    def on_game_duration_slider_change(self, instance, value):
        global GAME_DURATION
        GAME_DURATION = value
        FW_CC_QUEUE.put("[GDU] %d" % value)

    def on_home_trail_slider_change(self, instance, value):
        FW_CC_QUEUE.put("[HTD] %d" % value)

    def on_food_trail_slider_change(self, instance, value):
        FW_CC_QUEUE.put("[FTD] %d" % value)

    def on_ant_count_slider_change(self, instance, value):
        FW_CC_QUEUE.put("[IAC] %d" % value)

    def quit(self):
        IR_CC_QUEUE.put("[CMD] done")
        FW_CC_QUEUE.put("[CMD] done")
        App.get_running_app().stop()

def get(x, y):
    if x >= WIDTH or y >= HEIGHT:
        s = "Index %d or %d is out of bounds." % (x, y)
        raise IndexError(s)
    position = (y * HEIGHT * INTS_PER_FIELD) + (x * INTS_PER_FIELD)
    values = []
    for i in range(INTS_PER_FIELD):
        values.append(WORLD_DATA[position + i])
    return values

def poll(dt):
    global NUMBER, CURRENT_SCREEN, TIME, SCORES
    while FW_OUTPUT.poll():
        input = FW_OUTPUT.recv()
        if isinstance(input, str):
            if input.startswith("[GAME_STATE]"):
                global GAME_STATE
                GAME_STATE = int(input[12:])
                if GAME_STATE == GAME_BEGIN:
                    change_screen("start")
                elif GAME_STATE == GAME_RUNNING:
                    change_screen("simulation")
                elif GAME_STATE == GAME_END:
                    TIME = 0
                    SCREEN_LIST[3].children[0].update()
                    change_screen("end")
            elif input.startswith("[IPS]"):
                global IPS
                IPS = int(input[6:])
                SCREEN_LIST[4].children[0].tick_slider.value = IPS
        elif isinstance(input, list):
            SCORES = input

def index_of_screen(name):
    for i, screen in enumerate(SCREEN_LIST):
        if screen.name == name:
            return i
    else:
        return None

def change_screen(name):
    global CURRENT_SCREEN
    previous = index_of_screen(sm.current)
    new = index_of_screen(name)
    if name == "end":
        sm.transition = RiseInTransition()
    else:
        sm.transition = SlideTransition()
    direction = (new - previous) % len(SCREEN_LIST)
    if direction == 1:
        sm.transition.direction = "left"
    else:
        sm.transition.direction = "right"
    sm.current = name
    CURRENT_SCREEN = new

# declare screens
class SplashScreen(Screen):
    pass
class StartScreen(Screen):
    pass
class SimulationScreen(Screen):
    pass
class EndScreen(Screen):
    pass
class MenuScreen(Screen):
    pass

SHOW_HOME_PHEROMONES = True
SHOW_FOOD_PHEROMONES = True


WHITE = Color(1, 1, 1, 1)
BLACK = Color(0, 0, 0, 1)
RED = Color(1, 0, 0, 1)
BLUE = Color(0, 0, 1, 1)
GREEN = Color(0, 1, 0, 1)
GRAY = Color(0.5, 0.5, 0.5)

ALPHA_DAMPEN = 0.5
IPS = handler.IPS
ANT_COUNT = handler.ANT_COUNT
CURRENT_SCREEN = 0
GAME_BEGIN = 0
GAME_RUNNING = 1
GAME_END = 2
GAME_STOP = 3
GAME_STATE = GAME_BEGIN
GAME_DURATION = handler.GAME_DURATION
TIME = 0
SCORES = []
ROOT_PATH = os.path.dirname(__file__)
sm = ScreenManager()
SCREEN_LIST = [SplashScreen(name="splash"), StartScreen(name="start"), SimulationScreen(name="simulation"), EndScreen(name="end"), MenuScreen(name="menu")]
for screen in SCREEN_LIST:
    sm.add_widget(screen)
DEBUG = False

class AntificialApp(App):
    def __init__(self, fw_output, ir_cc_queue, fw_cc_queue, world_data, grid_resolution, player_count, grid_size):
        global FW_OUTPUT, IR_CC_QUEUE, FW_CC_QUEUE, WORLD_DATA, WIDTH, HEIGHT, GRID_SIZE, INTS_PER_FIELD, SCORES, PLAYER_COUNT, PROJECTOR_MODE
        super(AntificialApp, self).__init__()
        FW_OUTPUT = fw_output
        IR_CC_QUEUE = ir_cc_queue
        FW_CC_QUEUE = fw_cc_queue
        WORLD_DATA = world_data
        WIDTH = grid_resolution[0]
        HEIGHT = grid_resolution[1]
        GRID_SIZE = grid_size
        INTS_PER_FIELD = 4 + player_count
        SCORES = [0 for i in range(player_count)]
        PLAYER_COUNT = player_count


    def build(self):
        splash_widget = SplashWidget()
        start_widget = StartWidget()
        simulation_widget = SimulationWidget()
        end_widget = EndWidget()
        menu_widget = MenuWidget()

        SCREEN_LIST[0].add_widget(splash_widget)
        SCREEN_LIST[1].add_widget(start_widget)
        SCREEN_LIST[2].add_widget(simulation_widget)
        SCREEN_LIST[3].add_widget(end_widget)
        SCREEN_LIST[4].add_widget(menu_widget)

        Clock.schedule_interval(poll, 1.0 / 1.0)
        Clock.schedule_interval(simulation_widget.update_data, 1.0 / 1.0)
        Clock.schedule_interval(simulation_widget.update, 1.0 / 10)

        sm.bind(on_close=self._on_close)
        Window.bind(on_close=self._on_close)

        if PROJECTOR_MODE:
            Window.left = 1920
        return sm

    def _on_close(self, *largs):
        IR_CC_QUEUE.put("[CMD] done")
        FW_CC_QUEUE.put("[CMD] done")
        App.get_running_app().stop()
