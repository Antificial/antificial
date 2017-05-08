import image_recognition as ir
import framework as fw
import renderer as rr
from util import *
from multiprocessing import Process, Pipe, Queue

def init():
    global ir_cc_queue, fw_cc_queue, fw_output, irp, fwp
    ir_cc_queue = Queue() # For sending commands to sub-processes
    fw_cc_queue = Queue() # For sending commands to sub-processes
    ir_input, ir_output = Pipe() # For IPC
    fw_input, fw_output = Pipe() # Likewise
    irp = Process(target=ir.run, args=(ir_cc_queue, ir_input))
    fwp = Process(target=fw.run, args=(fw_cc_queue, ir_output, fw_input))
    irp.start()
    fwp.start()

if __name__ == '__main__':
    init()
    rr.AntificialApp(fw_output, ir_cc_queue, fw_cc_queue).run()
    irp.join()
    fwp.join()
