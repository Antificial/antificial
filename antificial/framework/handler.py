#! /usr/bin/env python

import util
import framework.colony as col
import framework.game as game
import time

# Management Constants
RUNNING = True
TIMEOUT = 1
IPS = 10
# Game State
GAME_BEGIN = 0
GAME_RUNNING = 1
GAME_END = 2
GAME_STOP = 3
GAME_STATE = GAME_BEGIN
GAME_DURATION = 5 # in seconds
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
    if s.startswith("[CMD]"):
        cmd = s[6:]
        if cmd == "done":
            print("[FW] Quitting")
            global RUNNING
            RUNNING = False
    elif s.startswith("[IPS]"):
        IPS = int(s[6:])

def handle_commands():
    try:
        input = FW_CC_QUEUE.get(False)
        handle_action(input)
    except:
        pass
           
def handle_pipe():
    if IR_OUTPUT.poll(TIMEOUT):
        input = IR_OUTPUT.recv()
        util.iprint("[FW] Received {input}!")
        util.iprint("[FW] Sending {input} to RR...")
        if isinstance(input, list):
            global WORLD
            WORLD.update_food(input)
         
        if isinstance(input, str):
            if input.startswith("[KEY]"):
                FW_CC_QUEUE.put(input)        
                
        # get field
        # change food
        # world set 
        # probably handle ball events here
        # analyse coordinate data and determine players
        # purge previous list of players and re-do

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
    t = time.time()
    finish_time = time.time() + GAME_DURATION
    wait_time = 1 / IPS
    while t < finish_time and RUNNING:
        t = time.time()
        start = time.perf_counter()
        handle_commands()
        handle_pipe() # update balls
        COLONY.update() # move ants
        # WORLD.decay_pheromone() # update pheromones
        end = time.perf_counter()
        proc_time = end - start
        sleep_time = wait_time - proc_time if proc_time < wait_time else 0
        time.sleep(sleep_time)

def app_loop():
    global COLONY, GAMERULES, GAME_STATE
    while RUNNING:
        handle_commands()
        COLONY = col.Colony(WORLD, HOME)
        GAMERULES = game.GameRules(COLONY)
        COLONY.init_gamerules(GAMERULES)
        handle_pipe()
        if GAME_STATE == GAME_BEGIN and RUNNING:
            print("[FW] Game State is %d" % GAME_STATE)
            FW_INPUT.send("[GAME_STATE] %d" % GAME_STATE)
            IR_CC_QUEUE.put("[GAME_STATE] %d" % GAME_STATE)
            while not poll_for_keypress(32) and RUNNING: # spacebar
                handle_commands()
                handle_pipe()
                time.sleep(0.5)
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
            # for every player:
                # FW_INPUT.send("[RESULTS] %d:%d" % (PLAYER, SCORE))
            time.sleep(1)
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
