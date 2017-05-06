#! /usr/bin/env python

import util
import time

RUNNING = True
TIMEOUT = 1

def shutdown():
    print("[RR] Shutting down...")

def handle_commands(cc_queue):
    try:
        cc = cc_queue.get(False)
        if cc == "done":
            util.iprint("[IR] Quit")
            global RUNNING
            RUNNING = False
    except:
        pass

def work(cc_queue, fw_output):
    while RUNNING:
        handle_commands(cc_queue)
        if fw_output.poll(TIMEOUT):
            input = fw_output.recv()
            util.iprint("[RR] Received {input}!")

# Run this from other code
def run(cc_queue, fw_output):
    try:
        print("Running RR module...")
        work(cc_queue, fw_output)
    except KeyboardInterrupt as e:
        shutdown()
