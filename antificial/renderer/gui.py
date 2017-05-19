#! /usr/bin/env python

import util
import time, math, os
from random import randint

from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.image import Image, AsyncImage
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.graphics.vertex_instructions import Line, Rectangle
from kivy.graphics import Color, InstructionGroup
from kivy.clock import Clock
from kivy.vector import Vector

Builder.load_string("""
<SplashWidget>:
    title: title_label
    subtitle: subtitle_label
    splash: splash_image
    AsyncImage:
        id: splash_image
        size: root.width * root.scale, root.width * root.scale
        pos: root.width / 2 - root.splash.size[0] / 2, root.top / 2 + 10
    Label:
        id: title_label
        font_size: 70
        center_x: root.width / 2
        top: root.top / 2
        text: "Antificial"
    Label:
        id: subtitle_label
        font_size: 35
        center_x: root.width / 2
        top: root.top / 2 - root.title.height
        text: "Loading..."

<StartWidget>:
    title: title_label
    Label:
        id: title_label
        font_size: 70
        center_x: root.width / 2
        top: root.top / 2
        text: "Press [Spacebar] to play!"

<SimulationWidget>:
    fps: fps_label
    Label:
        id: fps_label
        font_size: 70
        center_x: root.width / 2
        top: root.top - 50
        text: "00 FPS"

<EndWidget>:
    title: title_label
    Label:
        id: title_label
        font_size: 70
        center_x: root.width / 2
        top: root.top / 2
        text: "Game Finished"

<MenuWidget>:
    dbg: dbg_label
    btn_quit: btn_quit
    tick_slider: tick_slider
    BoxLayout:
        orientation: "horizontal"
        spacing: 10
        size: root.width, root.height
        GridLayout:
            cols: 1
            rows: 2
            spacing: 10
            padding: 10
            row_default_height: 80
            row_force_default: True
            BoxLayout:
                Label:
                    size: self.texture_size
                    font_size: 48
                    text: "Ticks / Second"
                Label:
                    size: self.texture_size
                    font_size: 48
                    text:  str(tick_slider.value)
            Slider:
                id: tick_slider
                min: 1
                max: 20
                step: 1
                value: 10
                value_track: True
        BoxLayout:
            spacing: 10
            padding: 10
            Label:
                id: dbg_label
                font_size: 70
                size: self.texture_size
                center_x: root.width / 2
                top: root.top - 150
                text: "0"
    BoxLayout:
        orientation: "horizontal"
        spacing: 10
        padding: 10
        size: root.width, 100
        Button:
            id: btn_quit
            text: "Quit"
            size_hint: root.width / root.btn_count, 1
""")

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
        global CURRENT_SCREEN
        if keycode[0] == 276: # left arrow
            CURRENT_SCREEN = (CURRENT_SCREEN - 1) % len(SCREEN_LIST)
            change_screen(SCREEN_LIST[CURRENT_SCREEN].name)
        elif keycode[0] == 275: # right arrow
            CURRENT_SCREEN = (CURRENT_SCREEN + 1) % len(SCREEN_LIST)
            change_screen(SCREEN_LIST[CURRENT_SCREEN].name)
        elif keycode[0] == 32: # spacebar
            FW_CC_QUEUE.put("[KEY] %d" % keycode[0])

class SimulationWidget(Widget):
    fps = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SimulationWidget, self).__init__(**kwargs)
        # self.grid_x = []
        # self.grid_y = []
        self.old_window_size_x = 0
        self.old_window_size_y = 0
        self.cells = [[0 for y in range(HEIGHT)] for x in range(WIDTH+1)]
        x, y = Window.size
        self.spacing_x = x / WIDTH
        self.spacing_y = y / HEIGHT
        x = 0
        y = -1
        count = 0
        for i in range(0, len(WORLD_DATA), INTS_PER_FIELD):
            x = (i - (count * INTS_PER_FIELD) + count) % WIDTH
            count += 1
            if x % WIDTH == 0:
                y += 1
            y_inverted = HEIGHT - y - 1
            alpha = WORLD_DATA[i + 2] / 256
            g = InstructionGroup()
            g.add(Color(256, 256, 256, alpha))
            g.add(Rectangle(pos=(x * self.spacing_x, y_inverted * self.spacing_y), size=(self.spacing_x, self.spacing_y)))
            self.canvas.add(g)
            self.cells[x][y_inverted] = g

    def update_fps(self, dt):
        x, y = Window.size
        self.fps.text = "%d FPS : RES: (%d, %d)" % (round(Clock.get_fps()), x, y)

    def update(self, dt):
        with self.canvas:
            x, y = Window.size
            self.spacing_x = x / WIDTH
            self.spacing_y = y / HEIGHT
            if self.old_window_size_x != x or self.old_window_size_y != y:
                self.old_window_size_x = x
                self.old_window_size_y = y
                for x in range(WIDTH):
                    for y in range(HEIGHT):
                        val = self.cells[x][y]
                        if val != 0:
                            val.children[2].pos = (x * self.spacing_x, y * self.spacing_y)
                            val.children[2].size = (self.spacing_x, self.spacing_y)
                # self.grid_x = []
                # self.grid_y = []
                # for i in range(0, WIDTH):
                #     self.grid_x.append(Line(points=[i*self.spacing_x, 0, i*self.spacing_x, y], width=1))
                # for j in range(0, HEIGHT):
                #     self.grid_y.append(Line(points=[0, j*self.spacing_y, x, j*self.spacing_y], width=1))
            x = 0
            y = -1
            count = 0
            for i in range(0, len(WORLD_DATA), INTS_PER_FIELD):
                x = (i - (count * INTS_PER_FIELD) + count) % WIDTH
                count += 1
                if x % WIDTH == 0:
                    y += 1
                y_inverted = HEIGHT - y - 1
                value = WORLD_DATA[i + 2]
                alpha = WORLD_DATA[i + 2] / 256
                self.cells[x][y_inverted].children[0].a = alpha

class EndWidget(Widget):
    title = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(EndWidget, self).__init__(**kwargs)

class MenuWidget(Widget):
    dbg = ObjectProperty(None)
    btn_quit = ObjectProperty(None)
    tick_slider = ObjectProperty(None)
    btn_count = NumericProperty(1)

    def __init__(self, **kwargs):
        super(MenuWidget, self).__init__(**kwargs)
        self.btn_quit.on_press = self.quit
        self.btn_count = len([widget for widget in self.walk(restrict=True) if type(widget) is Button])
        self.tick_slider.bind(value=self.on_tick_slider_change)

    def on_tick_slider_change(self, instance, value):
        FW_CC_QUEUE.put("[IPS] %d" % value)

    def quit(self):
        IR_CC_QUEUE.put("[CMD] done")
        FW_CC_QUEUE.put("[CMD] done")
        App.get_running_app().stop()

    def update_dbg(self, dt):
        x, y = Window.size
        self.dbg.text = str(NUMBER)

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
    global NUMBER, CURRENT_SCREEN
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
                    change_screen("end")
        else:
            NUMBER = input

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
    if name == "end" or sm.current == "end":
        sm.transition = FadeTransition()
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

CURRENT_SCREEN = 0
GAME_BEGIN = 0
GAME_RUNNING = 1
GAME_END = 2
GAME_STOP = 3
GAME_STATE = GAME_BEGIN
NUMBER = 0
ROOT_PATH = os.path.dirname(__file__)
sm = ScreenManager()
SCREEN_LIST = [SplashScreen(name="splash"), StartScreen(name="start"), SimulationScreen(name="simulation"), EndScreen(name="end"), MenuScreen(name="menu")]
for screen in SCREEN_LIST:
    sm.add_widget(screen)
Config.set("kivy", "log_level", "warning") # one of: trace, debug, info, warning, error, critical

class AntificialApp(App):
    def __init__(self, fw_output, ir_cc_queue, fw_cc_queue, world_data, grid_resolution, player_count, grid_size):
        super(AntificialApp, self).__init__()
        global FW_OUTPUT, IR_CC_QUEUE, FW_CC_QUEUE, WORLD_DATA, WIDTH, HEIGHT, GRID_SIZE, INTS_PER_FIELD
        FW_OUTPUT = fw_output
        IR_CC_QUEUE = ir_cc_queue
        FW_CC_QUEUE = fw_cc_queue
        WORLD_DATA = world_data
        WIDTH = grid_resolution[0]
        HEIGHT = grid_resolution[1]
        GRID_SIZE = grid_size
        INTS_PER_FIELD = 4 + player_count

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
        Clock.schedule_interval(simulation_widget.update_fps, 1.0 / 1.0)
        Clock.schedule_interval(simulation_widget.update, 1.0 / 10)
        Clock.schedule_interval(menu_widget.update_dbg, 1.0 / 1.0)

        sm.bind(on_close=self._on_close)
        Window.bind(on_close=self._on_close)

        return sm

    def _on_close(self, *largs):
        IR_CC_QUEUE.put("[CMD] done")
        FW_CC_QUEUE.put("[CMD] done")
        App.get_running_app().stop()