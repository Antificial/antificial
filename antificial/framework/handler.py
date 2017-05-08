#! /usr/bin/env python

import util
import framework.colony as colony
import time

RUNNING = True
TIMEOUT = 1

def shutdown():
    print("[FW] Shutting down...")

def handle_commands(cc_queue):
    try:
        cc = cc_queue.get(False)
        if cc == "done":
            util.iprint("[FW] Quit")
            global RUNNING
            RUNNING = False
    except:
        pass

def work(cc_queue, ir_output, fw_input):
    while RUNNING:
        handle_commands(cc_queue)
        if ir_output.poll(TIMEOUT):
            input = ir_output.recv()
            util.iprint("[FW] Received {input}!")
            util.iprint("[FW] Sending {input} to RR...")
            fw_input.send(input)

# Run this from other code
def run(cc_queue, ir_output, fw_input):
    try:
        print("Running FW module...")
        work(cc_queue, ir_output, fw_input)
    except KeyboardInterrupt as e:
        shutdown()
