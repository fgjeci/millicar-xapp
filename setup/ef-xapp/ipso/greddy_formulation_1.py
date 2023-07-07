import numpy as np
from typing import List


class GreedyFormulation():
    def __init__(
            self,
            allUsers,
            mcsTable,
            gnbResources,
            startingAssignment,
            improving_threshold: float = 0,
            handover_cost=1
    ):
        self.improving_threshold = improving_threshold
        self.allUsers = allUsers
        self.consideredUsers = allUsers
        self.mcsTable = mcsTable
        self.gnbResources = gnbResources
        self.startingAssignment = startingAssignment
        self.userAssignedSubset = [-1] * len(allUsers)
        # efs per cell start
        self.efsNumPerGnb = self.startingAssignment.sum(axis=1)
        # progressing assignment table
        self.assignmentTable = self.startingAssignment.copy()
        self.mcs_multiply_resources_table = (self.mcsTable.T * self.gnbResources).T

    def get_nodes_assigned_to_cell(self, cellInd: int):
        return [_ind for _ind, _val in enumerate(self.assignmentTable[cellInd]) if _val > 0]

    def get_list_neighboring_cells(self, efInd: int):
        return [_ind for _ind, _val in enumerate(self.mcsTable.T[efInd]) if _val > 0]

    def get_efs_index_list_assigned_to_same_cell(self, efInd: int, cellInd: int):
        _n_j = self.get_nodes_assigned_to_cell(cellInd)
        return [_i for _i in _n_j if _i != efInd]

    def calculate_throughput_in_cell_table(self):
        # In case we have exhausted all the assignments
        # if len(usersAssignedSubset) == 0:
        #     return None
        # if assignmentTable is None:
        #     assignmentTable = self.startingAssignment.copy()
        # filter by subset passed in the function and get the mcs
        _indexListOfAssignedSubset = [_ind for _ind, _val in enumerate(self.userAssignedSubset) if _val == -1]
        # _indexListOfNotAssignedSubset = [_ind for _ind, _val in enumerate(usersAssignedSubset) if _val != -1]
        _mcs_assignment_table = (self.mcsTable * self.assignmentTable).T[_indexListOfAssignedSubset]
        _nr_assigned_efs_per_cell = self.assignmentTable.sum(axis=1)

        return np.nan_to_num(
            (_mcs_assignment_table * self.gnbResources).T), _nr_assigned_efs_per_cell, _indexListOfAssignedSubset

    def get_changed_throughput_per_user(self, complete_matrix, n_j_cap_list: List[int], cellInd: int):
        _result_map = map(lambda _ef_ind:
                          np.nansum(complete_matrix[self.get_efs_index_list_assigned_to_same_cell(_ef_ind, cellInd)]),
                          n_j_cap_list)
        return np.array(list(_result_map))

    def get_lost_throughput_neigh_user(self, complete_matrix, neigh_cell_ind):
        _list_efs_in_neigh_node = self.get_nodes_assigned_to_cell(neigh_cell_ind)
        _total_lost = np.nansum(complete_matrix[_list_efs_in_neigh_node])
        return _total_lost

    def get_alpha_values(self, cellInd: int, n_j_cap_list, efs_per_cell):
        # _n_j_cap_list = self.get_nodes_assigned_to_cell(cellInd)
        _alpha_values = np.array((list(map(lambda _ef_ind: np.array(list(map(lambda _neigh_cell_id:
                                                                             self.mcs_multiply_resources_table[
                                                                                 _neigh_cell_id][_ef_ind] / (
                                                                                         efs_per_cell[
                                                                                             _neigh_cell_id] + 1) -
                                                                             self.mcs_multiply_resources_table[cellInd][
                                                                                 _ef_ind] / (efs_per_cell[cellInd])
                                                                             ,
                                                                             self.get_list_neighboring_cells(
                                                                                 _ef_ind)))),
                                           n_j_cap_list))))
        return _alpha_values
        # _starting_throughput = throughput_table[cellInd] / efs_per_cell[cellInd]
        # _ending_throughput = throughput_table.T / (efs_per_cell + 1)
        # return _ending_throughput.T - _starting_throughput

    def get_beta_values(self, cellInd: int, n_j_cap_list: np.ndarray, efs_per_cell: np.ndarray):
        # 1/(A_j_cap -1) - (1-A_j_cap)
        _efs_per_cell_change_factor = 1 / ((efs_per_cell - 1) * efs_per_cell)
        _efs_per_cell_change_factor[_efs_per_cell_change_factor == np.inf] = np.nan
        _complete_matrix = self.mcs_multiply_resources_table.T * _efs_per_cell_change_factor
        # beta_i vector
        # N_j_cap list
        # _n_j_cap_list = self.get_nodes_assigned_to_cell(cellInd)

        # for each i in  n_j_cap, we filter from the complete matrix all the efs assigned to the same cell;
        # eventually we make a sum of throughput for these efs
        _changed_throughput = self.get_changed_throughput_per_user(_complete_matrix, n_j_cap_list, cellInd)
        return _changed_throughput

    def get_gama_values(self, cellInd: int, n_j_cap_list, efs_per_cell):
        # 1/(A_j_cap + 1) - (1-A_j_cap)
        _efs_per_cell_change_factor = 1 / ((efs_per_cell + 1) * efs_per_cell)
        _efs_per_cell_change_factor[_efs_per_cell_change_factor == np.inf] = np.nan
        _complete_matrix = self.mcs_multiply_resources_table.T * _efs_per_cell_change_factor
        # N_j_cap list
        # _n_j_cap_list = self.get_nodes_assigned_to_cell(cellInd)

        _gama = np.array(list(map(lambda _ef_ind: np.array(
            list(map(lambda _neigh_cell_id: self.get_lost_throughput_neigh_user(_complete_matrix,
                                                                                _neigh_cell_id),
                     self.get_list_neighboring_cells(_ef_ind)))), n_j_cap_list)))

        return _gama

    def lowest_throughput_cell_index(self):
        # get throughput initially
        _throughput_table, _efs_per_cell, _remaining_efs_index = self.calculate_throughput_in_cell_table()
        # filter among the not considered user - not decided what to do
        # _indexListOfAssignedSubset = [_ind for _ind, _val in enumerate(self.usersAssignedSubset) if _val == -1]
        # get the index of row(cell id) and column ind (ef id) from the lowest throughput
        _complete_matrix = (_throughput_table.T / _efs_per_cell).T
        _arg_min_list = np.argwhere(_complete_matrix == np.min(_complete_matrix[_complete_matrix > 0]))
        if len(_arg_min_list) > 1:
            (_i, _j) = _arg_min_list[0]
        else:
            # it means we have only 1 data
            _i, _j = _arg_min_list[0][0], _arg_min_list[0][1]

        # Here we have to remap _j to the original the assignment matrix, since it makes reference to filterred matrix
        _j = _remaining_efs_index[_j]

        _n_j_cap_list = self.get_nodes_assigned_to_cell(_i)
        _alpha_values = self.get_alpha_values(_i, _n_j_cap_list, _efs_per_cell)
        _beta_values = self.get_beta_values(_i, _n_j_cap_list, _efs_per_cell)
        _gama_values = self.get_gama_values(_i, _n_j_cap_list, _efs_per_cell)
        _sigma_values = (_alpha_values.T + _beta_values) / (_gama_values.T + 1)
        _sigma_arg_max_list = np.argwhere(_sigma_values == np.max(_sigma_values))
        if len(_sigma_arg_max_list) > 1:
            (_sigma_i, _sigma_j) = _sigma_arg_max_list[0]

        else:
            # it means we have only 1 data
            _sigma_i, _sigma_j = _sigma_arg_max_list[0][0], _sigma_arg_max_list[0][1]

        _dest_node_j = self.get_list_neighboring_cells(_j)[_sigma_j]

        # check if the sigma value is above the improvement threshold
        if _sigma_values[_sigma_i][_sigma_j] > self.improving_threshold:
            self.userAssignedSubset[_j] = _dest_node_j
            self.assignmentTable[_i][_j] = 0
            self.assignmentTable[_dest_node_j][_j] = 1
        else:
            # if there is no improvement we just insert it to the considered nodes and move on
            self.userAssignedSubset[_j] = _i
        print(_gama_values)

    def optimize(self) -> List[int]:
        while self.userAssignedSubset.count(-1) > 0:
            self.lowest_throughput_cell_index()
        return self.userAssignedSubset
