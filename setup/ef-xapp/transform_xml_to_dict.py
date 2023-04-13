from typing import Mapping, Tuple

import xmltodict
from functools import reduce
import operator
import os
import re
# import asn1tools

_MAIN_TAG = ["E2AP-PDU"]
_MESSAGE_PART = ['E2SM-KPM-IndicationMessage', 'indicationMessage-Format1']
_HEADER_PART = ['E2SM-KPM-IndicationHeader', 'indicationHeader-Format1']

_PM_CONTAINERS = ['pm-Containers']
_LIST_OF_MATCHED_UES = ['list-of-matched-UEs', 'PerUE-PM-Item']

_HEADER_COLLECTION_START_TIME = ['collectionStartTime']
_HEADER_CELL_ID = [['id-GlobalE2node-ID', 'gNB', 'global-gNB-ID', 'gnb-id', 'gnb-ID'],
                   ['id-GlobalE2node-ID', 'eNB', 'global-eNB-ID', 'eNB-ID', 'macro-eNB-ID'],]
_HEADER_PLMN_ID = [['id-GlobalE2node-ID', 'gNB', 'global-gNB-ID', 'plmn-id'],
                   ['id-GlobalE2node-ID', 'eNB', 'global-eNB-ID', 'plmn-id'],]

_PM_CONTAINERS_UE_ID = ['ueId']
_PM_CONTAINERS_LIST_PM_INFORMATION = ['list-of-PM-Information', 'PM-Info-Item']
_PM_INFO_ITEM_TYPE = ['pmType', 'measName']
_PM_INFO_ITEM_VALUE = ['pmVal']

_RRC_SERVING_CELL_PATH = ['valueRRC', 'servingCellMeasurements', 'nr-measResultServingMOList', 'MeasResultServMO']
_RRC_SERVING_CELL_ID_PATH = ['servCellId']
_RRC_SERVING_CELL_SINR_PATH = ['measResultServingCell', 'measResult', 'cellResults', 'resultsSSB-Cell', 'sinr']
_RRC_SERVING_PHYSICAL_CELL_ID_PATH = ['measResultServingCell', 'physCellId']

_RRC_NEIGHBOR_CELL_PATH = ['valueRRC', 'measResultNeighCells', 'measResultListNR', 'MeasResultNR']
_RRC_NEIGHBOR_CELL_ID_PATH = ['physCellId']
_RRC_NEIGHBOR_CELL_SINR_PATH = ['measResult', 'cellResults', 'resultsSSB-Cell', 'sinr']

_JSON_USER_MEASUREMENTS = 'userMeasurements'
_JSON_USER_ASSIGNMENTS = 'userAssignments'
_JSON_CELL_ID = "cellId"
_JSON_MEASUREMENT = "meas"
_JSON_SINR = "sinr"
_JSON_IMSI = "imsi"


class XmlToDictDataTransform:
    def __init__(self):
        # self.data = {}
        self.assignments = []
        self.measurements = []
        self.gnb_resources = []
        self.buffer = []

    def reset(self):
        # self.data = {}
        self.assignments = []
        self.measurements = []
        self.gnb_resources = []
    
    def append_msg(self, msg: str):
        if self._start_new_msg:
            self._buffer += msg
            if msg[-11:] == "</E2AP-PDU>":
                self._start_new_msg = False
                _complete_msg = self._buffer
                self._buffer = ""
                self.parse_incoming_data(_complete_msg)
        else:
            if msg[:10] == "<E2AP-PDU>":
                # new message
                self._start_new_msg = True
                self._buffer += msg

    def parse_incoming_data(self, xml_string: str):
        _data = xmltodict.parse(xml_string)
        _input_dict = reduce(operator.getitem, _MAIN_TAG, _data)
        # print(_input_dict)
        _header_collection_time, _header_cell_id, _header_plmn_id = self.parse_header(_input_dict)
        _cell_id_int = -1
        # print(_header_cell_id)
        try:
            _cell_id_int =  int(bytes.fromhex(_header_cell_id).split(b'\x00')[0], 16)
        except ValueError:
            _cell_id_int = int(bytes(int(_header_cell_id[i: i + 8], 2) for i in range(0, len(_header_cell_id), 8)).split(b'\x00')[0])
        try:
            _header_plmn_id = bytes.fromhex(_header_plmn_id).decode('utf-8')
        except ValueError:
            pass
        try:
            _header_collection_time = int(_header_collection_time, 16)
        except ValueError:
            pass

        # print(_header_collection_time, _cell_id_int, _header_plmn_id)
        self.parse_message(_input_dict, _cell_id_int)

    def parse_header(self, input_dict: Mapping):
        _header = reduce(operator.getitem, _HEADER_PART, input_dict)
        _collection_time = reduce(operator.getitem, _HEADER_COLLECTION_START_TIME, _header)
        _cell_id = -1
        for _header_cell_id_path in _HEADER_CELL_ID:
            try:
                _cell_id = str(reduce(operator.getitem, _header_cell_id_path, _header))
                # remove all tabs, whitespaces and new lines
                _cell_id = re.sub(r"[\\n\t\s\n]*", "", _cell_id)
            except KeyError:
                pass
        # print(_cell_id)
        _plmn_id = -1
        for _header_plmn_id_path in _HEADER_PLMN_ID:
            try:
                _plmn_id = reduce(operator.getitem, _header_plmn_id_path, _header)
            except KeyError:
                pass
        # print(_cell_id, _plmn_id, _collection_time)
        return _collection_time, _cell_id, _plmn_id

    def parse_message(self, input_dict: Mapping, cell_id: int):
        
        _message_dict = reduce(operator.getitem, _MESSAGE_PART, input_dict)
        # try:
        _matched_ues_dict = reduce(operator.getitem, _LIST_OF_MATCHED_UES, _message_dict)
        _cell_assignments = self._get_cell_assignments(_matched_ues_dict, cell_id)
        self.assignments.append(_cell_assignments)
        _cell_measurements = self._get_cell_measurements(_matched_ues_dict, cell_id)
        self.measurements.append(_cell_measurements)

        print("Assignments")
        print(self.assignments)
        print("Measurements")
        print(self.measurements)

        try:
            _pm_contanines = reduce(operator.getitem, _PM_CONTAINERS_LIST_PM_INFORMATION, _message_dict)
            _pm_cont_list = self._get_pm_information(_pm_contanines)
            print("Pm container")
            print(_pm_cont_list)
        except KeyError:
            pass    

    def _get_cell_assignments(self, input_dict: Mapping, cell_id: int) -> Mapping:
        _user_assignment_list = []
        # print("Cell Assignment")
        # print(input_dict)
        if isinstance(input_dict, dict):
            _user_assignments = self._get_single_user_assignment(input_dict)
            if len(_user_assignments) == 1:
                _user_assignment_list.append(_user_assignments[0])
        else:
            for matched_ue_dict in input_dict:
                _user_assignments = self._get_single_user_assignment(matched_ue_dict)

                if len(_user_assignments) == 1:
                    _user_assignment_list.append(_user_assignments[0])
        return {_JSON_CELL_ID: cell_id, _JSON_USER_ASSIGNMENTS: _user_assignment_list}

    def _get_cell_measurements(self, input_dict: Mapping, cell_id: int) -> Mapping:
        _user_measurement_list = []
        # print(input_dict)
        
        if isinstance(input_dict, dict):
            _user_measurements = self._get_single_user_measurements(input_dict)
            if len(_user_measurements) == 1:
                _user_measurement_list.append(_user_measurements[0])
        else:
            for matched_ue_dict in input_dict:
                _user_measurements = self._get_single_user_measurements(matched_ue_dict)
                if len(_user_measurements) == 1:
                    _user_measurement_list.append(_user_measurements[0])
        # print(_user_measurement_list)
        # 1/0
        return {_JSON_CELL_ID: cell_id, _JSON_USER_MEASUREMENTS: _user_measurement_list}

    def _get_single_user_assignment(self, input_dict: Mapping) -> Tuple[int, int]:
        _users_assignment_list = []
        try:
            ue_id = reduce(operator.getitem, _PM_CONTAINERS_UE_ID, input_dict)
            ue_id = int(bytes.fromhex(str(ue_id))) # binary to int conversion
            _list_pm_info_dict = reduce(operator.getitem, _PM_CONTAINERS_LIST_PM_INFORMATION, input_dict)
            if isinstance(_list_pm_info_dict, dict):
                _name_field = reduce(operator.getitem, _PM_INFO_ITEM_TYPE, _list_pm_info_dict)
                _single_data_dict = reduce(operator.getitem, _PM_INFO_ITEM_VALUE, _list_pm_info_dict)
                _assign_list = self._get_serving_cell_sinr(_single_data_dict)
                if (_assign_list[0] > -1) & (_assign_list[1] > -1):
                    _users_assignment_list.append({_JSON_IMSI: ue_id, _JSON_SINR: _assign_list[1]})
            else:
                for _pm_info_dict in _list_pm_info_dict:
                    _name_field = reduce(operator.getitem, _PM_INFO_ITEM_TYPE, _pm_info_dict)
                    _single_data_dict = reduce(operator.getitem, _PM_INFO_ITEM_VALUE, _pm_info_dict)
                    _assign_list = self._get_serving_cell_sinr(_single_data_dict)
                    if (_assign_list[0] > -1) & (_assign_list[1] > -1):
                        _users_assignment_list.append({_JSON_IMSI: ue_id, _JSON_SINR: _assign_list[1]})
            if len(_users_assignment_list) < 2:
                return _users_assignment_list
        except KeyError:
            pass
        return []

    # Returns the measurement for that user if it exist in the branch for not more that 1 time
    # otherwise it returns an empty list
    def _get_single_user_measurements(self, input_dict: Mapping) -> list:
        # print(input_dict)
        # 1/0
        try:
            ue_id = reduce(operator.getitem, _PM_CONTAINERS_UE_ID, input_dict)
            # hexagonal to string
            ue_id = int(bytes.fromhex(ue_id).decode('utf-8'))
            _list_pm_info_dict = reduce(operator.getitem, _PM_CONTAINERS_LIST_PM_INFORMATION, input_dict)
            _users_measurement_list = []
            if isinstance(_list_pm_info_dict, dict):
                _name_field = reduce(operator.getitem, _PM_INFO_ITEM_TYPE, _list_pm_info_dict)
                _single_data_dict = reduce(operator.getitem, _PM_INFO_ITEM_VALUE, _list_pm_info_dict)
                _meas_list = self._get_neighbor_cell_sinr_measurements(_single_data_dict)
                if len(_meas_list) > 0:
                    _users_measurement_list.append({_JSON_IMSI: ue_id, _JSON_MEASUREMENT: _meas_list})

            else:
                for _pm_info_dict in _list_pm_info_dict:
                    _name_field = reduce(operator.getitem, _PM_INFO_ITEM_TYPE, _pm_info_dict)
                    _single_data_dict = reduce(operator.getitem, _PM_INFO_ITEM_VALUE, _pm_info_dict)
                    _meas_list = self._get_neighbor_cell_sinr_measurements(_single_data_dict)
                    if len(_meas_list) > 0:
                        _users_measurement_list.append({_JSON_IMSI: ue_id, _JSON_MEASUREMENT: _meas_list})
            if len(_users_measurement_list) < 2:
                return _users_measurement_list
        except KeyError:
            pass
        return []

    def _get_serving_cell_sinr(self, input_dict: Mapping) -> Tuple[int, float]:
        # print(input_dict)
        # check initially we are seeing serving cell data
        
        if (_RRC_SERVING_CELL_PATH[1] not in input_dict[_RRC_SERVING_CELL_PATH[0]].keys()):
            return -1, -1
        try:
            _sub_dict = reduce(operator.getitem, _RRC_SERVING_CELL_PATH, input_dict)
            _serving_cell_id = reduce(operator.getitem, _RRC_SERVING_CELL_ID_PATH, _sub_dict)
            _phy_serving_cell_id = reduce(operator.getitem, _RRC_SERVING_PHYSICAL_CELL_ID_PATH, _sub_dict)
            _sinr_serving_cell_id = reduce(operator.getitem, _RRC_SERVING_CELL_SINR_PATH, _sub_dict)
            # print(_serving_cell_id, _sinr_serving_cell_id)
            return int(_serving_cell_id), float(_sinr_serving_cell_id)
        except (KeyError, TypeError):
            # means we cannot find the path in the dictionary
            print("Error in parsing data")
            print(input_dict)
            1/0
        return -1, -1

    def _get_neighbor_cell_sinr_measurements(self, input_dict: Mapping) -> list:
        _list_of_measurements = []
        if (_RRC_NEIGHBOR_CELL_PATH[1] not in input_dict[_RRC_NEIGHBOR_CELL_PATH[0]].keys()):
            return []
        # print(input_dict)
        # 1/0
        _sub_dict_neigh = reduce(operator.getitem, _RRC_NEIGHBOR_CELL_PATH, input_dict)
        try:
            if isinstance(_sub_dict_neigh, dict):
                # means we have only one measurements and not a list of measurements
                _phy_neigh_cell_id = int(reduce(operator.getitem, _RRC_NEIGHBOR_CELL_ID_PATH, _sub_dict_neigh))
                _phy_neigh_sinr = float(reduce(operator.getitem, _RRC_NEIGHBOR_CELL_SINR_PATH, _sub_dict_neigh))
                _list_of_measurements.append({_JSON_CELL_ID: _phy_neigh_cell_id, _JSON_SINR: _phy_neigh_sinr})
            else:
                for _single_dict in _sub_dict_neigh:
                    _phy_neigh_cell_id = int(reduce(operator.getitem, _RRC_NEIGHBOR_CELL_ID_PATH, _single_dict))
                    _phy_neigh_sinr = float(reduce(operator.getitem, _RRC_NEIGHBOR_CELL_SINR_PATH, _single_dict))
                    _list_of_measurements.append({_JSON_CELL_ID: _phy_neigh_cell_id, _JSON_SINR: _phy_neigh_sinr})
            # return _list_of_measurements
        except (KeyError, TypeError):
            # means we cannot find the path in the dictionary
            print("Error in parsing data")
        return _list_of_measurements

    def _get_single_pm_information(self, input_dict: Mapping) -> Tuple[str, str, float]:
        name_field = reduce(operator.getitem, _PM_INFO_ITEM_TYPE, input_dict)
        _single_data_dict = reduce(operator.getitem, _PM_INFO_ITEM_VALUE, input_dict)
        _data_type_key = list(_single_data_dict.keys())
        if (len(_data_type_key)!=1):
            # shouldn't happem
            return ("", "", -1)
        # if name_field == 'valueRRC':
        #     _assign_list = float(self._get_serving_cell_sinr(_single_data_dict))
        #     if (_assign_list[0] > -1) & (_assign_list[1] > -1):
        #         return (_JSON_SINR, 'valueRRC', _assign_list[1])
        #     else:
        #         return ("", 'valueRRC', -1)
        elif _data_type_key[0] == 'valueInt':
            return (name_field, 'valueInt', int(reduce(operator.getitem, ['valueInt'], _single_data_dict)))
        elif _data_type_key[0] == 'valueReal':
            return (name_field, 'valueReal', float(reduce(operator.getitem, ['valueInt'], _single_data_dict)))
        else:
            return ("", "", -1)
    
    # direct encoding data to the data structure
    def _get_pm_information(self, input_dict: Mapping) -> list:
        _pm_containers_list = []
        if isinstance(input_dict, dict):
            _single_pm_value = self._get_single_pm_information(input_dict)
            if (_single_pm_value[2] != -1):
                _pm_containers_list.append({_single_pm_value[0]: _single_pm_value[2]})
        else:
            for _pm_info_dict in input_dict:
                _single_pm_value = self._get_single_pm_information(_pm_info_dict)
                if (_single_pm_value[2] != -1):
                    _pm_containers_list.append({_single_pm_value[0]: _single_pm_value[2]})
        return _pm_containers_list

    
        


# if __name__ == '__main__':
#     _transformer = XmlToDictDataTransform()
#     # print(os.getcwd())
#     _filename = 'xapp-logger.log'
#     _dir = '.'
#     _complete_msg = ""
#     _tmp_msg = ""
#     _start_new_msg = False
#     with open(os.path.join(_dir, _filename)) as _file:
#     # with open(_filename) as _file:
#         lines = _file.readlines()
#         for line in lines:
#             _split_line = line.split("'")
#             # check in start of a new message
#             if len(_split_line)==3:
#                 if _start_new_msg:
#                     _tmp_msg += _split_line[1]
#                     if _split_line[1][-11:] == "</E2AP-PDU>":
#                         _start_new_msg=False
#                         _complete_msg = _tmp_msg
#                         _tmp_msg = ""
#                         # code to call the msg decodification
#                         # print("\n\n")
#                         # print(_complete_msg)
#                         # print("\n\n")
#                         _transformer.parse_incoming_data(_complete_msg)
#                 else: 
#                     if (_split_line[1][:10] == "<E2AP-PDU>"):
#                         # new message
#                         _start_new_msg = True
#                         _tmp_msg += _split_line[1]
    
#     print(_transformer.assignments)
    # with open(os.path.join(os.getcwd(), 'setup/ef-xapp/filexml.xml')) as f:
    #     lines = f.readlines()
    #     _strip_list = ''.join([re.sub(r"[\t\s\n]*", "", _line) for _line in lines])
    #     _transformer.parse_incoming_data(_strip_list)