import logging
from xapp_control import *
# import functools 
import os
import numpy as np
import transform_xml_to_dict_single_report as transform
import time, threading
# from threading import Thread
from ipso.trasform_pre_optimize import EfAssignDataPreparation
from ipso.greddy_formulation import GreedyFormulation
from ipso.ipso_formulation import IntegerPSO
from ctrl_msg_encoder_decoder import RicControlMessageEncoder
from analysis_time import OptimizerTimer, InterOptimizationTimer
import analysis_time

def send_optimized_data(socket, encoder_class:RicControlMessageEncoder):
    # @functools.wraps(socket, encoder_class)
    def send_data(ue_ids, initial_assignment, optimized_assignment):
        data_length, data_bytes = encoder_class.encode_result(ue_ids, initial_assignment, optimized_assignment)
        # we could make a check here that data length is identical to received data length from c++ function
        logging.info('Sending back the data with size ..' + str(data_length))
        send_socket(socket, data_bytes)
    return send_data

def _optimize_and_send_data(_inter_optimizer_timer: InterOptimizationTimer, transform: transform.XmlToDictDataTransform, sendingDataCallback):
# def _optimize_and_send_data(transform: transform.XmlToDictDataTransform, sendingDataCallback):
    if (len(transform.assignments) == 0) | (len(transform.measurements) == 0) | (len(transform.gnb_resources) == 0):
        print("Not enough data to perform optimization")
        print(transform.assignments)
        print(transform.measurements)
        print("Resetting")
        transform.reset()
        # if _inter_optimizer_timer is not None:
        #     _inter_optimizer_timer.run()
        return

    
    # print(transform.assignments)
    # print(transform.measurements)
    # print(transform.gnb_resources)
    # if transform.is_data_updated():
    #     print("Data cannot be used for optimization")
    #     return
    _pre_optimize_data = EfAssignDataPreparation(assignments=transform.assignments, 
                                                            measurements=transform.measurements,
                                                            gnbAvailableResources=transform.gnb_resources)
    
    print("Imsi list")
    print(_pre_optimize_data.allImsi)
    print("Preassignment list")
    print(_pre_optimize_data.assignmentsArray)
    
    # Greedy optimization
    greedy = GreedyFormulation(allUsers=_pre_optimize_data.allImsi, mcsTable=_pre_optimize_data.mcsTable,
                                          gnbResources=_pre_optimize_data.gnbResources, startingAssignment=_pre_optimize_data.assignmentsTable)
    _optimized_assign_list = greedy.optimize()

    #IPSO Optimization
    # n_particles = 10
    # dimensions = _pre_optimize_data.nrEfs
    # options = {'c1': 0.5, 'c2': 0.3, 'w': 0.3, 'k':1, 'p':2}
    # _number_possible_dest_cells = len(_pre_optimize_data.gnbResources)
    # init_pos = np.random.randint(_number_possible_dest_cells, size=(n_particles, dimensions))
    # ipso = IntegerPSO(n_particles, dimensions, options=options, 
    #                   velocity_clamp=(-_number_possible_dest_cells, _number_possible_dest_cells), init_pos=init_pos)
    # cost, pos_ind = ipso.optimize(_pre_optimize_data.cost_function, iters=100)
    # position shall contain cell index
    
    print("Optimized assignment")
    print(_optimized_assign_list)
    _assignment_array_real_cell_id = [_pre_optimize_data.allCells[_assign] for _assign in _pre_optimize_data.assignmentsArray]
    _optimized_array_real_cell_id = [_pre_optimize_data.allCells[_opt] for _opt in _optimized_assign_list]

#     # return the resulting of optimization
#     # return  _pre_optimize_data.allImsi, _pre_optimize_data.assignmentsArray, _optimized_assign_list
    # sendingDataCallback(_pre_optimize_data.allImsi, _pre_optimize_data.assignmentsArray, _optimized_assign_list)
    sendingDataCallback(_pre_optimize_data.allImsi, _assignment_array_real_cell_id, _optimized_array_real_cell_id)
    #reseting data for the next stage
    transform.reset()

_OPTIMIZATION_TIME = 10 # seconds
_INTER_OPTIMIZATION_TIME = 30 # seconds

def main():
    _report_filename = "/home/ef-xapp/report.csv"
    # configure logger and console output
    logging_filename = os.path.join(os.getcwd(), 'report.log')
    # logging_filename = '/home/ef-xapp/xapp-logger.log' # os.path.join(os.getcwd(), )
    logging.basicConfig(level=logging.DEBUG, filename=logging_filename, filemode='a',
                        format='%(asctime)-15s %(levelname)-8s %(message)s')
    logger = logging.getLogger('')
    # logger.handlers.clear()
    # to avoid propagating logger to root
    logger.propagate = False
    formatter = logging.Formatter('%(asctime)-15s %(levelname)-8s %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)
    control_sck = open_control_socket(4200)

    _transform = transform.XmlToDictDataTransform()
    _msg_encoder = RicControlMessageEncoder()

    # global _inter_optimizer_timer
    # _inter_optimizer_timer = None

    # global _optimizer_timer
    # _optimizer_timer = None

    # _optimizer_timer = OptimizerTimer(interval=_OPTIMIZATION_TIME, function=_optimize_and_send_data,
    #                                   inter_optimizer_timer=_inter_optimizer_timer, args=(_inter_optimizer_timer, _transform, send_optimized_data(control_sck, _msg_encoder)))
    
    # _inter_optimizer_timer = InterOptimizationTimer(interval=_INTER_OPTIMIZATION_TIME, optimization_timer=_optimizer_timer, args=None)

    # _optimizer_timer.inter_optimizer_timer = _inter_optimizer_timer

    # _optimizer_timer.start()
    # _inter_optimizer_timer.start()

    # _optimizer_timer.reset_timer()
    # _inter_optimizer_timer.reset_timer()

    _send_encoded_data_func = send_optimized_data(control_sck, _msg_encoder)


    while True:
        data_sck = receive_from_socket(control_sck, _msg_encoder)

        if len(data_sck) <= 0:
            if len(data_sck) == 0:
                continue
            else:
                logging.info('Negative value for socket')
                break
        else:
            # logging.info('Received data')
            
            # appending the data to the tranformer
            if isinstance(data_sck, list):
                for _msg in data_sck:
                    logging.info('Received data: ' + _msg)
                    _transform.parse_incoming_data(_msg)
            else:
                logging.info('Received data: ' + data_sck)
                _transform.parse_incoming_data(data_sck)
            # have to decide what to do next; when to start optimizing
            # one option might be to wait for a certain time and eventually start doing the optimization
            # optimize after 10 ms and send the result
            # having a single report we can optimize directly as there is only one set of data
            
            if _transform.can_perform_optimization():
                print("Can perform optimization with data")
                print(_transform.gnb_resources)
                print(_transform.assignments)
                print(_transform.measurements)
                _optimize_and_send_data(None, _transform, _send_encoded_data_func)
            # if (_transform.num_of_reports != 0) & (_transform.num_of_received_reports == _transform.num_of_reports):
            #     _send_encoded_data_func([10,20,30], [1,2,3], [0,1,1])
            #     _transform.reset()

            # if not _inter_optimizer_timer.finished.is_set():
            #     if not _optimizer_timer.finished.is_set():
            #         _optimizer_timer.reset_timer()
            #         _optimizer_timer.run()
            # else:
            #     _optimizer_timer.reset_timer()
            #     _optimizer_timer.run()


if __name__ == '__main__':
    main()

