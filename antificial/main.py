#! /usr/bin/env python

import image_recognition as ir
import framework as fw
import renderer as rr
from util import *
from multiprocessing import Process, Pipe, Queue
import time

def main():
    ir_cc_queue = Queue() # For sending commands to sub-processes
    fw_cc_queue = Queue() # For sending commands to sub-processes
    rr_cc_queue = Queue() # For sending commands to sub-processes
    ir_input, ir_output = Pipe() # For IPC
    fw_input, fw_output = Pipe() # Likewise
    irp = Process(target=ir.run, args=(ir_cc_queue, ir_input))
    fwp = Process(target=fw.run, args=(fw_cc_queue, ir_output, fw_input))
    rrp = Process(target=rr.run, args=(rr_cc_queue, fw_output))
    irp.start()
    fwp.start()
    rrp.start()
    try:
        for i in range(3): # loop, adminstration stuff, maybe show panel to interact with processes
            time.sleep(1)
        ir_cc_queue.put("done")
        fw_cc_queue.put("done")
        rr_cc_queue.put("done")
        # Wait for processes to terminate
        irp.join()
        fwp.join()
        rrp.join()
    except KeyboardInterrupt as e:
        print("Received CTRL+C") # Additional main process cleanup here
    print("Done!")

if __name__ == '__main__':
        main()
