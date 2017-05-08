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
from kivy.graphics.vertex_instructions import Ellipse, Line
from kivy.clock import Clock
from kivy.vector import Vector

Builder.load_string("""
<Ant>:
    size: 25, 25
    canvas:
        Ellipse:
            pos: self.pos
            size: self.size

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

class Ant():
    velocity = [1,1]
    eli = None

    def __init__(self, eli, velocity):
        self.velocity = velocity
        self.eli = eli

    def move(self, top, width):
        if self.eli.pos[1] < 0 or self.eli.pos[1] > top:
            self.velocity[1] *= -1
        if self.eli.pos[0] < 0:
            self.velocity[0] *= -1
        if self.eli.pos[0] > width:
            self.velocity[0] *= -1
        self.eli.pos = Vector(*self.velocity) + self.eli.pos

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
        self.ants = []
        self.grid_x = []
        self.grid_y = []
        self.grid_size = 180
        self.old_window_size_x = 0
        self.old_window_size_y = 0
        with self.canvas:
            x, y = Window.size
            if self.old_window_size_x != x or self.old_window_size_y != y:
                self.old_window_size_x = x
                self.old_window_size_y = y
                lines_x = math.ceil(x / self.grid_size) + 1
                lines_y = math.ceil(y / self.grid_size) + 1
                for i in range(0, lines_x):
                    self.grid_x.append(Line(points=[i*self.grid_size, 0, i*self.grid_size, y], width=2))
                for j in range(0, lines_y):
                    self.grid_y.append(Line(points=[0, j*self.grid_size, x, j*self.grid_size], width=2))
            for x in range(1, 2000):
                eli = Ellipse(pos=[randint(0, 1600), randint(0, 1200)], size=[10, 10])
                self.ants.append(Ant(eli=eli, velocity=[randint(-5, 5),randint(-5, 5)]))

    def update_fps(self, dt):
        x, y = Window.size
        self.fps.text = "%d FPS : RES: (%d, %d)" % (round(Clock.get_fps()), x, y)

    def update(self, dt):
        with self.canvas:
            x, y = Window.size
            if self.old_window_size_x != x or self.old_window_size_y != y:
                print("changing grid")
                self.old_window_size_x = x
                self.old_window_size_y = y
                lines_x = math.ceil(x / self.grid_size) + 1
                lines_y = math.ceil(y / self.grid_size) + 1
                self.grid_x = []
                self.grid_y = []
                for i in range(0, lines_x):
                    self.grid_x.append(Line(points=[i*self.grid_size, 0, i*self.grid_size, y], width=2))
                for j in range(0, lines_y):
                    self.grid_y.append(Line(points=[0, j*self.grid_size, x, j*self.grid_size], width=2))
        # for ant in self.ants:
        #     ant.move(top=self.top, width=self.width)

    def _keyboard_closed(self):
        print('My keyboard has been closed!')

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print('The key', keycode, 'have been pressed')
        print(' - text is %r' % text)
        print(' - modifiers are %r' % modifiers)
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
    def __init__(self, fw_output, ir_cc_queue, fw_cc_queue):
        super(AntificialApp, self).__init__()
        global pipe, ir_cc, fw_cc
        pipe = fw_output
        ir_cc = ir_cc_queue
        fw_cc = fw_cc_queue

    def build(self):
        simulation_widget = SimulationWidget()
        menu_widget = MenuWidget()
        simulation_screen.add_widget(simulation_widget)
        menu_screen.add_widget(menu_widget)

        btn_quit = Button(text='Quit')
        btn_quit.bind(on_press=menu_widget.btn_quit)
        menu_widget.add_widget(btn_quit)

        Clock.schedule_interval(simulation_widget.update, 1.0 / 30.0)
        Clock.schedule_interval(simulation_widget.update_fps, 1.0 / 20.0)
        Clock.schedule_interval(menu_widget.update_dbg, 1.0 / 20.0)
        Clock.schedule_interval(menu_widget.get_data, 1 / 2)
        return sm
