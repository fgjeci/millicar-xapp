from enum import Enum
import xml
from typing import Mapping, List, Union, Tuple

import xmltodict
from functools import reduce
import operator
import os
# import numpy as np
import re
import pickle
import datetime

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
                   ['id-GlobalE2node-ID', 'eNB', 'global-eNB-ID', 'pLMN-Identity'], ]

_CUCP_PM_REPORTS_NUMBER = ['pm-Containers', 'PM-Containers-Item', 'performanceContainer',
                           'oCU-CP', 'cu-CP-Resource-Status', 'numberOfActive-UEs']

_PM_CONTAINERS_UE_ID = ['ueId']
_PM_CONTAINERS_LIST_PM_INFORMATION = ['list-of-PM-Information', 'PM-Info-Item']
_PM_INFO_ITEM_TYPE = ['pmType', 'measName']
_PM_INFO_ITEM_VALUE = ['pmVal']

# _RRC_SERVING_CELL_PATH = ['valueRRC', 'servingCellMeasurements', 'nr-measResultServingMOList', 'MeasResultServMO']
# _RRC_SERVING_CELL_ID_PATH = ['servCellId']
# _RRC_SERVING_CELL_SINR_PATH = ['measResultServingCell', 'measResult', 'cellResults', 'resultsSSB-Cell', 'sinr']
# _RRC_SERVING_CELL_MCS_PATH = ['measResultServingCell', 'measResult', 'cellResults', 'resultsSSB-Cell', 'mcs']
# _RRC_SERVING_PHYSICAL_CELL_ID_PATH = ['measResultServingCell', 'physCellId']

_RRC_SERVING_CELL_PATH = ['valueRRC', 'measResultNeighCells', 'measResultListNR', 'MeasResultNR']
_RRC_SERVING_CELL_ID_PATH = ['physCellId']
_RRC_SERVING_CELL_SINR_PATH = ['measResult', 'cellResults', 'resultsSSB-Cell', 'sinr']
_RRC_SERVING_CELL_MCS_PATH = ['measResult', 'cellResults', 'resultsSSB-Cell', 'mcs']

_RRC_NEIGHBOR_CELL_PATH = ['valueRRC', 'measResultNeighCells', 'measResultListNR', 'MeasResultNR']
_RRC_NEIGHBOR_CELL_ID_PATH = ['physCellId']
_RRC_NEIGHBOR_CELL_SINR_PATH = ['measResult', 'cellResults', 'resultsSSB-Cell', 'sinr']
_RRC_NEIGHBOR_CELL_MCS_PATH = ['measResult', 'cellResults', 'resultsSSB-Cell', 'mcs']

_USER_SERVING_CELL_SINR = "HO.SrcCellQual.RS-SINR.UEID"
_USER_NEIGHBOUR_CELL_SINR = "HO.TrgtCellQual.RS-SINR.UEID"

_GENERATING_MILLICAR_NODE_ID = "GeneratingNode.Rnti.UEID"
_GENERATING_MILLICAR_NODE_POSITION_X = "GeneratingNode.PositionX.UEID"
_GENERATING_MILLICAR_NODE_POSITION_Y = "GeneratingNode.PositionY.UEID"

_JSON_SINR = "sinr"
_JSON_MCS = "mcs"
_JSON_IMSI = "imsi"
_JSON_POSITION_X = "PositionX"
_JSON_POSITION_Y = "PositionY"
_JSON_SOURCE_RNTI = "SourceRnti"
_JSON_MEASUREMENT = "meas"
_JSON_ACTIVE_MEASUREMENT = "ActiveMeasurment"
# _JSON_CELL_ID = "cellId"
_JSON_PEER_RNTI = "PeerRnti"
_JSON_COLLECTION_TIME = "CollectionTime"
_JSON_ALL_UE_REPORTS = "AllDataReports"
_JSON_PLMN = "Plmn"
_JSON_TIMESTAMP = 'time'


class ServingPeerMeasurement:
    def __init__(self, input_dict: Mapping = None):
        self.input_dict = input_dict
        self.peer_rnti: int = None
        self.sinr: float = None
        self.mcs: int = None
        self._parse_data()

    def _parse_data(self):
        try:
            self.peer_rnti = int(reduce(operator.getitem, _RRC_SERVING_CELL_ID_PATH, self.input_dict))
            self.sinr = float(reduce(operator.getitem, _RRC_SERVING_CELL_SINR_PATH, self.input_dict))
            self.mcs = int(reduce(operator.getitem, _RRC_SERVING_CELL_MCS_PATH, self.input_dict))
        except (KeyError, TypeError):
            # means we cannot find the path in the dictionary
            print("Error in parsing data")

    def is_valid(self):
        return (self.peer_rnti is not None) & (self.sinr is not None) & (self.mcs is not None)

    def to_dict(self):
        return {_JSON_PEER_RNTI: self.peer_rnti, _JSON_MCS: self.mcs}


class PeerMeasurement:
    def __init__(self, input_dict: Mapping = None):
        self.input_dict = input_dict
        self.peer_rnti = None
        self.sinr = None
        self.mcs = None
        self._parse_data()

    def _parse_data(self):
        try:
            self.peer_rnti = int(reduce(operator.getitem, _RRC_NEIGHBOR_CELL_ID_PATH, self.input_dict))
            self.sinr = float(reduce(operator.getitem, _RRC_NEIGHBOR_CELL_SINR_PATH, self.input_dict))
            self.mcs = int(reduce(operator.getitem, _RRC_NEIGHBOR_CELL_MCS_PATH, self.input_dict))
        except (KeyError, TypeError):
            # means we cannot find the path in the dictionary
            print("Error in parsing data")

    def is_valid(self):
        return (self.peer_rnti is not None) & (self.sinr is not None) & (self.mcs is not None)

    def to_dict(self):
        return {_JSON_PEER_RNTI: self.peer_rnti, _JSON_MCS: self.mcs}


class ServingUserMeasurements:
    def __init__(self, input_dict: Mapping = None):
        self.input_dict = input_dict
        self.list_of_measurements: List[ServingPeerMeasurement] = self._parse_data()

    def _parse_data(self) -> List[ServingPeerMeasurement]:
        _list_of_measurements = []
        if _RRC_SERVING_CELL_PATH[0] not in self.input_dict.keys():
            return []
        else:
            if _RRC_SERVING_CELL_PATH[1] not in self.input_dict[_RRC_SERVING_CELL_PATH[0]].keys():
                return []
        _sub_dict_neigh = reduce(operator.getitem, _RRC_SERVING_CELL_PATH, self.input_dict)
        try:
            if isinstance(_sub_dict_neigh, dict):
                _neigh_cell_user_meas = ServingPeerMeasurement(_sub_dict_neigh)
                # means we have only one measurements and not a list of measurements
                _list_of_measurements.append(_neigh_cell_user_meas)
            else:
                for _single_dict in _sub_dict_neigh:
                    _neigh_cell_user_meas = ServingPeerMeasurement(_single_dict)
                    _list_of_measurements.append(_neigh_cell_user_meas)
            # return _list_of_measurements
        except (KeyError, TypeError):
            # means we cannot find the path in the dictionary
            print("Error in parsing data")
        return _list_of_measurements

    def to_dict(self):
        return [_user_measurement.to_dict() for _user_measurement in self.list_of_measurements]

    def get_rntis(self):
        return [_user_measurement.peer_rnti for _user_measurement in self.list_of_measurements
                if _user_measurement.peer_rnti is not None]


class UserMeasurements:
    def __init__(self, input_dict: Mapping = None):
        self.input_dict = input_dict
        self.list_of_measurements: List[PeerMeasurement] = self._parse_data()

    def _parse_data(self) -> List[PeerMeasurement]:
        _list_of_measurements = []
        if _RRC_NEIGHBOR_CELL_PATH[0] not in self.input_dict.keys():
            return []
        else:
            if _RRC_NEIGHBOR_CELL_PATH[1] not in self.input_dict[_RRC_NEIGHBOR_CELL_PATH[0]].keys():
                return []
        _sub_dict_neigh = reduce(operator.getitem, _RRC_NEIGHBOR_CELL_PATH, self.input_dict)
        try:
            if isinstance(_sub_dict_neigh, dict):
                _neigh_cell_user_meas = PeerMeasurement(_sub_dict_neigh)
                # means we have only one measurements and not a list of measurements
                _list_of_measurements.append(_neigh_cell_user_meas)
            else:
                for _single_dict in _sub_dict_neigh:
                    _neigh_cell_user_meas = PeerMeasurement(_single_dict)
                    _list_of_measurements.append(_neigh_cell_user_meas)
            # return _list_of_measurements
        except (KeyError, TypeError):
            # means we cannot find the path in the dictionary
            print("Error in parsing data")
        return _list_of_measurements

    def to_dict(self):
        return [_user_measurement.to_dict() for _user_measurement in self.list_of_measurements]

    def get_rntis(self):
        return [_user_measurement.peer_rnti for _user_measurement in self.list_of_measurements
                if _user_measurement.peer_rnti is not None]


class MillicarUeSingleReport:
    def __init__(self, input_dict, header_collection_time: int = -1):
        self._input_dict = input_dict
        self.ue_id = None
        self.rnti = None
        self.position_x = None
        self.position_y = None
        self.serving_sinr_reports: ServingUserMeasurements = None
        self.sinr_reports: UserMeasurements = None
        self.collection_time = header_collection_time

    def _parse_pm_container(self, input_dict=None):
        if input_dict is None:
            input_dict = self._input_dict
        if isinstance(input_dict, list):# & (len(input_dict) == 5):
            for _single_report in input_dict:
                name_field = reduce(operator.getitem, _PM_INFO_ITEM_TYPE, _single_report)
                _single_data_dict = reduce(operator.getitem, _PM_INFO_ITEM_VALUE, _single_report)
                if name_field == _GENERATING_MILLICAR_NODE_ID:
                    self.rnti = int(reduce(operator.getitem, ['valueInt'], _single_data_dict))
                elif name_field == _GENERATING_MILLICAR_NODE_POSITION_X:
                    self.position_x = int(reduce(operator.getitem, ['valueInt'], _single_data_dict))
                elif name_field == _GENERATING_MILLICAR_NODE_POSITION_Y:
                    self.position_y = int(reduce(operator.getitem, ['valueInt'], _single_data_dict))
                elif name_field == _USER_SERVING_CELL_SINR:
                    # the report of active communication
                    self.serving_sinr_reports = ServingUserMeasurements(_single_data_dict)
                elif name_field == _USER_NEIGHBOUR_CELL_SINR:
                    # the last is the neighbour measurements
                    self.sinr_reports = UserMeasurements(_single_data_dict)

    def parse(self, input_dict: Union[dict, List[dict]] = None):
        if input_dict is None:
            input_dict = self._input_dict
        try:
            _ue_id = reduce(operator.getitem, _PM_CONTAINERS_UE_ID, input_dict)
            self.ue_id = int(bytes.fromhex(str(_ue_id)))  # binary to int conversion
            _list_pm_info_dict = reduce(operator.getitem, _PM_CONTAINERS_LIST_PM_INFORMATION, input_dict)
            self._parse_pm_container(_list_pm_info_dict)
        except KeyError:
            pass

    def is_valid(self) -> bool:
        return True
        # return (self.rnti is not None) & (self.position_x is not None) & \
        #         (self.position_y is not None) & (self.sinr_reports is not None) & \
        #        (self.ue_id is not None)

    def to_dict(self):
        return {_JSON_SOURCE_RNTI: self.rnti, _JSON_POSITION_X: self.position_x, _JSON_POSITION_Y: self.position_y,
                _JSON_MEASUREMENT: self.sinr_reports.to_dict() if (self.sinr_reports is not None) else [],
                _JSON_ACTIVE_MEASUREMENT: self.serving_sinr_reports.to_dict() if (self.serving_sinr_reports is not None) else [],
                _JSON_COLLECTION_TIME: self.collection_time,
                _JSON_TIMESTAMP: str(datetime.datetime.now()),
                }

    def get_connected_rntis(self) -> List[int]:
        _all_rntis = set()
        if self.serving_sinr_reports is not None:
            _all_rntis.update(self.serving_sinr_reports.get_rntis())
        if self.sinr_reports is not None:
            _all_rntis.update(self.sinr_reports.get_rntis())
        return list(_all_rntis)

class XmlToDictDataTransform:
    def __init__(self, plmn="110"):
        self.num_of_received_reports = 0
        self.num_of_reports = 0
        self.plmn_id = plmn
        self.all_users_reports: List[MillicarUeSingleReport] = []

    def reset(self):
        self.num_of_received_reports = 0
        self.num_of_reports = 0
        self.all_users_reports = []
        # self.plmn_id = "110"

    def can_perform_optimization(self):
        _received_all_reports = (self.num_of_reports != 0) & (self.num_of_received_reports == self.num_of_reports)
        if _received_all_reports:
            print("All reports received thus we can perform optimization")
        return _received_all_reports

    def peek_header(xml_string: str):
        try:
            _data = xmltodict.parse(xml_string)
            _input_dict = reduce(operator.getitem, _MAIN_TAG, _data)
            _header = reduce(operator.getitem, _HEADER_PART, _input_dict)
            _collection_time = reduce(operator.getitem, _HEADER_COLLECTION_START_TIME, _header)
            # print("Collection time " + str(int(re.sub(r"[\\n\t\s\n]*", "", _collection_time), 16)))
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
                    try:
                        _plmn_id = bytes.fromhex(_plmn_id).decode('utf-8')
                    except ValueError:
                        pass
                except KeyError:
                    pass
            return _collection_time, _cell_id, _plmn_id
        except xml.parsers.expat.ExpatError:
            print(xml_string)
            return -1, -1, -1

    def parse_incoming_data(self, xml_string: str):
        self.num_of_received_reports += 1
        try:
            _data = xmltodict.parse(xml_string)
            _input_dict = reduce(operator.getitem, _MAIN_TAG, _data)
            _header_collection_time, _header_cell_id, _header_plmn_id = self.parse_header(_input_dict)
            _cell_id_int = -1
            try:
                _cell_id_int = int(bytes.fromhex(_header_cell_id).split(b'\x00')[0], 16)
            except ValueError:
                try:
                    _cell_id_int = int(
                        bytes(int(_header_cell_id[i: i + 8], 2) for i in range(0, len(_header_cell_id), 8)).split(
                            b'\x00')[
                            0])
                except ValueError:
                    _cell_id_only = _header_cell_id.split('(')[0]
                    _cell_id_int = int(bytes.fromhex(_cell_id_only).split(b'\x00')[0], 16)
            try:
                _header_plmn_id = bytes.fromhex(_header_plmn_id).decode('utf-8')
            except ValueError:
                pass
            _header_collection_time_int: int = -1
            try:
                # _header_collection_time = int(_header_collection_time, 16)
                _header_collection_time_int = int(re.sub(r"[\\n\t\s\n]*", "", _header_collection_time), 16)
            except ValueError:
                pass
            # print(_header_collection_time, _cell_id_int, _header_plmn_id)
            # self.parse_message(_input_dict, _cell_id_int)
            self.parse_message_single_report(_input_dict, _header_collection_time_int)
            # print("Received report " + str(self.num_of_received_reports) + " from " + str(self.num_of_reports) + \
            #       " for collection time " + str(_header_collection_time))
        except xml.parsers.expat.ExpatError:
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
        # print(_cell_id)
        _plmn_id = -1
        for _header_plmn_id_path in _HEADER_PLMN_ID:
            try:
                _plmn_id = reduce(operator.getitem, _header_plmn_id_path, _header)
            except KeyError:
                pass
        return _collection_time, _cell_id, _plmn_id

    def parse_message_single_report(self, input_dict: Mapping, header_collection_time: int):
        _reports_per_user_list: List[MillicarUeSingleReport] = self._parse_message_ues_single_report(input_dict, header_collection_time)
        if len(_reports_per_user_list) != 1:
            print("Unexpected length of received reports")
        else:
            self.all_users_reports.append(_reports_per_user_list[0])
            # store the data in traces everytime a new report comes
            # pickle_out = open('/home/traces/ue_reports.pickle', 'ab+')
            pickle_out = open('/home/traces/ue_reports_' + self.plmn_id + '.pickle', 'ab+')
            _ue_reports_dict = _reports_per_user_list[0].to_dict()
            _ue_reports_dict[_JSON_PLMN] = self.plmn_id
            pickle.dump(_ue_reports_dict, pickle_out)
            pickle_out.close()

    def _parse_message_ues_single_report(self, input_dict: Mapping, header_collection_time: int) -> List:
        _message_dict = reduce(operator.getitem, _MESSAGE_PART, input_dict)
        _matched_ues_dict = {}
        try:
            _matched_ues_dict = reduce(operator.getitem, _LIST_OF_MATCHED_UES, _message_dict)
            self.num_of_reports = int(reduce(operator.getitem, _CUCP_PM_REPORTS_NUMBER, _message_dict))
        except KeyError:
            pass
        try:
            _reports_per_user_list = []
            if isinstance(_matched_ues_dict, list):
                for _imsi_data_report in _matched_ues_dict:
                    single_report = MillicarUeSingleReport(_imsi_data_report, header_collection_time)
                    single_report.parse()
                    if single_report.is_valid():
                        _reports_per_user_list.append(single_report)
            else:
                single_report = MillicarUeSingleReport(_matched_ues_dict, header_collection_time)
                single_report.parse()
                if single_report.is_valid():
                    _reports_per_user_list.append(single_report)
            return _reports_per_user_list
        except KeyError:
            pass
        return []

    def to_dict(self):
        # return [report.to_dict() for report in self.all_users_reports]
        return {
            _JSON_TIMESTAMP: str(datetime.datetime.now()),
            _JSON_PLMN: self.plmn_id,
            _JSON_ALL_UE_REPORTS: [report.to_dict() for report in self.all_users_reports]
        }


_msg = b'<message><E2SM-KPM-IndicationHeader><indicationHeader-Format1><collectionStartTime>65 6C 66 65 72 28 21 00</collectionStartTime><id-GlobalE2node-ID><gNB><global-gNB-ID><plmn-id>31 31 31</plmn-id><gnb-id><gnb-ID>31 00 00 00\n                        </gnb-ID></gnb-id></global-gNB-ID></gNB></id-GlobalE2node-ID></indicationHeader-Format1></E2SM-KPM-IndicationHeader><E2SM-KPM-IndicationMessage><indicationMessage-Format1><pm-Containers><PM-Containers-Item><performanceContainer><oCU-CP><cu-CP-Resource-Status><numberOfActive-UEs>2</numberOfActive-UEs></cu-CP-Resource-Status></oCU-CP></performanceContainer></PM-Containers-Item></pm-Containers><cellObjectID>NRCellCU</cellObjectID><list-of-matched-UEs><PerUE-PM-Item><ueId>30 30 30 30 31</ueId><list-of-PM-Information><PM-Info-Item><pmType><measName>GeneratingNode.Rnti.UEID</measName></pmType><pmVal><valueInt>1</valueInt></pmVal></PM-Info-Item><PM-Info-Item><pmType><measName>GeneratingNode.PositionX.UEID</measName></pmType><pmVal><valueInt>0</valueInt></pmVal></PM-Info-Item><PM-Info-Item><pmType><measName>GeneratingNode.PositionY.UEID</measName></pmType><pmVal><valueInt>3</valueInt></pmVal></PM-Info-Item><PM-Info-Item><pmType><measName>HO.TrgtCellQual.RS-SINR.UEID</measName></pmType><pmVal><valueRRC><rrcEvent><b1/></rrcEvent></valueRRC></pmVal></PM-Info-Item></list-of-PM-Information></PerUE-PM-Item></list-of-matched-UEs></indicationMessage-Format1></E2SM-KPM-IndicationMessage></message>'

if __name__ == '__main__':
    _transformer = XmlToDictDataTransform()
    # print(os.getcwd())
    _filename = 'data.xml'
    _dir = '.'
    _complete_msg = ""
    _tmp_msg = ""
    _start_new_msg = False
    # with open(_filename) as _file:
    # with open(os.path.join(_dir, _filename)) as _file:
    #     lines = _file.readlines()
    #     _transformer.parse_incoming_data(lines[0])
    #     print(_transformer.measurements)
    _transformer.parse_incoming_data(str(_msg))
    print()