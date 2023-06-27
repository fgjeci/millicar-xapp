from queue import Queue
from transform_xml_to_dict_millicar import MillicarUeSingleReport
from typing import List, Tuple
import numpy as np
from more_itertools import locate


class MillicarPreoptimize:
    def __init__(
        self,
        peer_measurements_history_depth: int = 1,  # indicates the # of samples to be considered for the sinr
        to_relay_threshold: float = 46
    ):
        self._peer_measurements_history_depth = peer_measurements_history_depth
        self._measurements_queue = Queue(maxsize=self._peer_measurements_history_depth)
        # self._last_serving_measurement = None
        # self.sinr_agg_func = sinr_agg_func
        self._all_rntis = []
        self.to_relay_threshold = to_relay_threshold # if a connection reaches this threshold, it is defined as to be relayed,
        # this due to conversion
        self.genuine_links_relay: List[List[int]] = self._get_communication_rnti_tuples()

    def set_genuine_link(self, rnti: int, peer_rnti: int, relay_rnti: int)->bool:
        _entry_inserted = False
        _indexes_first_direction_ = list(locate(self.genuine_links_relay, 
                                           lambda _single_link: ((_single_link[0] == rnti) & \
                                                (_single_link[1] == peer_rnti))))
        _indexes_sec_direction_ = list(locate(self.genuine_links_relay, 
                                         lambda _single_link: ((_single_link[0] == peer_rnti) & \
                                                (_single_link[1] == rnti))))
        
        if len(_indexes_first_direction_)==1:
            _entry_inserted = self.genuine_links_relay[_indexes_first_direction_[0]][2] != relay_rnti

            self.genuine_links_relay[_indexes_first_direction_[0]][2] = relay_rnti
            
        elif len(_indexes_sec_direction_)==1:
            _entry_inserted = self.genuine_links_relay[_indexes_sec_direction_[0]][2] != relay_rnti
            self.genuine_links_relay[_indexes_sec_direction_[0]][2] = relay_rnti
        return _entry_inserted


    def get_original_link_tuple(self, rnti:int, peer_rnti:int )-> Tuple[int, int, int]:
        _filter_1 = list(filter(lambda _single_link: ((_single_link[0] == peer_rnti) | \
                                                    (_single_link[0] == rnti)), self.genuine_links_relay))
        _filter_2 = list(filter(lambda _single_link: ((_single_link[1] == peer_rnti) | \
                                                    (_single_link[1] == rnti)), self.genuine_links_relay))
        
        if len(_filter_1) >0:
            return _filter_1[0]
        elif len(_filter_2) >0:
            return _filter_2[0]
        else:
            return (-1, -1, -1)

    def _get_communication_rnti_tuples(self)-> List[List[int]]:
        _nr_groups = 8
        _nr_sources = 4
        _all_communicating_tuples = [] 
        for _group_range in range(_nr_groups):
            for _source_ind in range(_nr_sources):
                _all_communicating_tuples.append([_group_range*8 + _source_ind+1, 
                                                  _group_range*8 + _source_ind+1+4, int(np.iinfo(np.uint16).max)])
        return _all_communicating_tuples

    def insert_measurements(self, reports: List[MillicarUeSingleReport]):
        if self._measurements_queue.full():
            # if full remove the oldest element
            _ = self._measurements_queue.get()
        # put the new element
        self._measurements_queue.put(reports)

    def can_perform_optimization(self) -> bool:
        # we only perform optimization when we have full buffer
        return self._measurements_queue.full()

    # Returns active links: rnti, peer rnti and sinr
    def _get_active_links(self) -> List[Tuple[int, int, float]]:
        # get data assignment data from last queue position
        # make reference to the last queue element to define the active links
        _return_list = []
        _queue_size = len(self._measurements_queue.queue)
        if _queue_size > 0:
            _queue_elem: List[MillicarUeSingleReport] = self._measurements_queue.queue[_queue_size-1]
            for _ue_single_report in _queue_elem:
                _rnti = _ue_single_report.rnti
                # get only active links
                if _ue_single_report.serving_sinr_reports is not None:
                    for _single_meas in _ue_single_report.serving_sinr_reports.list_of_measurements:
                        if _single_meas.peer_rnti != _rnti:
                            # instead of taking the sinr of active measurements we take the estimated SNR
                            _return_list.append((_rnti, _single_meas.peer_rnti, _single_meas.sinr))
        return _return_list

    # def _get_active_links(self) -> List[Tuple[int, int, float]]:
    #     # get data assignment data from last queue position
    #     # make reference to the last queue element to define the active links
    #     _return_list = []
        

    #     # _return_list.append((_rnti, _single_meas.peer_rnti, _single_meas.sinr))
    #     return _return_list

    # return true if sinr of a link is below predefined threshold
    def _need_relay_link(self, _tuple: Tuple[int, int, float]):
        # rnti, peer rnti, sinr
        # can modify in the future
        return _tuple[2] < self.to_relay_threshold

    # rnti, peer_rnti, sinr left to right, sinr oposite
    def _get_need_relay_links_both_side(self, links_need_relay: List[Tuple[int, int, float, float]],
                                        active_links: List[Tuple[int, int, float]]):
        _need_relay_links_both_sides = []
        for _link in links_need_relay:
            _rnti = _link[0]
            _peer_rnti = _link[1]
            # check if reverse link exists
            _reverse_link_need_relay = list(filter(lambda _single_link: ((_single_link[0] == _peer_rnti) & \
                                                              (_single_link[1] == _rnti)),  links_need_relay))
            _reverse_link_active_links = list(filter(lambda _single_link: ((_single_link[0] == _peer_rnti) & \
                                                              (_single_link[1] == _rnti)),  active_links))
            if len(_reverse_link_need_relay) > 0:
                # exist the reverse link
                _need_relay_links_both_sides.append((*_link, _reverse_link_need_relay[0][2]))
            else:
                # reverse link does not exist in need relay, though if it is not in the active links either
                # it means that the link is one directional, thus we insert in the return list
                if len(_reverse_link_active_links)==0:

                    _need_relay_links_both_sides.append((*_link, 0))
        return _need_relay_links_both_sides

    # return a list of tuples source-dest which needs relay
    def get_need_relay_links(self) -> List[Tuple[int, int, float, float]]:
        _active_links = self._get_active_links()
        _need_relay = list(
            filter(lambda _single_act_link: self._need_relay_link(_single_act_link), _active_links))
        # both directions must need relay
        # filter non bidirectional
        _need_relay_both_sides: List[Tuple[int, int, float, float]] = self._get_need_relay_links_both_side(_need_relay, _active_links)
        return _need_relay_both_sides

    def is_need_relay_links(self) -> bool:
        has_need_relay = any([self._need_relay_link(_active_link) for _active_link in self._get_active_links()])
        return has_need_relay

    def get_all_rntis(self) -> set:
        _rnti_list = set()
        # from active connections
        for _queue_elem in self._measurements_queue.queue:
            reports: List[MillicarUeSingleReport] = _queue_elem
            for _single_report in reports:
                _rnti = _single_report.rnti
                if _rnti is not None:
                    _rnti_list.update([_rnti])
                if _single_report.serving_sinr_reports is not None:
                    for _single_meas in _single_report.serving_sinr_reports.list_of_measurements:
                        _rnti_list.update([_single_meas.peer_rnti])
                if _single_report.sinr_reports is not None:
                    for _single_meas in _single_report.sinr_reports.list_of_measurements:
                        _rnti_list.update([_single_meas.peer_rnti])
        return _rnti_list

    def _get_peer_measurement_instance(self, queue_ind: int, all_rntis: List[int]):
        reports: List[MillicarUeSingleReport] = self._measurements_queue.queue[queue_ind]
        _nr_rntis = len(all_rntis)
        # square matrix containg sinr for each pair; to be used to decide the relay
        sinr_table = np.zeros((_nr_rntis, _nr_rntis), dtype=int)
        try:
            for _single_report in reports:
                _source_rnti_ind = all_rntis.index(_single_report.rnti)
                if _single_report.sinr_reports is not None:
                    for _meas in _single_report.sinr_reports.list_of_measurements:
                        _dest_rnti_ind = all_rntis.index(_meas.peer_rnti)
                        sinr_table[_source_rnti_ind][_dest_rnti_ind] = _meas.sinr
        except ValueError:
            # do nothing
            pass
        return sinr_table

    def _get_peer_measurements(self) -> np.array:
        _all_rntis = list(sorted(self.get_all_rntis()))
        _queue_size = len(self._measurements_queue.queue)
        _all_sinr_tables = []
        for _ind in range(_queue_size):
            sinr_table = self._get_peer_measurement_instance(_ind, _all_rntis)
            _all_sinr_tables.append(sinr_table)
        return np.array(_all_sinr_tables)

    def agg_peer_measurement(self) -> np.array:
        _measurements = self._get_peer_measurements()
        _agg_sinr_meas = np.mean(_measurements, axis=0)
        return _agg_sinr_meas

    def peer_position(self) -> np.array:
        # get position by the last report
        _all_rntis = list(sorted(self.get_all_rntis()))
        _queue_size = len(self._measurements_queue.queue)
        _nr_rntis = len(_all_rntis)
        distance_matrix = np.full((_nr_rntis, _nr_rntis), dtype=float, fill_value=np.inf)
        if _queue_size > 0:
            reports: List[MillicarUeSingleReport] = self._measurements_queue.queue[_queue_size-1]
            _nr_reports = len(reports)
            for _first_index in range(_nr_reports):
                _first_position_x = reports[_first_index].position_x
                _first_position_y = reports[_first_index].position_y
                _first_position_rnti = reports[_first_index].rnti
                _first_position_rnti_index = _all_rntis.index(_first_position_rnti)
                _connected_rntis = reports[_first_index].get_connected_rntis()
                for _second_index in range(_first_index+1, _nr_reports):
                    _second_position_rnti = reports[_second_index].rnti
                    if _second_position_rnti in _connected_rntis:
                        _second_position_x = reports[_second_index].position_x
                        _second_position_y = reports[_second_index].position_y
                        _second_position_rnti_index = _all_rntis.index(_second_position_rnti)
                        _distance = abs(_second_position_x - _first_position_x) + \
                                    abs(_second_position_y - _first_position_y)

                        distance_matrix[_first_position_rnti_index][_second_position_rnti_index] = _distance
                        distance_matrix[_second_position_rnti_index][_first_position_rnti_index] = _distance

        return distance_matrix



if __name__ == '__main__':
    queue = Queue(maxsize=3)
    _list = [[0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [0, 7]]
    _arr1 = np.full((3, 3), dtype=int, fill_value=1)
    _arr2 = np.full((3, 3), dtype=int, fill_value=2)
    _arr3 = np.full((3, 3), dtype=int, fill_value=3)
    _all_arrays = [_arr1, _arr2, _arr3]
    _all_arrays_np = np.array(_all_arrays)
    print(_all_arrays_np)
    np.sum()
    # for _i in range(7):
    for _i in _list:
        if queue.full():
            drop = queue.get()
        queue.put(_i)
        print(len(queue.queue))
        # for _elem in queue.queue:
        #     print(_elem[1])


