import image_recognition as ir
import framework as fw
from util import *
from multiprocessing import Process, Pipe, Queue, Array, set_start_method
from random import randint

GRID_SIZE = 15
RESOLUTION = (1920, 1080)
GRID_RESOLUTION = (int(RESOLUTION[0] / GRID_SIZE), int(RESOLUTION[1] / GRID_SIZE)) # pre-compute this
PLAYER_COUNT = 2
HOME = (int(GRID_RESOLUTION[0] / 2), int(GRID_RESOLUTION[1] / 2)) # center home for now

def init():
    ir_cc_queue = Queue() # For sending commands to sub-processes
    fw_cc_queue = Queue() # For sending commands to sub-processes
    ir_input, ir_output = Pipe() # For IPC
    fw_input, fw_output = Pipe() # Likewise
    world = fw.World(GRID_RESOLUTION, PLAYER_COUNT)
    for x in range(20):
        for y in range(20):
            f = world.get(randint(0, GRID_RESOLUTION[0]-1), randint(0, GRID_RESOLUTION[1]-1))
            f.ant_count = 100
            f.home_pheromone_level = 100
            world.set(f)
    irp = Process(target=ir.run, args=(ir_cc_queue, ir_input, GRID_RESOLUTION))
    fwp = Process(target=fw.run, args=(ir_cc_queue, fw_cc_queue, ir_output, fw_input, world, HOME))
    return irp, fwp, ir_cc_queue, fw_cc_queue, fw_output, world

if __name__ == '__main__':
    set_start_method('spawn')
    try:
        import renderer as rr
        irp, fwp, ir_cc_queue, fw_cc_queue, fw_output, world = init()
        irp.start()
        fwp.start()
        rr.AntificialApp(fw_output, ir_cc_queue, fw_cc_queue, world.data, GRID_RESOLUTION, PLAYER_COUNT, GRID_SIZE).run()
        irp.join()
        fwp.join()
    except KeyboardInterrupt as e:
        print("Shutting down...")
