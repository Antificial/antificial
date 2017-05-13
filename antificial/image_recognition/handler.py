#! /usr/bin/env python

import util
import time

RUNNING = True
GAME_BEGIN = 0
GAME_RUNNING = 1
GAME_END = 2
GAME_STOP = 3
GAME_STATE = GAME_BEGIN

def shutdown():
    print("[IR] Shutting down...")

def handle_action(s):
    if s.startswith("[CMD]"):
        cmd = s[6:]
        if cmd == "done":
            print("[IR] Quitting")
            global RUNNING
            RUNNING = False
    elif s.startswith("[GAME_STATE]"):
        global GAME_STATE
        GAME_STATE = int(s[12:])

def handle_commands():
    try:
        input = CC_QUEUE.get(False)
        handle_action(input)
    except:
        pass

def work():
    count = 0
    while RUNNING:
        handle_commands()
        if GAME_STATE == GAME_BEGIN:
            time.sleep(1)
        if GAME_STATE == GAME_RUNNING:
            util.iprint("[IR] Sending number {count} to FW...")
            IR_INPUT.send(count)
            count += 1
            time.sleep(1.0)
        if GAME_STATE == GAME_END:
            time.sleep(1)

# Run this from other code
def run(cc_queue, ir_input):
    global CC_QUEUE, IR_INPUT
    CC_QUEUE = cc_queue
    IR_INPUT = ir_input
    try:
        print("Running IR module...")
        work()
    except KeyboardInterrupt as e:
        shutdown()
