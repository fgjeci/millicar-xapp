import numpy as np
from typing import List, Tuple
from operator import itemgetter
from millicar_pre_optimize import MillicarPreoptimize
import pickle
import datetime

_JSON_RNTI = "Rnti"
_JSON_PEER_RNTI = "PeerRnti"
_JSON_SNR_RELAY_NODES_RNTI = 'SnrRelayNodesRnti'
_JSON_SNR_RELAY_NODES_GOODNESS = 'SnrRelayNodesGoodness'
_JSON_DISTANCE_RELAY_NODES_RNTI = 'DistanceRelayNodesRnti'
_JSON_DISTANCE_RELAY_NODES_GOODNESS = 'DistanceRelayNodesGoodness'
_JSON_GOODNESS = "RelayGoodness"
_JSON_DISTANCE = "RelayDistance"

_JSON_ACTIVE_LINK_RELAY_LIST = "RelayList"
_JSON_PLMN = "Plmn"
_JSON_TIMESTAMP = 'time'

class ActiveLinkRelayList:
    def __init__(
            self,
            rnti: int,
            peer_rnti: int,
            relay_nodes_rnti_goodness: List[Tuple[int, float]] = [],  # relay rnti and path goodness
            relay_nodes_distance: List[Tuple[int, float]] = [] # relay rnti, x & y position
    ):
        self.rnti = rnti
        self.peer_rnti = peer_rnti
        self.relay_nodes_rnti_goodness = relay_nodes_rnti_goodness
        self.relay_nodes_distance = relay_nodes_distance

    # get snr of main link
    def get_original_link_goodness(self)->Tuple[int, float]:
        _filter_main_link = list(filter(lambda _single_link: (_single_link[0] == int(np.iinfo(np.uint16).max)) \
                                                    , self.relay_nodes_rnti_goodness))
        if len(_filter_main_link)>0:
            return _filter_main_link[0]
        return (int(np.iinfo(np.uint16).max), -1)

    def choose_best_relay_goodness(self, main_link_goodness_threshold:float = -1) -> Tuple[int, float]:
        # the choosing strategy is based upon the best value of goodness
        # return the tuple (rnti, goodness) with highest goodness
        # return max(self.relay_nodes_rnti_goodness, key=itemgetter(1))
        _main_link_goodness = self.get_original_link_goodness()
        # print("threshold " + str(main_link_goodness_threshold))
        # print(_main_link_goodness)
        if _main_link_goodness[1] == -1:
            return max(filter(lambda x: not np.isnan(x[1]), self.relay_nodes_rnti_goodness),
                    key=itemgetter(1))
        else:
            # means exist the main link goodness factor
            # check if main link goodness (snr) is above threshold
            if _main_link_goodness[1] > main_link_goodness_threshold:
                # return (int(np.iinfo(np.uint16).max))
                return _main_link_goodness
            else:
                # retunr the max among all possible relays
                # considering the main link as well
                try:
                    return max(filter(lambda x: not np.isnan(x[1]), self.relay_nodes_rnti_goodness),
                        key=itemgetter(1))
                except ValueError:
                    return _main_link_goodness

    def choose_best_relay_position(self):
        # the choosing strategy is based upon the shortest path
        # return min(self.relay_nodes_distance, key=itemgetter(1))
        return min(filter(lambda x: not np.isnan(x[1]), self.relay_nodes_distance),
                   key=itemgetter(1))

    def choose_best_relay_position_threshold(self, main_link_goodness_threshold:float = -1) -> Tuple[int, float]:
        # the choosing strategy is based upon the shortest path
        _main_link_goodness = self.get_original_link_goodness()
        # print("threshold pos " + str(main_link_goodness_threshold))
        # print(_main_link_goodness)
        # print(self.relay_nodes_distance)
        if _main_link_goodness[1] == -1:
            return min(filter(lambda x: not np.isnan(x[1]), self.relay_nodes_distance),
                    key=itemgetter(1))
        else:
            # means exist the main link goodness factor
            # check if main link goodness (snr) is above threshold
            if _main_link_goodness[1] > main_link_goodness_threshold:
                # return (int(np.iinfo(np.uint16).max))
                return _main_link_goodness
            else:
                # retunr the min distance among all possible relays
                # considering the main link as well
                return min(filter(lambda x: not np.isnan(x[1]), self.relay_nodes_distance),
                    key=itemgetter(1))

    def to_dict(self):
        _filter_goodness = list(filter(lambda _single_link: (not np.isnan(_single_link[1]) ) \
                                                    , self.relay_nodes_rnti_goodness))
        _filter_distance_goodness = list(filter(lambda _single_link: (not np.isinf(_single_link[1]) ) \
                                                    , self.relay_nodes_distance))
        # return {
        #     _JSON_RNTI: self.rnti,
        #     _JSON_PEER_RNTI: self.peer_rnti,
        #     _JSON_SNR_RELAY_NODES_RNTI: [_tuple[0] for _tuple in _filter_goodness],
        #     _JSON_SNR_RELAY_NODES_GOODNESS: [_tuple[1] for _tuple in _filter_goodness],
        #     _JSON_DISTANCE_RELAY_NODES_RNTI: [_tuple[0] for _tuple in _filter_distance_goodness],
        #     _JSON_DISTANCE_RELAY_NODES_GOODNESS: [_tuple[1] for _tuple in _filter_distance_goodness]
        # }
        return {
            _JSON_RNTI: self.rnti,
            _JSON_PEER_RNTI: self.peer_rnti,
            _JSON_GOODNESS: [[_tuple[0], _tuple[1]] for _tuple in _filter_goodness],
            _JSON_DISTANCE: [[_tuple[0], _tuple[1]] for _tuple in _filter_distance_goodness]
        }

class MillicarFormulation:
    def __init__(
            self,
            preoptimize,
            plmn: str = "110"
    ):
        self.preoptimize: MillicarPreoptimize = preoptimize
        self.plmn = plmn

    # return goodness factor from list of sinr
    def _get_goodness_factor(self, sinr_list: List[float]) -> float:
        if any([_elem <= 0 for _elem in sinr_list]):
            # not a valid route
            return np.nan
        _reverse_sinr_list = [1 / _single_sinr for _single_sinr in sinr_list]
        _sum_components = sum(_reverse_sinr_list)
        return 1 * len(sinr_list) / _sum_components

    def _get_path_part_relay_rnti_goodness_tuples(self, rnti: int, peer_rnti: int, all_rntis: List[int],
                                                  all_peer_measurements: np.array) -> List[Tuple[int, float]]:
        _relay_paths_goodness: List[Tuple[int, float]] = []
        rnti_index = all_rntis.index(rnti)
        peer_rnti_index = all_rntis.index(peer_rnti)
        # only 1 node shall serve as relay in this scenario
        _potential_relay_nodes = [_rnti for _rnti in all_rntis if _rnti not in [rnti, peer_rnti]]
        # for each potential relay node we calculate the weighted sinr
        for _pot_relay_node_rnti in _potential_relay_nodes:
            try:
                _pot_relay_index = all_rntis.index(_pot_relay_node_rnti)
                _rnti_relay_sinr = all_peer_measurements[rnti_index][_pot_relay_index]
                _relay_peer_rnti_sinr = all_peer_measurements[_pot_relay_index][peer_rnti_index]
                # reverse path
                _relay_rnti_sinr = all_peer_measurements[_pot_relay_index][rnti_index]
                _peer_rnti_relay_sinr = all_peer_measurements[peer_rnti_index][_pot_relay_index]
                # goodness factor as an entire path
                # _goodness_factor = self._get_goodness_factor([_rnti_relay_sinr, _relay_peer_rnti_sinr])
                # considering the reverse path as well
                _goodness_factor = self._get_goodness_factor([_rnti_relay_sinr, _relay_peer_rnti_sinr,
                                                              _relay_rnti_sinr, _peer_rnti_relay_sinr])
                _relay_paths_goodness.append((_pot_relay_node_rnti, _goodness_factor))
            except ValueError:
                pass
        # adding main path 
        _rnti_peer_main_sinr = all_peer_measurements[rnti_index][peer_rnti_index]
        _rnti_peer_reverse_sinr = all_peer_measurements[peer_rnti_index][rnti_index]
        _main_path_goodness_factor = self._get_goodness_factor([_rnti_peer_main_sinr, 
                                                                _rnti_peer_reverse_sinr])
        _relay_paths_goodness.append((int(np.iinfo(np.uint16).max), 
                                      _main_path_goodness_factor))
        
        # print("Relay")
        # print(_relay_paths_goodness)

        return _relay_paths_goodness

    def _get_path_part_relay_rnti_distance_tuples(self, rnti: int, peer_rnti: int, all_rntis: List[int],
                                                  all_peer_distance: np.array) -> List[Tuple[int, float]]:
        _relay_paths_distance: List[Tuple[int, float]] = []
        rnti_index = all_rntis.index(rnti)
        peer_rnti_index = all_rntis.index(peer_rnti)
        # only 1 node shall serve as relay in this scenario
        _potential_relay_nodes = [_rnti for _rnti in all_rntis if _rnti not in [rnti, peer_rnti]]
        for _pot_relay_node_rnti in _potential_relay_nodes:
            try:
                _pot_relay_index = all_rntis.index(_pot_relay_node_rnti)
                _rnti_relay_distance = all_peer_distance[rnti_index][_pot_relay_index]
                _relay_peer_rnti_distance = all_peer_distance[_pot_relay_index][peer_rnti_index]
                _total_distance = _rnti_relay_distance + _relay_peer_rnti_distance
                _relay_paths_distance.append((_pot_relay_node_rnti, _total_distance))
            except ValueError:
                pass

        return _relay_paths_distance

    def _choose_relay_paths_distance(self, active_links_with_relays: List[ActiveLinkRelayList]):
        # this shall be the code that shall select the best realy paths
        # for the moment we select them independently and by the best goodness factor
        _relay_path_list: List[List[int, int, int]] = []  # source , destination , relay
        for _active_link in active_links_with_relays:
            # _rnti_distance_best_relay_link = _active_link.choose_best_relay_position()
            _rnti_distance_best_relay_link = _active_link.choose_best_relay_position_threshold(self.preoptimize.to_relay_threshold)
            _relay_rnti = _rnti_distance_best_relay_link[0]
            _source_rnti = _active_link.rnti
            _dest_rnti = _active_link.peer_rnti
            _inserted: bool = self.preoptimize.set_genuine_link(_source_rnti, _dest_rnti, _relay_rnti)
            if (_inserted):
                # insert in the list to generate the report
                _relay_path_list.append([_source_rnti, _dest_rnti, _relay_rnti])
            
        return _relay_path_list

    def _choose_relay_paths(self, active_links_with_relays: List[ActiveLinkRelayList]):
        # this shall be the code that shall select the best realy paths
        # for the moment we select them independently and by the best goodness factor
        _relay_path_list: List[List[int, int, int]] = []  # source , destination , relay
        for _active_link in active_links_with_relays:
            # Check if main link is above threshold
            # if main link is above threshold we keep main link
            _rnti_goodness_best_relay_link = _active_link.choose_best_relay_goodness(self.preoptimize.to_relay_threshold)
            _relay_rnti = _rnti_goodness_best_relay_link[0]
            _source_rnti = _active_link.rnti
            _dest_rnti = _active_link.peer_rnti
            # insert it to the vector of genuine links
            _inserted: bool = self.preoptimize.set_genuine_link(_source_rnti, _dest_rnti, _relay_rnti)
            if (_inserted):
                # insert in the list to generate the report
                _relay_path_list.append([_source_rnti, _dest_rnti, _relay_rnti])
            
        return _relay_path_list

    # def optimize_closest_node(self):
    #     _need_relays: List[tuple[int, int, float, float]] = self.preoptimize.get_need_relay_links()
    #     _relay_paths_chosen: List[List[int, int, int]] = []
    #     # print("Need relays distance")
    #     # print(_need_relays)
    #     if len(_need_relays) > 0:
    #         _all_rntis: List[int] = list(sorted(self.preoptimize.get_all_rntis()))
    #         _all_peer_positions = self.preoptimize.peer_position()
    #         _active_links_with_relays: List[ActiveLinkRelayList] = []
    #         # calculate the relays that can be done and the cost
    #         for _single_relay in _need_relays:
    #             rnti = _single_relay[0]
    #             peer_rnti = _single_relay[1]
    #             # tuple (relay_rnti, path shortest distance)
    #             # here we have to check whether the link is genuine
    #             # we only relay the genuine link
    #             _original_rnti_peer_tuple = self.preoptimize.get_original_link_tuple(rnti, peer_rnti)
    #             if _original_rnti_peer_tuple == (-1, -1, -1):
    #                 continue
    #             # if the path is an intermediate path, that is is involved a relay node
    #             # we do not change only this part of the path
    #             # but we change the entire relay path and choose a new one
    #             rnti = _original_rnti_peer_tuple[0]
    #             peer_rnti = _original_rnti_peer_tuple[1]
    #             _all_relay_rnti_distance = self._get_path_part_relay_rnti_distance_tuples(rnti, peer_rnti, _all_rntis,
    #                                                                                       _all_peer_positions)
    #             _active_links_with_relays.append(ActiveLinkRelayList(rnti=rnti, peer_rnti=peer_rnti,
    #                                                                  relay_nodes_distance=_all_relay_rnti_distance))
    #         _relay_paths_chosen = self._choose_relay_paths_distance(_active_links_with_relays)
    #     return _relay_paths_chosen

    # def optimize(self):
    #     _need_relays: List[tuple[int, int, float, float]] = self.preoptimize.get_need_relay_links()
    #     _relay_paths_chosen: List[List[int, int, int]] = []
    #     # print("Need relays sinr")
    #     # print(_need_relays)
    #     if len(_need_relays) > 0:
    #         _all_rntis: List[int] = list(sorted(self.preoptimize.get_all_rntis()))
    #         # measurements of signal strength
    #         _all_peer_measurements = self.preoptimize.agg_peer_measurement()
    #         _active_links_with_relays: List[ActiveLinkRelayList] = []
    #         # calculate the relays that can be done and the cost
    #         for _single_relay in _need_relays:
    #             rnti = _single_relay[0]
    #             peer_rnti = _single_relay[1]
    #             # here we have to check whether the link is genuine
    #             # we only relay the genuine link
    #             _original_rnti_peer_tuple = self.preoptimize.get_original_link_tuple(rnti, peer_rnti)
    #             if _original_rnti_peer_tuple == (-1, -1, -1):
    #                 continue
    #             # if the path is an intermediate path, that is is involved a relay node
    #             # we do not change only this part of the path
    #             # but we change the entire relay path and choose a new one
    #             rnti = _original_rnti_peer_tuple[0]
    #             peer_rnti = _original_rnti_peer_tuple[1]
    #             _all_relay_rnti_goodness = self._get_path_part_relay_rnti_goodness_tuples(rnti, peer_rnti, _all_rntis,
    #                                                                                       _all_peer_measurements)
    #             _active_links_with_relays.append(ActiveLinkRelayList(rnti=rnti, peer_rnti=peer_rnti,
    #                                                                  relay_nodes_rnti_goodness=_all_relay_rnti_goodness))
    #         _relay_paths_chosen = self._choose_relay_paths(_active_links_with_relays)
    #     return _relay_paths_chosen
    
    def optimize(self):
        _genuine_links = self.preoptimize.genuine_links_relay
        _relay_paths_chosen: List[List[int, int, int]] = []
        _all_rntis: List[int] = list(sorted(self.preoptimize.get_all_rntis()))
        # measurements of signal strength
        _all_peer_measurements = self.preoptimize.agg_peer_measurement()
        # print(_all_peer_measurements)
        _active_links_with_relays: List[ActiveLinkRelayList] = []
        for _link in _genuine_links:
            _rnti = _link[0]
            _peer_rnti = _link[1]
            _original_rnti_peer_tuple = self.preoptimize.get_original_link_tuple(_rnti, _peer_rnti)
            if _original_rnti_peer_tuple == (-1, -1, -1):
                continue
            # _relay_rnti = _link[2]
            _all_relay_rnti_goodness = self._get_path_part_relay_rnti_goodness_tuples(_rnti, _peer_rnti, _all_rntis,
                                                                                          _all_peer_measurements)
            _active_links_with_relays.append(ActiveLinkRelayList(rnti=_rnti, peer_rnti=_peer_rnti,
                                                                relay_nodes_rnti_goodness=_all_relay_rnti_goodness))
        # traces 
        _map = {_JSON_TIMESTAMP: str(datetime.datetime.now()),
                _JSON_PLMN:self.plmn,
                _JSON_ACTIVE_LINK_RELAY_LIST: [_link_relay_list.to_dict() for _link_relay_list in _active_links_with_relays]}
        pickle_out = open('/home/traces/relay_links_reports.pickle', 'ab+')
        pickle.dump(_map, pickle_out)
        pickle_out.close()
        _relay_paths_chosen = self._choose_relay_paths(_active_links_with_relays)
        return _relay_paths_chosen
    
    def optimize_closest_node(self):
        _genuine_links = self.preoptimize.genuine_links_relay
        _relay_paths_chosen: List[List[int, int, int]] = []
        _all_rntis: List[int] = list(sorted(self.preoptimize.get_all_rntis()))
        # measurements of signal strength
        _all_peer_measurements = self.preoptimize.agg_peer_measurement()
        _all_peer_positions = self.preoptimize.peer_position()
        _active_links_with_relays: List[ActiveLinkRelayList] = []
        for _link in _genuine_links:
            _rnti = _link[0]
            _peer_rnti = _link[1]
            # _relay_rnti = _link[2]
            _original_rnti_peer_tuple = self.preoptimize.get_original_link_tuple(_rnti, _peer_rnti)
            if _original_rnti_peer_tuple == (-1, -1, -1):
                continue
            try: 
                _all_relay_rnti_distance = self._get_path_part_relay_rnti_distance_tuples(_rnti, _peer_rnti, _all_rntis,
                                                                                    _all_peer_positions)
                _all_relay_rnti_goodness = self._get_path_part_relay_rnti_goodness_tuples(_rnti, _peer_rnti, _all_rntis,
                                                                                            _all_peer_measurements)
                _active_links_with_relays.append(ActiveLinkRelayList(rnti=_rnti, peer_rnti=_peer_rnti,
                                                                relay_nodes_distance=_all_relay_rnti_distance, 
                                                                relay_nodes_rnti_goodness=_all_relay_rnti_goodness))
            except ValueError:
                pass
        # traces 
        _map = {_JSON_TIMESTAMP: str(datetime.datetime.now()),
                _JSON_PLMN:self.plmn,
                _JSON_ACTIVE_LINK_RELAY_LIST: [_link_relay_list.to_dict() for _link_relay_list in _active_links_with_relays]}
        pickle_out = open('/home/traces/relay_links_reports.pickle', 'ab+')
        pickle.dump(_map, pickle_out)
        pickle_out.close()
        _relay_paths_chosen = self._choose_relay_paths_distance(_active_links_with_relays)
        return _relay_paths_chosen

if __name__ == '__main__':
    _all_rntis = [1, 2, 3, 4]
    rnti = 1
    peer_rnti = 2
    _potential_relay_nodes = [_rnti for _rnti in _all_rntis if _rnti not in [rnti, peer_rnti]]
    print(_potential_relay_nodes)
