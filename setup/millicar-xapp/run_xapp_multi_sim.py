import logging
from typing import List
from xapp_control import *
# from xapp_control_local_test import *
# import functools 
import os
import numpy as np
import transform_xml_to_dict_millicar as transform
from ctrl_msg_encoder_decoder import RicControlMessageEncoder
from millicar_pre_optimize import MillicarPreoptimize
from millicar_optimization import MillicarFormulation

_simulation_map = [
    [111, 0, 'no relay'],
    [112, 0, 'distance'],
    [113, 0, 'sinr'],
    [114, -5, 'no relay'],
    [115, -5, 'distance'],
    [116, -5, 'sinr'],
    [117, -10, 'no relay'],
    [118, -10, 'distance'],
    [119, -10, 'sinr'],
]

class XmlToDictManager:
    def __init__(self,
                 plmn: str = "111",
                 ) -> None:
        self.plmn = plmn
        self.transform = transform.XmlToDictDataTransform()
        # number of samples to take to for mean
        _sim_map_filter = list(filter(lambda _sim: str(_sim[0]) == str(plmn), _simulation_map))
        _relay_threshold = 46
        if len(_sim_map_filter) == 1:
            _relay_threshold += _sim_map_filter[0][1]
        self.preoptimize_queue = MillicarPreoptimize(peer_measurements_history_depth=5,
                                                     to_relay_threshold=_relay_threshold)
    

def send_optimized_data(socket, encoder_class:RicControlMessageEncoder):
    def send_data(ue_ids, initial_assignment, optimized_assignment, plmn):
        data_length, data_bytes = encoder_class.encode_result_plmn(ue_ids, initial_assignment, optimized_assignment, plmn)
        # we could make a check here that data length is identical to received data length from c++ function
        logging.info('Sending back the data with size ..' + str(data_length))
        send_socket(socket, data_bytes)
    return send_data

def _optimize_and_send_data(transform: XmlToDictManager, sendingDataCallback):
    plmn = transform.plmn
    ##### Optimization part
    _sim_map_filter = list(filter(lambda _sim: str(_sim[0]) == plmn, _simulation_map))
    _all_relays = []
    if len(_sim_map_filter) == 1:
        # _relay_threshold = _sim_map_filter[0][1]
        _optimization_type = _sim_map_filter[0][2]
        _formulation = MillicarFormulation(transform.preoptimize_queue)
        if _optimization_type == 'distance':
            print("Distance optimization")
            _all_relays: List[List[int]] = _formulation.optimize_closest_node()
        elif _optimization_type == 'sinr':
            print("Sinr optimization")
            _all_relays: List[List[int]] = _formulation.optimize()


    # transform data 
    _source_rntis = [_relay[0] for _relay in _all_relays]
    _dest_rntis = [_relay[1] for _relay in _all_relays]
    _relay_rntis = [_relay[2] for _relay in _all_relays]
    sendingDataCallback(_source_rntis, _dest_rntis, _relay_rntis, plmn)
    # sendingDataCallback([1,2,3,4,5], [0,1,2,2,2], [0,1,0,0,1], plmn)
    transform.transform.reset()

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
                    _collection_time, _cell_id, _plmn_id = transform.XmlToDictDataTransform.peek_header(_msg)
                    # print("Plmn id of the sender " + str(_plmn_id))
                    if (_plmn_id!= -1) & (_cell_id!= -1)& (_collection_time!= -1):
                        # find the right manager to parse data 
                        _xml_manager_filter = list(filter(lambda _xmlManager: _xmlManager.plmn == _plmn_id, _transform_list))
                        # either there exist a manager, so the filter gives only 1 element
                        if len(_xml_manager_filter) == 1:
                            _xml_manager_filter[0].transform.parse_incoming_data(_msg)
                        else:
                            # we insert a new manager 
                            _transform = XmlToDictManager(_plmn_id)
                            _transform.transform.parse_incoming_data(_msg)
                            _transform_list.append(_transform)
                            
            else:
                logging.info('Received data: ' + data_sck)
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
            # for _transform in []:
                _received_all_reports = (_transform.transform.num_of_reports != 0) & (
                            _transform.transform.num_of_received_reports == _transform.transform.num_of_reports)
                # # we could make a check here that data length is identical to received data length from c++ function
                # logging.info('Sending back the data with size ..' + str(data_length))
                # send_socket(control_sck, data_bytes)
                if _received_all_reports:
                    # insert in queue
                    _transform.preoptimize_queue.insert_measurements(_transform.transform.all_users_reports)
                    if _transform.preoptimize_queue.can_perform_optimization() & \
                        _transform.preoptimize_queue.is_need_relay_links():
                        _optimize_and_send_data(_transform, _send_encoded_data_func)
                    _transform.transform.reset()


if __name__ == '__main__':
    main()
    # _msg_encoder = RicControlMessageEncoder()
    # ue_ids = [0, 1]
    # initial_assignment = [10, 12]
    # optimized_assignment = [13, 14]
    # plmn = "111"
    # data_length, data_bytes = _msg_encoder.encode_result_plmn(ue_ids, initial_assignment, optimized_assignment, plmn)