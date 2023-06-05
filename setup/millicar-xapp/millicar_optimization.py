import numpy as np
from typing import List, Tuple
from operator import itemgetter
from millicar_pre_optimize import MillicarPreoptimize


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

    def choose_best_relay_goodness(self):
        # the choosing strategy is based upon the best value of goodness
        # return the tuple (rnti, goodness) with highest goodness
        # return max(self.relay_nodes_rnti_goodness, key=itemgetter(1))
        return max(filter(lambda x: not np.isnan(x[1]), self.relay_nodes_rnti_goodness),
                   key=itemgetter(1))

    def choose_best_relay_position(self):
        # the choosing strategy is based upon the shortest path
        # return min(self.relay_nodes_distance, key=itemgetter(1))
        return min(filter(lambda x: not np.isnan(x[1]), self.relay_nodes_distance),
                   key=itemgetter(1))


class MillicarFormulation:
    def __init__(
            self,
            preoptimize
    ):
        self.preoptimize: MillicarPreoptimize = preoptimize

    def _get_goodness_factor(self, sinr_list: List[float]):
        if any([_elem <= 0 for _elem in sinr_list]):
            # not a valid route
            return np.nan
        _reverse_sinr_list = [1 / _single_sinr for _single_sinr in sinr_list]
        _sum_components = sum(_reverse_sinr_list)
        return 1 / _sum_components

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
            _rnti_distance_best_relay_link = _active_link.choose_best_relay_position()
            _relay_rnti = _rnti_distance_best_relay_link[0]
            _source_rnti = _active_link.rnti
            _dest_rnti = _active_link.peer_rnti
            _relay_path_list.append([_source_rnti, _dest_rnti, _relay_rnti])
        return _relay_path_list

    def _choose_relay_paths(self, active_links_with_relays: List[ActiveLinkRelayList]):
        # this shall be the code that shall select the best realy paths
        # for the moment we select them independently and by the best goodness factor
        _relay_path_list: List[List[int, int, int]] = []  # source , destination , relay
        for _active_link in active_links_with_relays:
            _rnti_goodness_best_relay_link = _active_link.choose_best_relay_goodness()
            _relay_rnti = _rnti_goodness_best_relay_link[0]
            _source_rnti = _active_link.rnti
            _dest_rnti = _active_link.peer_rnti
            _relay_path_list.append([_source_rnti, _dest_rnti, _relay_rnti])
        return _relay_path_list

    def optimize_closest_node(self):
        _need_relays: List[tuple[int, int, float, float]] = self.preoptimize.get_need_relay_links()
        _relay_paths_chosen: List[List[int, int, int]] = []
        if len(_need_relays) > 0:
            _all_rntis: List[int] = list(sorted(self.preoptimize.get_all_rntis()))
            _all_peer_positions = self.preoptimize.peer_position()
            _active_links_with_relays: List[ActiveLinkRelayList] = []
            # calculate the relays that can be done and the cost
            for _single_relay in _need_relays:
                rnti = _single_relay[0]
                peer_rnti = _single_relay[1]
                # tuple (relay_rnti, path shortest distance)
                _all_relay_rnti_distance = self._get_path_part_relay_rnti_distance_tuples(rnti, peer_rnti, _all_rntis,
                                                                                          _all_peer_positions)
                _active_links_with_relays.append(ActiveLinkRelayList(rnti=rnti, peer_rnti=peer_rnti,
                                                                     relay_nodes_distance=_all_relay_rnti_distance))
            _relay_paths_chosen = self._choose_relay_paths_distance(_active_links_with_relays)
        return _relay_paths_chosen

    def optimize(self):
        _need_relays: List[tuple[int, int, float, float]] = self.preoptimize.get_need_relay_links()
        _relay_paths_chosen: List[List[int, int, int]] = []
        if len(_need_relays) > 0:
            _all_rntis: List[int] = list(sorted(self.preoptimize.get_all_rntis()))
            # measurements of signal strength
            _all_peer_measurements = self.preoptimize.agg_peer_measurement()
            _active_links_with_relays: List[ActiveLinkRelayList] = []
            # calculate the relays that can be done and the cost
            for _single_relay in _need_relays:
                rnti = _single_relay[0]
                peer_rnti = _single_relay[1]
                # tuple (relay_rnti, path goodness)
                _all_relay_rnti_goodness = self._get_path_part_relay_rnti_goodness_tuples(rnti, peer_rnti, _all_rntis,
                                                                                          _all_peer_measurements)
                _active_links_with_relays.append(ActiveLinkRelayList(rnti=rnti, peer_rnti=peer_rnti,
                                                                     relay_nodes_rnti_goodness=_all_relay_rnti_goodness))
            _relay_paths_chosen = self._choose_relay_paths(_active_links_with_relays)
        return _relay_paths_chosen


if __name__ == '__main__':
    _all_rntis = [1, 2, 3, 4]
    rnti = 1
    peer_rnti = 2
    _potential_relay_nodes = [_rnti for _rnti in _all_rntis if _rnti not in [rnti, peer_rnti]]
    print(_potential_relay_nodes)
