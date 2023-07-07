import xml
from typing import Mapping, List, Union, Tuple

import xmltodict
from functools import reduce
import operator
import os
import re

# _MAIN_TAG = ["E2AP-PDU"]
_MAIN_TAG = ["message"]
_MESSAGE_PART = ['E2SM-KPM-IndicationMessage', 'indicationMessage-Format1']
_HEADER_PART = ['E2SM-KPM-IndicationHeader', 'indicationHeader-Format1']

_PM_CONTAINERS = ['pm-Containers']
_LIST_OF_MATCHED_UES = ['list-of-matched-UEs', 'PerUE-PM-Item']

_HEADER_COLLECTION_START_TIME = ['collectionStartTime']
_HEADER_CELL_ID = [['id-GlobalE2node-ID', 'gNB', 'global-gNB-ID', 'gnb-id', 'gnb-ID'],
                   ['id-GlobalE2node-ID', 'eNB', 'global-eNB-ID', 'eNB-ID', 'macro-eNB-ID'], ]
_HEADER_PLMN_ID = [['id-GlobalE2node-ID', 'gNB', 'global-gNB-ID', 'plmn-id'],
                   ['id-GlobalE2node-ID', 'eNB', 'global-eNB-ID', 'plmn-id'],
                   ['id-GlobalE2node-ID', 'eNB', 'global-eNB-ID', 'pLMN-Identity'],]

_CELL_OBJECT_ID = ['cellObjectID']

_PM_CONTAINERS_UE_ID = ['ueId']
_PM_CONTAINERS_LIST_PM_INFORMATION = ['list-of-PM-Information', 'PM-Info-Item']
_PM_INFO_ITEM_TYPE = ['pmType', 'measName']
_PM_INFO_ITEM_VALUE = ['pmVal']

_RRC_SERVING_CELL_PATH = ['valueRRC', 'servingCellMeasurements', 'nr-measResultServingMOList', 'MeasResultServMO']
_RRC_SERVING_CELL_ID_PATH = ['servCellId']
_RRC_SERVING_CELL_SINR_PATH = ['measResultServingCell', 'measResult', 'cellResults', 'resultsSSB-Cell', 'sinr']
_RRC_SERVING_CELL_MCS_PATH = ['measResultServingCell', 'measResult', 'cellResults', 'resultsSSB-Cell', 'mcs']
_RRC_SERVING_PHYSICAL_CELL_ID_PATH = ['measResultServingCell', 'physCellId']

_RRC_NEIGHBOR_CELL_PATH = ['valueRRC', 'measResultNeighCells', 'measResultListNR', 'MeasResultNR']
_RRC_NEIGHBOR_CELL_ID_PATH = ['physCellId']
_RRC_NEIGHBOR_CELL_SINR_PATH = ['measResult', 'cellResults', 'resultsSSB-Cell', 'sinr']
_RRC_NEIGHBOR_CELL_MCS_PATH = ['measResult', 'cellResults', 'resultsSSB-Cell', 'mcs']

_JSON_USER_MEASUREMENTS = 'userMeasurements'
_JSON_USER_ASSIGNMENTS = 'userAssignments'
_JSON_CELL_ID = "cellId"
_JSON_MEASUREMENT = "meas"
_JSON_SINR = "sinr"
_JSON_MCS = "mcs"
_JSON_IMSI = "imsi"
_JSON_GNB_USER_RESOURCES = "gnbResources"

_UE_USED_PRB_FIELD_NAME = 'RRU.PrbUsedDl.UEID'

def _build_single_pm_info_item(meas_name:str, value: Union[int, float]) -> Mapping:
    _pm_value_data_type = "valueInt" if isinstance(value, int) else "valueReal"
    _pm_type = {_PM_INFO_ITEM_TYPE[0]: {_PM_INFO_ITEM_TYPE[1]: meas_name}}
    _pm_value = {_PM_INFO_ITEM_VALUE[0]: {_pm_value_data_type: value}}
    return _pm_type | _pm_value

def _build_per_ue_pm_item(ueId: int, destination_cell: int):
    _list_pm_information = {_PM_CONTAINERS_LIST_PM_INFORMATION[0]:
    {_PM_CONTAINERS_LIST_PM_INFORMATION[1]: _build_single_pm_info_item("Destination", destination_cell)}}
    return {_PM_CONTAINERS_UE_ID[0]: ueId} | _list_pm_information

def _build_per_cell_item(ue_ids: List[int], destination_cell: int):
    return {_LIST_OF_MATCHED_UES[0]: {_LIST_OF_MATCHED_UES[1]:
  [_build_per_ue_pm_item(ue_id, destination_cell) for ue_id in ue_ids]}}

class XmlToDictDataTransform:
    def __init__(self):
        # self.data = {}
        self.assignments = []
        self.measurements = []
        self.gnb_resources = []
        self._start_new_msg = False
        self._buffer = ""

    def reset(self):
        # self.data = {}
        self.assignments = []
        self.measurements = []
        self.gnb_resources = []
        self._start_new_msg = False
        self._buffer = ""

    def parse_incoming_data(self, xml_string: str):
        # print(xml_string)
        try:
            _data = xmltodict.parse(xml_string)
            _input_dict = reduce(operator.getitem, _MAIN_TAG, _data)
            print(_input_dict)
            _header_collection_time, _header_cell_id, _header_plmn_id = self.parse_header(_input_dict)
            _cell_id_int = -1
            try:
                _cell_id_int = int(bytes.fromhex(_header_cell_id).split(b'\x00')[0], 16)
            except ValueError:
                try:
                    _cell_id_int = int(
                        bytes(int(_header_cell_id[i: i + 8], 2) for i in range(0, len(_header_cell_id), 8)).split(b'\x00')[
                            0])
                except ValueError:
                    _cell_id_only = _header_cell_id.split('(')[0]
                    _cell_id_int = int(bytes.fromhex(_cell_id_only).split(b'\x00')[0], 16)
            try:
                _header_plmn_id = bytes.fromhex(_header_plmn_id).decode('utf-8')
            except ValueError:
                pass
            try:
                _header_collection_time = int(_header_collection_time, 16)
            except ValueError:
                pass
            self.parse_message(_input_dict, _cell_id_int)
        except xml.parsers.expat.ExpatError:
            print("Error in parsing xml string")
            print(xml_string)

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
        _plmn_id = -1
        for _header_plmn_id_path in _HEADER_PLMN_ID:
            try:
                _plmn_id = reduce(operator.getitem, _header_plmn_id_path, _header)
            except KeyError:
                pass
        return _collection_time, _cell_id, _plmn_id

    def parse_message(self, input_dict: Mapping, cell_id: int):

        _message_dict = reduce(operator.getitem, _MESSAGE_PART, input_dict)
        # print(_message_dict)
        _matched_ues_dict = {}
        try:
            _matched_ues_dict = reduce(operator.getitem, _LIST_OF_MATCHED_UES, _message_dict)
            _cell_assignments = self._get_cell_assignments(_matched_ues_dict, cell_id)
            self._append_assignment_data(_cell_assignments)
        except KeyError:
            pass
        try:
            _cell_measurements = self._get_cell_measurements(_matched_ues_dict, cell_id)
            self._append_measurement_data(_cell_measurements)
        except KeyError:
            pass
        try:
            _user_kpis = self._get_user_kpis(_matched_ues_dict, cell_id)
            self._append_gnb_used_resources(_user_kpis)
        except KeyError:
            pass
        try:
            _pm_containers = reduce(operator.getitem, _PM_CONTAINERS_LIST_PM_INFORMATION, _message_dict)
            _pm_cont_list = self._get_pm_information(_pm_containers)
            # print(_pm_cont_list)
        except KeyError:
            pass

    def _append_gnb_used_resources(self, _cell_data: dict):
        _cell_id = _cell_data.get(_JSON_CELL_ID)
        _used_prb_in_cell_by_efs = 0
        for _user_meas in _cell_data.get(_JSON_MEASUREMENT):
            _imsi = _user_meas.get(_JSON_IMSI)
            # TODO: Have to check that the user is ef
            _user_measurements = _user_meas.get(_JSON_USER_MEASUREMENTS)
            _prb_used_filtered = list(filter(lambda pair: _UE_USED_PRB_FIELD_NAME in pair.keys(), _user_measurements))
            if len(_prb_used_filtered) == 1:
                _used_prb_in_cell_by_efs += _prb_used_filtered[0][_UE_USED_PRB_FIELD_NAME]
        # check if there exist data in the gnb resources vector
        # print(self.gnb_resources)
        _existing_data_for_cell = list(filter(lambda pair_ind_cell_resour: pair_ind_cell_resour[1][_JSON_CELL_ID] == _cell_id, enumerate(self.gnb_resources)))
        if len(_existing_data_for_cell) == 1:
            # get the index from enumerate, used it to access the list of gn resources
            self.gnb_resources[_existing_data_for_cell[0][0]] = {_JSON_CELL_ID: _cell_id, _JSON_GNB_USER_RESOURCES: _used_prb_in_cell_by_efs}
        elif len(_existing_data_for_cell) > 1:
            # shouldn't happen
            pass
        else:
            self.gnb_resources.append({_JSON_CELL_ID: _cell_id, _JSON_GNB_USER_RESOURCES: _used_prb_in_cell_by_efs})

    def _get_user_kpis(self, input_dict: Mapping, cell_id: int)->list:
        _ue_meas_list = []
        if isinstance(input_dict, dict):
            ue_id = reduce(operator.getitem, _PM_CONTAINERS_UE_ID, input_dict)
            ue_id = int(bytes.fromhex(str(ue_id)))
            _pm_containers = reduce(operator.getitem, _PM_CONTAINERS_LIST_PM_INFORMATION, input_dict)
            _pm_cont_list = self._get_pm_information(_pm_containers)
            _ue_meas_list.append({_JSON_IMSI : ue_id, _JSON_USER_MEASUREMENTS: _pm_cont_list})
        else:
            # we have a list
            for matched_ue_dict in input_dict:
                ue_id = reduce(operator.getitem, _PM_CONTAINERS_UE_ID, matched_ue_dict)
                ue_id = int(bytes.fromhex(str(ue_id)))
                _pm_containers = reduce(operator.getitem, _PM_CONTAINERS_LIST_PM_INFORMATION, matched_ue_dict)
                _pm_cont_list = self._get_pm_information(_pm_containers)
                _ue_meas_list.append({_JSON_IMSI : ue_id, _JSON_USER_MEASUREMENTS: _pm_cont_list})
        return {_JSON_CELL_ID: cell_id, _JSON_MEASUREMENT: _ue_meas_list}

    def _append_measurement_data(self, _meas_data: dict):
        _cell_id = _meas_data[_JSON_CELL_ID]
        _measurements_list = _meas_data[_JSON_USER_MEASUREMENTS]
        _cell_measurement_data = []
        _cell_measurement_data = list(
            filter(lambda _ind_meas: _ind_meas[1][_JSON_CELL_ID] == _cell_id, enumerate(self.measurements)))
        if len(_cell_measurement_data) > 1:
            # this shouldn't happen; if it happens we drop all data
            self.reset()
            return
        elif len(_cell_measurement_data) == 0:
            self.measurements.append(_meas_data)
        else:
            for _measurement in _measurements_list:
                _imsi = _measurement[_JSON_IMSI]
                _meas = _measurement[_JSON_MEASUREMENT]
                _single_user_measurement_data = []

                _single_user_measurement_data = list(filter(
                    lambda _ind_user_meas: _ind_user_meas[1][_JSON_IMSI] == _imsi,
                    enumerate(self.measurements[_cell_measurement_data[0][0]][_JSON_USER_MEASUREMENTS])))

                if len(_single_user_measurement_data) > 1:
                    # this shouldn't happen; if it happens we drop all data
                    self.reset()
                    return
                elif len(_single_user_measurement_data) == 0:
                    self.measurements[_cell_measurement_data[0][0]][_JSON_USER_MEASUREMENTS].append({_JSON_IMSI: _imsi, _JSON_MEASUREMENT: _meas})
                else:
                    # we have measurements from this imsi, thus we check per cell base;
                    # if cell doesn't exist we create it, otherwise we add to the list
                    
                    for _single_meas in _meas:
                        _neigh_cell_id = _single_meas[_JSON_CELL_ID]
                        _neigh_sinr = _single_meas[_JSON_SINR]
                        if isinstance(_neigh_sinr, list):
                            _neigh_sinr = _neigh_sinr
                        else:
                            _neigh_sinr = []
                        _single_neigh_cell_data = list(filter(
                            lambda _ind_neigh_meas: _ind_neigh_meas[1][_JSON_CELL_ID] == _neigh_cell_id,
                            enumerate(self.measurements[_cell_measurement_data[0][0]][_JSON_USER_MEASUREMENTS] \
                                          [_single_user_measurement_data[0][0]][_JSON_MEASUREMENT])))
                        if len(_single_neigh_cell_data) > 1:
                            # this shouldn't happen; if it happens we drop all data
                            self.reset()
                            return
                        elif len(_single_neigh_cell_data) == 0:
                            self.measurements[_cell_measurement_data[0][0]][_JSON_USER_MEASUREMENTS] \
                                [_single_user_measurement_data[0][0]][_JSON_MEASUREMENT] = [_single_meas]
                        else:
                            if len(_neigh_sinr)>0:
                                self.measurements[_cell_measurement_data[0][0]][_JSON_USER_MEASUREMENTS] \
                                    [_single_user_measurement_data[0][0]][_JSON_MEASUREMENT] \
                                    [_single_neigh_cell_data[0][0]][_JSON_SINR].append(_neigh_sinr[0])

    def _append_assignment_data(self, _assign_data: dict):
        _cell_id = _assign_data[_JSON_CELL_ID]
        _user_assignment_list = _assign_data[_JSON_USER_ASSIGNMENTS]
        _cell_assignment_data = list(
            filter(lambda _ind_assignment: _ind_assignment[1][_JSON_CELL_ID] == _cell_id, enumerate(self.assignments)))
        if len(_cell_assignment_data) > 1:
            # this shouldn't happen; if it happens we drop all data
            self.reset()
            return
        elif len(_cell_assignment_data) == 0:
            self.assignments.append(_assign_data)
        else:
            for _user_assignment in _user_assignment_list:
                _imsi = _user_assignment[_JSON_IMSI]
                _sinr = _user_assignment[_JSON_SINR]
                _sinr = _sinr if isinstance(_sinr, list) else [_sinr]

                # update the data entry in the class member
                # we should have only 1 assignment per cell id
                # we have to update the sinr only
                # _cell_assignment_data[0][0] index in the dict
                _local_assignment_data = self.assignments[_cell_assignment_data[0][0]][_JSON_USER_ASSIGNMENTS]
                _imsi_list = list(filter(lambda _ind_imsi: _ind_imsi[1][_JSON_IMSI] == _imsi, enumerate(_local_assignment_data)))
                if len(_imsi_list) == 0:
                    self.assignments[_cell_assignment_data[0][0]][_JSON_USER_ASSIGNMENTS].append({_JSON_IMSI: _imsi, _JSON_SINR: _sinr})
                elif len(_imsi_list) == 1:
                    self.assignments[_cell_assignment_data[0][0]][_JSON_USER_ASSIGNMENTS][_imsi_list[0][0]][_JSON_SINR].extend(_sinr)
                else:
                    # shouldn't happen
                    self.reset()

    def _get_cell_assignments(self, input_dict: Mapping, cell_id: int) -> Mapping:
        # print(input_dict)
        _user_assignment_list = []
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

        if isinstance(input_dict, dict):
            _user_measurements = self._get_single_user_measurements(input_dict)
            if len(_user_measurements) == 1:
                _user_measurement_list.append(_user_measurements[0])
        else:
            for matched_ue_dict in input_dict:
                _user_measurements = self._get_single_user_measurements(matched_ue_dict)
                if len(_user_measurements) == 1:
                    _user_measurement_list.append(_user_measurements[0])
        return {_JSON_CELL_ID: cell_id, _JSON_USER_MEASUREMENTS: _user_measurement_list}

    def _get_single_user_assignment(self, input_dict: Mapping) -> Tuple[int, int]:
        _users_assignment_list = []
        try:
            ue_id = reduce(operator.getitem, _PM_CONTAINERS_UE_ID, input_dict)
            ue_id = int(bytes.fromhex(str(ue_id)))  # binary to int conversion
            _list_pm_info_dict = reduce(operator.getitem, _PM_CONTAINERS_LIST_PM_INFORMATION, input_dict)
            if isinstance(_list_pm_info_dict, dict):
                _name_field = reduce(operator.getitem, _PM_INFO_ITEM_TYPE, _list_pm_info_dict)
                _single_data_dict = reduce(operator.getitem, _PM_INFO_ITEM_VALUE, _list_pm_info_dict)
                _assign_list = self._get_serving_cell_sinr(_single_data_dict)
                if (_assign_list[0] > -1) & (_assign_list[1] > -1):
                    _users_assignment_list.append({_JSON_IMSI: ue_id, _JSON_MCS: _assign_list[1]})
                    # _users_assignment_list.append({_JSON_IMSI: ue_id, _JSON_SINR: _assign_list[1]})
            else:
                for _pm_info_dict in _list_pm_info_dict:
                    _name_field = reduce(operator.getitem, _PM_INFO_ITEM_TYPE, _pm_info_dict)
                    _single_data_dict = reduce(operator.getitem, _PM_INFO_ITEM_VALUE, _pm_info_dict)
                    _assign_list = self._get_serving_cell_sinr(_single_data_dict)
                    if (_assign_list[0] > -1) & (_assign_list[1] > -1):
                        # _users_assignment_list.append({_JSON_IMSI: ue_id, _JSON_SINR: _assign_list[1]})
                        _users_assignment_list.append({_JSON_IMSI: ue_id, _JSON_MCS: _assign_list[1]})
            if len(_users_assignment_list) < 2:
                return _users_assignment_list
        except (KeyError, TypeError):
            pass
        return []

    # Returns the measurement for that user if it exist in the branch for not more that 1 time
    # otherwise it returns an empty list
    def _get_single_user_measurements(self, input_dict: Mapping) -> list:
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
        except (KeyError, TypeError):
            pass
        return []

    def _get_serving_cell_sinr(self, input_dict: Mapping) -> Tuple[int, float]:
        if _RRC_SERVING_CELL_PATH[0] not in input_dict.keys():
            return -1, -1
        else:
            if _RRC_SERVING_CELL_PATH[1] not in input_dict[_RRC_SERVING_CELL_PATH[0]].keys():
                return -1, -1
        try:
            _sub_dict = reduce(operator.getitem, _RRC_SERVING_CELL_PATH, input_dict)
            _serving_cell_id = reduce(operator.getitem, _RRC_SERVING_CELL_ID_PATH, _sub_dict)
            _phy_serving_cell_id = reduce(operator.getitem, _RRC_SERVING_PHYSICAL_CELL_ID_PATH, _sub_dict)
            _sinr_serving_cell_id = reduce(operator.getitem, _RRC_SERVING_CELL_SINR_PATH, _sub_dict)
            _mcs_serving_cell_id = reduce(operator.getitem, _RRC_SERVING_CELL_MCS_PATH, _sub_dict)
            # return int(_serving_cell_id), float(_sinr_serving_cell_id)
            return int(_serving_cell_id), float(_mcs_serving_cell_id)
        except (KeyError, TypeError):
            # means we cannot find the path in the dictionary
            print("Error in parsing data")
        return -1, -1

    def _get_neighbor_cell_sinr_measurements(self, input_dict: Mapping) -> list:
        _list_of_measurements = []
        # if (_RRC_NEIGHBOR_CELL_PATH[1] not in input_dict[_RRC_NEIGHBOR_CELL_PATH[0]].keys()):
        #     return []
        if _RRC_NEIGHBOR_CELL_PATH[0] not in input_dict.keys():
            return []
        else:
            if _RRC_NEIGHBOR_CELL_PATH[1] not in input_dict[_RRC_NEIGHBOR_CELL_PATH[0]].keys():
                return []
        _sub_dict_neigh = reduce(operator.getitem, _RRC_NEIGHBOR_CELL_PATH, input_dict)
        try:
            if isinstance(_sub_dict_neigh, dict):
                # means we have only one measurements and not a list of measurements
                _phy_neigh_cell_id = int(reduce(operator.getitem, _RRC_NEIGHBOR_CELL_ID_PATH, _sub_dict_neigh))
                _phy_neigh_sinr = float(reduce(operator.getitem, _RRC_NEIGHBOR_CELL_SINR_PATH, _sub_dict_neigh))
                _phy_neigh_mcs = int(reduce(operator.getitem, _RRC_NEIGHBOR_CELL_MCS_PATH, _sub_dict_neigh))
                # _list_of_measurements.append({_JSON_CELL_ID: _phy_neigh_cell_id, _JSON_SINR: [_phy_neigh_sinr]})
                _list_of_measurements.append({_JSON_CELL_ID: _phy_neigh_cell_id, _JSON_MCS: [_phy_neigh_mcs]})
            else:
                for _single_dict in _sub_dict_neigh:
                    _phy_neigh_cell_id = int(reduce(operator.getitem, _RRC_NEIGHBOR_CELL_ID_PATH, _single_dict))
                    _phy_neigh_sinr = float(reduce(operator.getitem, _RRC_NEIGHBOR_CELL_SINR_PATH, _single_dict))
                    _phy_neigh_mcs = int(reduce(operator.getitem, _RRC_NEIGHBOR_CELL_MCS_PATH, _single_dict))
                    # _list_of_measurements.append({_JSON_CELL_ID: _phy_neigh_cell_id, _JSON_SINR: [_phy_neigh_sinr]})
                    _list_of_measurements.append({_JSON_CELL_ID: _phy_neigh_cell_id, _JSON_MCS: [_phy_neigh_mcs]})
            # return _list_of_measurements
        except (KeyError, TypeError):
            # means we cannot find the path in the dictionary
            print("Error in parsing data")
        return _list_of_measurements

    def _get_single_pm_information(self, input_dict: Mapping) -> Tuple[str, str, float]:
        name_field = reduce(operator.getitem, _PM_INFO_ITEM_TYPE, input_dict)
        _single_data_dict = reduce(operator.getitem, _PM_INFO_ITEM_VALUE, input_dict)
        _data_type_key = list(_single_data_dict.keys())
        if (len(_data_type_key) != 1):
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
            return (name_field, 'valueReal', float(reduce(operator.getitem, ['valueReal'], _single_data_dict)))
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

    def append_msg_2(self, msg: str):
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

    def append_msg(self, msg:str):
        self._buffer += msg
        # print(self._buffer)
        _msg_start_l_ind = str(self._buffer).find("<E2AP-PDU>")
        if _msg_start_l_ind > 0:
            # it means that we have an error in the buffer
            # we have to redefine the buffer
            self._buffer = self._buffer[_msg_start_l_ind:]
        elif _msg_start_l_ind == -1:
            # Drop everything in the buffer, since we have invalid data
            self._buffer = ""
        else:
            # We have valid buffer starting with <E2AP-PDU>
            # we check if there is ending tags
            _msg_end_l_ind = str(self._buffer).find("</E2AP-PDU>")
            while _msg_end_l_ind != -1:
                _complete_msg: str = self._buffer[:(_msg_end_l_ind + 11)]
                self.parse_incoming_data(_complete_msg)
                # remove parsed msg
                self._buffer = self._buffer[(_msg_end_l_ind + 11):]
                _msg_end_l_ind = str(self._buffer).find("</E2AP-PDU>")