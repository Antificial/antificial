#! /usr/bin/env python

import util
import time

RUNNING = True

def shutdown():
    print("[IR] Shutting down...")

def handle_commands(cc_queue):
    try:
        cc = cc_queue.get(False)
        if cc == "done":
            util.iprint("[IR] Quit")
            global RUNNING
            RUNNING = False
    except:
        pass

def work(cc_queue, ir_input):
    count = 0
    while RUNNING:
        handle_commands(cc_queue)
        util.iprint("[IR] Sending number {count} to FW...")
        ir_input.send(count)
        count += 1
        time.sleep(1.0)

# Run this from other code
def run(cc_queue, ir_input):
    try:
        print("Running IR module...")
        work(cc_queue, ir_input)
    except KeyboardInterrupt as e:
        shutdown()
