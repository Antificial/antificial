#! /usr/bin/env python

import util
import framework.colony as col
import framework.game as game
import time

# Management Constants
RUNNING = True
TIMEOUT = 0
IPS = 15
ANT_COUNT = 300
DECAY_RATE_HOME = 1
DECAY_RATE_FOOD = 4
# Game State
GAME_BEGIN = 0
GAME_RUNNING = 1
GAME_END = 2
GAME_STOP = 3
GAME_STATE = GAME_BEGIN
GAME_DURATION = 180 # in seconds
# Game Data
COLONY = None
GAMERULES = None
WORLD = None
HOME = None
IR_CC_QUEUE = None
FW_CC_QUEUE = None
IR_OUTPUT = None
FW_INPUT = None
PLAYERS = []

def shutdown():
    print("[FW] Shutting down...")

def handle_action(s):
    global IPS, DECAY_RATE_HOME, DECAY_RATE_FOOD, GAME_DURATION, ANT_COUNT, GAME_STATE
    if s.startswith("[CMD]"):
        cmd = s[6:]
        if cmd == "done":
            print("[FW] Quitting")
            global RUNNING
            RUNNING = False
    elif s.startswith("[IPS]"):
        IPS = int(s[6:])
    elif s.startswith("[HTD]"):
        DECAY_RATE_HOME = int(s[6:])
    elif s.startswith("[FTD]"):
        DECAY_RATE_FOOD = int(s[6:])
    elif s.startswith("[GDU]"):
        GAME_DURATION = int(s[6:])
    elif s.startswith("[IAC]"):
        ANT_COUNT = int(s[6:])
    elif s.startswith("[KEY]"):
        key = int(s[6:])
        if key == 114:
            GAME_STATE = GAME_END

def handle_commands():
    try:
        while not FW_CC_QUEUE.empty():
            input = FW_CC_QUEUE.get(False)
            handle_action(input)
    except:
        pass

def handle_pipe():
    if IR_OUTPUT.poll(TIMEOUT):
        input = IR_OUTPUT.recv()
        if isinstance(input, list):
            global WORLD
            WORLD.update_food(input)

        if isinstance(input, str):
            if input.startswith("[KEY]"):
                FW_CC_QUEUE.put(input)

def poll_for_keypress(keycode):
    try:
        input = FW_CC_QUEUE.get(False)
        if input.startswith("[KEY]"):
            key = int(input[5:])
            if key == keycode:
                return True
        else:
            handle_action(input)
    except:
        pass
    return False

def game_loop():
    global IPS, GAME_DURATION
    start_time = time.time()
    t = time.time()
    finish_time = start_time + GAME_DURATION
    start_IPS = IPS
    scope_IPS = IPS
    while t < finish_time and RUNNING and GAME_STATE == GAME_RUNNING:
        if IPS != start_IPS:
            scope_IPS = IPS
            start_IPS = IPS
        finish_time = start_time + GAME_DURATION
        wait_time = 1 / scope_IPS
        t = time.time()
        start = time.perf_counter()
        handle_commands()
        handle_pipe() # update balls
        scores = COLONY.update() # move ants
        WORLD.decay_pheromones(DECAY_RATE_HOME, DECAY_RATE_FOOD) # update pheromones
        FW_INPUT.send(scores)
        end = time.perf_counter()
        proc_time = end - start
        sleep_time = wait_time - proc_time if proc_time < wait_time else 0
        if sleep_time == 0 and t % 5 < 0.1:
            actual_ips = int(1 / proc_time)
            if actual_ips + 1 < scope_IPS:
                print("[FW] Dropping ticks. Should be 1/%d but is 1/%d. Adjusting down..." % (IPS, actual_ips))
                scope_IPS = int(actual_ips) + 1
                FW_INPUT.send("[IPS] %d" % scope_IPS)
        time.sleep(sleep_time)

def app_loop():
    global COLONY, GAMERULES, GAME_STATE
    while RUNNING:
        handle_commands()
        handle_pipe()
        if GAME_STATE == GAME_BEGIN and RUNNING:
            print("[FW] Game State is %d" % GAME_STATE)
            FW_INPUT.send("[GAME_STATE] %d" % GAME_STATE)
            IR_CC_QUEUE.put("[GAME_STATE] %d" % GAME_STATE)
            while not poll_for_keypress(32) and RUNNING: # spacebar
                handle_commands()
                handle_pipe()
                time.sleep(0.5)
            COLONY = col.Colony(WORLD, HOME, ANT_COUNT)
            GAMERULES = game.GameRules(COLONY)
            COLONY.init_gamerules(GAMERULES)
            GAME_STATE = GAME_RUNNING
        if GAME_STATE == GAME_RUNNING and RUNNING:
            print("[FW] Game State is %d" % GAME_STATE)
            FW_INPUT.send("[GAME_STATE] %d" % GAME_STATE)
            IR_CC_QUEUE.put("[GAME_STATE] %d" % GAME_STATE)
            game_loop()
            GAME_STATE = GAME_END
        if GAME_STATE == GAME_END and RUNNING:
            WORLD.reset()
            print("[FW] Game State is %d" % GAME_STATE)
            FW_INPUT.send("[GAME_STATE] %d" % GAME_STATE)
            IR_CC_QUEUE.put("[GAME_STATE] %d" % GAME_STATE)
            time.sleep(10)
            GAME_STATE = GAME_BEGIN

# Run this from other code
def run(ir_cc_queue, fw_cc_queue, ir_output, fw_input, world, home):
    global WORLD, HOME, IR_CC_QUEUE, FW_CC_QUEUE, IR_OUTPUT, FW_INPUT
    IR_CC_QUEUE = ir_cc_queue
    FW_CC_QUEUE = fw_cc_queue
    IR_OUTPUT = ir_output
    FW_INPUT = fw_input
    HOME = home
    WORLD = world
    try:
        print("Running FW module...")
        app_loop()
    except KeyboardInterrupt as e:
        shutdown()
