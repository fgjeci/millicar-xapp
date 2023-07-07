import logging
from typing import List
from xapp_control import *
# from xapp_control_local_test import *
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

class XmlToDictManager:
    def __init__(self, plmn: str) -> None:
        self.plmn = plmn
        self.transform = transform.XmlToDictDataTransform()
    

def send_optimized_data(socket, encoder_class:RicControlMessageEncoder):
    def send_data(ue_ids, initial_assignment, optimized_assignment, plmn):
        data_length, data_bytes = encoder_class.encode_result_plmn(ue_ids, initial_assignment, optimized_assignment, plmn)
        # we could make a check here that data length is identical to received data length from c++ function
        logging.info('Sending back the data with size ..' + str(data_length))
        send_socket(socket, data_bytes)
    return send_data

def _optimize_and_send_data(plmn: str, transform: transform.XmlToDictDataTransform, sendingDataCallback):
    if (len(transform.assignments) == 0) | (len(transform.measurements) == 0) | (len(transform.gnb_resources) == 0):
        print("Not enough data to perform optimization")
        print(transform.assignments)
        print(transform.measurements)
        print("Resetting")
        transform.reset()
        # if _inter_optimizer_timer is not None:
        #     _inter_optimizer_timer.run()
        return

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

    sendingDataCallback(_pre_optimize_data.allImsi, _assignment_array_real_cell_id, _optimized_array_real_cell_id, plmn)
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

    _transform_list: List[XmlToDictManager] = []

    # _transform = transform.XmlToDictDataTransform()
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
                    # logging.info('Received data: ' + _msg)
                    _collection_time, _cell_id, _plmn_id = transform.XmlToDictDataTransform.peek_header(_msg)
                    # print("Plmn id of the sender " + str(_plmn_id))
                    if (_plmn_id!= -1) & (_cell_id!= -1)& (_collection_time!= -1):
                        # find the right manager to parse data 
                        _xml_manager_filter = list(filter(lambda _xmlManager: _xmlManager.plmn == _plmn_id,_transform_list))
                        # either there exist a manager, so the filter gives only 1 element
                        if len(_xml_manager_filter) == 1:
                            _xml_manager_filter[0].transform.parse_incoming_data(_msg)
                        else:
                            # we insert a new manager 
                            _transform = XmlToDictManager(_plmn_id)
                            _transform.transform.parse_incoming_data(_msg)
                            _transform_list.append(_transform)
                            
            else:
                # logging.info('Received data: ' + data_sck)
                _collection_time, _cell_id, _plmn_id = transform.XmlToDictDataTransform.peek_header(data_sck)
                # print("Plmn id of the sender " + str(_plmn_id))
                if (_plmn_id!= -1) & (_cell_id!= -1)& (_collection_time!= -1):
                    # find the right manager to parse data 
                    _xml_manager_filter = list(filter(lambda _xmlManager: _xmlManager.plmn == _plmn_id,_transform_list))
                    # either there exist a manager, so the filter gives only 1 element
                    if len(_xml_manager_filter) == 1:
                        _xml_manager_filter[0].transform.parse_incoming_data(data_sck)
                    else:
                        # we insert a new manager 
                        _transform = XmlToDictManager(_plmn_id)
                        _transform.transform.parse_incoming_data(data_sck)
                        _transform_list.append(_transform)

                    # _transform.parse_incoming_data(data_sck)
            # have to decide what to do next; when to start optimizing
            # one option might be to wait for a certain time and eventually start doing the optimization
            # optimize after 10 ms and send the result
            # having a single report we can optimize directly as there is only one set of data
            for _transform in _transform_list:
                # data_length, data_bytes = _msg_encoder.encode_result_plmn([12, 13], [7,8], [7,8], "111")
                # # we could make a check here that data length is identical to received data length from c++ function
                # logging.info('Sending back the data with size ..' + str(data_length))
                # send_socket(control_sck, data_bytes)
                if _transform.transform.can_perform_optimization():
                    print("Can perform optimization with data for plmn " + str(_transform.plmn))
                    print(_transform.transform.gnb_resources)
                    print(_transform.transform.assignments)
                    print(_transform.transform.measurements)
                    _optimize_and_send_data(_transform.plmn, _transform.transform, _send_encoded_data_func)


if __name__ == '__main__':
    main()
    # _msg_encoder = RicControlMessageEncoder()
    # ue_ids = [0, 1]
    # initial_assignment = [10, 12]
    # optimized_assignment = [13, 14]
    # plmn = "111"
    # data_length, data_bytes = _msg_encoder.encode_result_plmn(ue_ids, initial_assignment, optimized_assignment, plmn)