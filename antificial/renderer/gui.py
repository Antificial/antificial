#! /usr/bin/env python

import util
import time
import math
from random import randint

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.graphics.vertex_instructions import Line, Rectangle
from kivy.graphics import Color, InstructionGroup
from kivy.clock import Clock
from kivy.vector import Vector

Builder.load_string("""
<SimulationWidget>:
    fps: fps_label
    Label:
        id: fps_label
        font_size: 70
        center_x: root.width / 2
        top: root.top - 50
        text: "00 FPS"

<MenuWidget>:
    dbg: dbg_label
    Label:
        id: dbg_label
        font_size: 70
        center_x: root.width / 2
        top: root.top - 150
        text: "---"
""")
pipe = None

def get(x, y):
    if x >= WIDTH or y >= HEIGHT:
        s = "Index %d or %d is out of bounds." % (x, y)
        raise IndexError(s)
    position = (y * HEIGHT * INTS_PER_FIELD) + (x * INTS_PER_FIELD)
    values = []
    for i in range(INTS_PER_FIELD):
        values.append(WORLD_DATA[position + i])
    return values

class MenuWidget(Widget):
    dbg = ObjectProperty(None)
    btn_quit = ObjectProperty(None)
    number = 0

    def __init__(self, **kwargs):
        super(MenuWidget, self).__init__(**kwargs)

    def btn_quit(self, dt):
        ir_cc.put("done")
        fw_cc.put("done")
        App.get_running_app().stop()

    def get_data(self, dt):
        if pipe.poll():
            self.number = pipe.recv()

    def update_dbg(self, dt):
        x, y = Window.size
        self.dbg.text = "%d" % self.number

class SimulationWidget(Widget):
    fps = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SimulationWidget, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
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
            if WORLD_DATA[i + 1] > 0:
                x = (i - (count * INTS_PER_FIELD) + count) % WIDTH
                count += 1
                if x % WIDTH == 0:
                    y += 1
                alpha = WORLD_DATA[i + 2] / 256
                g = InstructionGroup()
                g.add(Color(256, 256, 256, alpha))
                g.add(Rectangle(pos=(x * self.spacing_x, y * self.spacing_y), size=(self.spacing_x, self.spacing_y)))
                self.canvas.add(g)
                self.cells[x][y] = g

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
                if WORLD_DATA[i + 1] > 0:
                    x = (i - (count * INTS_PER_FIELD) + count) % WIDTH
                    count += 1
                    if x % WIDTH == 0:
                        y += 1
                    alpha = WORLD_DATA[i + 2] / 256
                    self.cells[x][y].children[0].a = alpha

    def _keyboard_closed(self):
        pass

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[0] == 97:
            sm.transition.direction = "right"
            sm.current = "simulation"
        elif keycode[0] == 100:
            sm.transition.direction = "left"
            sm.current = "menu"

# Declare both screens
class SimulationScreen(Screen):
    pass

class MenuScreen(Screen):
    pass

# Create the screen manager
sm = ScreenManager()
simulation_screen = SimulationScreen(name='simulation')
menu_screen = MenuScreen(name='menu')
sm.add_widget(simulation_screen)
sm.add_widget(menu_screen)

class AntificialApp(App):
    def __init__(self, fw_output, ir_cc_queue, fw_cc_queue, world_data, resolution, player_count, grid_size):
        super(AntificialApp, self).__init__()
        global pipe, ir_cc, fw_cc, WORLD_DATA, WIDTH, HEIGHT, GRID_SIZE, INTS_PER_FIELD
        pipe = fw_output
        ir_cc = ir_cc_queue
        fw_cc = fw_cc_queue
        WORLD_DATA = world_data
        WIDTH = int(resolution[0] / grid_size)
        HEIGHT = int(resolution[1] / grid_size)
        GRID_SIZE = grid_size
        INTS_PER_FIELD = 4 + player_count

    def build(self):
        simulation_widget = SimulationWidget()
        menu_widget = MenuWidget()
        simulation_screen.add_widget(simulation_widget)
        menu_screen.add_widget(menu_widget)

        btn_quit = Button(text='Quit')
        btn_quit.bind(on_press=menu_widget.btn_quit)
        menu_widget.add_widget(btn_quit)

        Clock.schedule_interval(simulation_widget.update, 1.0 / 2.0)
        Clock.schedule_interval(simulation_widget.update_fps, 1.0 / 2.0)
        Clock.schedule_interval(menu_widget.update_dbg, 1.0 / 2.0)
        Clock.schedule_interval(menu_widget.get_data, 1 / 2.0)
        return sm
