import image_recognition as ir
import framework as fw
import renderer as rr
from util import *
from multiprocessing import Process, Pipe, Queue, Array

GRID_SIZE = 15
RESOLUTION = (100, 100)
GRID_RESOLUTION = (int(RESOLUTION[0]/GRID_SIZE), int(RESOLUTION[1]/GRID_SIZE)) # pre-compute this
PLAYER_COUNT = 2
HOME = (int(GRID_RESOLUTION[0]/2), int(GRID_RESOLUTION[1]/2)) # center home for now

def init():
    ir_cc_queue = Queue() # For sending commands to sub-processes
    fw_cc_queue = Queue() # For sending commands to sub-processes
    ir_input, ir_output = Pipe() # For IPC
    fw_input, fw_output = Pipe() # Likewise
    world = fw.World(GRID_RESOLUTION, PLAYER_COUNT)
    irp = Process(target=ir.run, args=(ir_cc_queue, ir_input, RESOLUTION, GRID_SIZE))
    fwp = Process(target=fw.run, args=(ir_cc_queue, fw_cc_queue, ir_output, fw_input, world, HOME))
    return irp, fwp, ir_cc_queue, fw_cc_queue, fw_output, world

if __name__ == '__main__':
    try:
        irp, fwp, ir_cc_queue, fw_cc_queue, fw_output, world = init()
        irp.start()
        fwp.start()
        rr.AntificialApp(fw_output, ir_cc_queue, fw_cc_queue, world.data, GRID_RESOLUTION, PLAYER_COUNT, GRID_SIZE).run()
        irp.join()
        fwp.join()
    except KeyboardInterrupt as e:
        print("Shutting down...")
