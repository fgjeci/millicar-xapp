from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Mapping, Union

import numpy as np
from operator import itemgetter

_IMSI_FIELD = 'imsi'
_MCS_FIELD = 'mcs'
_MEASUREMENTS_FIELD = 'meas'
_CELLID_FIELD = 'cellId'
_USER_MEASUREMENTS_FIELD = 'userMeasurements'
_USER_ASSIGNMENTS_FIELD = 'userAssignments'
_GNB_RESOUCES = 'gnbResources'


class Measurement:
    def __init__(self, cellId: int = -1, mcs: int = -1, dictData: Dict[str, int] = None):
        if dictData is not None:
            self.cellId = dictData.get(_CELLID_FIELD)
            self.mcs = dictData.get(_MCS_FIELD)
        else:
            self.cellId = cellId
            self.mcs = mcs

    def __repr__(self) -> str:
        return f"(cellId={self.cellId}, mcs={self.mcs})"


class UserMeasurements:
    def __init__(self, imsi: int = -1, measurements: List[Measurement] = [],
                 dictData: Mapping[str, Union[int, List[Mapping[str, int]]]] = None):
        if dictData is not None:
            self.imsi = dictData.get(_IMSI_FIELD)
            self.measurements = []
            measurements = dictData.get(_MEASUREMENTS_FIELD)
            if isinstance(measurements, list):
                for measurementDict in measurements:
                    self.measurements.append(Measurement(dictData=measurementDict))
        else:
            self.imsi = imsi
            self.measurements = measurements

    def __repr__(self) -> str:
        return f"(cellId={self.imsi})"


class CellMeasurements:
    def __init__(self, cellid: int = 0, userMeasurements: List[UserMeasurements] = [],
                 dictData: Mapping[str, Union[int, List[Mapping[str, List[Mapping[str, int]]]]]] = None):
        if dictData is not None:
            self.cellid = dictData.get(_CELLID_FIELD)
            self.userMeasurements = []
            allUsersMeasurements = dictData.get(_USER_MEASUREMENTS_FIELD)
            if isinstance(allUsersMeasurements, list):
                for singleUserMeasurements in allUsersMeasurements:
                    self.userMeasurements.append(UserMeasurements(dictData=singleUserMeasurements))
        else:
            self.cellid = cellid
            self.userMeasurements = userMeasurements

    def getEfsImsi(self) -> set:
        return set([userMeasurement.imsi for userMeasurement in self.userMeasurements])

    def getCellsId(self) -> set:
        _cellIds = []
        for userMeasurement in self.userMeasurements:
            for singleUserMeasurement in userMeasurement.measurements:
                _cellIds.append(singleUserMeasurement.cellId)
        return set(_cellIds)

    def __repr__(self) -> str:
        return f"(cellId={self.cellid})"


class Assignment:
    def __init__(self, imsi: int = -1, mcs: int = -1, dictData: Dict[str, int] = None):
        if dictData is not None:
            self.imsi = dictData.get(_IMSI_FIELD)
            self.mcs = dictData.get(_MCS_FIELD)
        else:
            self.imsi = imsi
            self.mcs = mcs

    def __repr__(self) -> str:
        return f"(imsi={self.imsi}, mcs={self.mcs})"


class CellAssignments:
    def __init__(self, cellid: int = 0, userAssignments: List[Assignment] = [],
                 dictData: Mapping[str, Union[int, List[Mapping[str, int]]]] = None):
        if dictData is not None:
            self.cellid = dictData.get(_CELLID_FIELD)
            self.userAssignments = []
            allAssignments = dictData.get(_USER_ASSIGNMENTS_FIELD)
            if isinstance(allAssignments, list):
                for singleUserAssignment in allAssignments:
                    self.userAssignments.append(Assignment(dictData=singleUserAssignment))
        else:
            self.cellid = cellid
            self.userAssignments = userAssignments

    def getEfsImsi(self) -> set:
        return set([userAssignment.imsi for userAssignment in self.userAssignments])

    def __repr__(self) -> str:
        return f"(cellId={self.cellid})"


class EfAssignDataPreparation:
    def __init__(
            self,
            # imsi, mcs and num symb used by user
            assignments: List[Mapping[str, Union[int, List[Mapping[str, int]]]]] = [],
            # cellid: source cell, imsi:int, meas: List [cellid: 2, mcs: 26]
            measurements: List[Mapping[str, Union[int, List[Mapping[str, Union[int, Mapping[str, int]]]]]]] = [],
            gnbAvailableResources: List[Dict[str, int]] = []
        ):
        self.assignments = assignments
        self.measurements = measurements
        self.resources = gnbAvailableResources

        # Creating the table of mcs by user
        self.cellsAssignments = self.get_cells_assignment()
        self.cellsMeasurements = self.get_cells_measurements()

        self.allImsi = sorted(self.get_all_efs_imsi())
        self.allCells = sorted(self.get_all_cells())

        self.fill_missing_data()

        self.nrGnbs = len(self.allCells)
        self.nrEfs = len(self.allImsi)
        self.assignmentsArray = np.full(self.nrEfs, dtype=int, fill_value=-1)
        self.assignmentsArrayMap = [[(-1, -1) for _closNeighInd in range(3)] for _efInd in range(self.nrEfs)]
        self.mcsTable = np.zeros((self.nrGnbs, self.nrEfs), dtype=int)
        self.insert_data_in_mcs_table()
        # assignment table (binary)

        self.assignmentsTable = np.zeros((self.nrGnbs, self.nrEfs), dtype=int)
        self.insert_assignment_in_table()
        # assignment array -> have size as nrEFs and shall contain the index of the assigned gnb for each ef

        self.insert_assignment_in_array()
        self.insert_measurements_in_array()
        # Gnb available resource
        self.gnbResources = np.zeros(self.nrGnbs, dtype=int)
        self.insert_gnb_assignment()
        # efs per cell start
        self.efsNumPerGnb = self.assignmentsTable.sum(axis=1)
        self.startingThroughput = self.calculate_throughput()

    def report_data_in_file(self, filename:str):
        with open(filename, "a+") as file: 
            for _imsi_ind_assign, _imsi_assign in enumerate(self.allImsi):
                _cell_id_ind_assign = self.assignmentsArray[_imsi_ind_assign]
                _cell_id_assign = self.allCells[_cell_id_ind_assign]
                _mcs_assign = self.mcsTable[_cell_id_assign][_imsi_ind_assign]
                _serving_cell_str = str(_imsi_assign) + "," + str(_cell_id_assign) + "," + str(_mcs_assign)
                _bool_cell_ind_meas = self.mcsTable.T[_imsi_ind_assign]>0
                _neigh_cell_report_str = ""
                for _neigh_cell_ind in list(self.allCells[_bool_cell_ind_meas]):
                    _neigh_cell_id = self.allCells[_neigh_cell_ind]
                    _neigh_cell_mcs = self.mcsTable[_neigh_cell_ind][_imsi_ind_assign]
                    _neigh_cell_report_str += "," + str(_neigh_cell_id) + "," + str(_neigh_cell_mcs)
                file.write(_serving_cell_str + _neigh_cell_report_str)
        

    def get_cells_assignment(self) -> List[CellAssignments]:
        return [CellAssignments(dictData=assignment) for assignment in self.assignments]

    def get_cells_measurements(self):
        return [CellMeasurements(dictData=measurement) for measurement in self.measurements]

    def get_all_efs_imsi(self) -> set:
        _imsiList = set()
        for cellAssignment in self.cellsAssignments:
            _imsiList.update(cellAssignment.getEfsImsi())
        for cellMeasurements in self.cellsMeasurements:
            _imsiList.update(cellMeasurements.getEfsImsi())
        return _imsiList

    def get_all_cells(self) -> set:
        _cells = set([cellAssignment.cellid for cellAssignment in self.cellsAssignments])
        for cellMeasurement in self.cellsMeasurements:
            _cells.add(cellMeasurement.cellid)
            _cells.update(cellMeasurement.getCellsId())
        return _cells

    def fill_missing_data(self):
        # assignment
        for _cell_id in self.allCells:
            if len(list(filter(lambda _assing: _assing.cellid == _cell_id, self.cellsAssignments))) == 0:
                # if missing we add it
                self.cellsAssignments.append(CellAssignments(cellid=_cell_id))
            if len(list(filter(lambda _assing: _assing.cellid == _cell_id, self.cellsMeasurements))) == 0:
                # if missing we add it
                self.cellsMeasurements.append(CellMeasurements(cellid=_cell_id))

    def insert_data_in_mcs_table(self):
        for cellAssignments in self.cellsAssignments:
            for userAssignment in cellAssignments.userAssignments:
                _nodeInd = self.allImsi.index(userAssignment.imsi)
                _filterNonNoneInAssignmentArrayMap = self.assignmentsArrayMap[_nodeInd].index((-1, -1))
                self.mcsTable[self.allCells.index(cellAssignments.cellid)] \
                    [_nodeInd] = userAssignment.mcs

                _mappedCellIndex = max([_elem[1] for _elem in self.assignmentsArrayMap[_nodeInd]]) + 1
                _tupleToAdd = (cellAssignments.cellid, _mappedCellIndex)

                if (_filterNonNoneInAssignmentArrayMap > 2):
                    # tuple real cell id and
                    self.assignmentsArrayMap[_nodeInd].append(_tupleToAdd)
                else:
                    self.assignmentsArrayMap[_nodeInd][_mappedCellIndex] = _tupleToAdd

        for cellMeasurements in self.cellsMeasurements:
            for userMeasurements in cellMeasurements.userMeasurements:
                for userMeasurement in userMeasurements.measurements:
                    _nodeInd = self.allImsi.index(userMeasurements.imsi)
                    self.mcsTable[self.allCells.index(userMeasurement.cellId)][
                        _nodeInd] = userMeasurement.mcs[len(userMeasurement.mcs)-1] if isinstance(userMeasurement.mcs, list) else userMeasurement.mcs

                    _filterNonNoneInAssignmentArrayMap = self.assignmentsArrayMap[_nodeInd].index((-1, -1)) if self.assignmentsArrayMap[_nodeInd].count((-1, -1)) else -1
                    _cellIdExists = any([item for item in self.assignmentsArrayMap[_nodeInd]if item[0] == userMeasurement.cellId])
                    _mappedCellIndex = max(self.assignmentsArrayMap[_nodeInd], key=itemgetter(1))[1] + 1
                    _tupleToAdd = (userMeasurement.cellId, _mappedCellIndex)
                    if _cellIdExists:
                        continue
                    if (_filterNonNoneInAssignmentArrayMap > 2) | (_filterNonNoneInAssignmentArrayMap == -1):
                        # tuple real cell id and
                        self.assignmentsArrayMap[_nodeInd].append(_tupleToAdd)
                    else:
                        self.assignmentsArrayMap[_nodeInd][_mappedCellIndex] = _tupleToAdd

    def insert_assignment_in_table(self):
        for cellAssignments in self.cellsAssignments:
            for userAssignment in cellAssignments.userAssignments:
                self.assignmentsTable[
                    self.allCells.index(cellAssignments.cellid)][
                    self.allImsi.index(userAssignment.imsi)] = 1

    def insert_assignment_in_array(self):
        for cellAssignments in self.cellsAssignments:
            for userAssignment in cellAssignments.userAssignments:
                self.assignmentsArray[self.allImsi.index(userAssignment.imsi)] = self.allCells.index(cellAssignments.cellid)

    def insert_measurements_in_array(self):
        for cellMeasurement in self.cellsMeasurements:
            for userMeasurement in cellMeasurement.userMeasurements:
                userMeasurement

    def insert_gnb_assignment(self):
        for _ind, _cell in enumerate(self.allCells):
            # First element of tuple has cell id
            # List of tuple of the filtering
            _filterListCellId = list(filter(lambda _tupleElem: _tupleElem.get(_CELLID_FIELD) == _cell, self.resources))
            if len(_filterListCellId) != 1:
                pass
                # print("Error, there should be single entries for cell id")
                ### We insert random number of resources
                # self.gnbResources[_ind] = int(np.random.uniform(low=30) * 16 * 14 * 10)
            else:
                # the number of resources should be in the second index of the tuple
                self.gnbResources[_ind] = _filterListCellId[0].get(_GNB_RESOUCES)

    def _get_next_calculate_throughput(self, mappedCellId: List):
        _assignArrayMap = self.assignmentsArrayMap[mappedCellId[0]]
        _iterator_filter = filter(lambda realMapCellIdPair: realMapCellIdPair[1] == mappedCellId[1], _assignArrayMap)
        _iterator_list = list(_iterator_filter)
        # means it does not find the cell id in the map
        # might happen due to data incompletion

        if len(_iterator_list) == 0:
            return [-1, -1]
        return _iterator_list[0]
        # return next(_iterator_filter)

    def _get_user_mcs_by_index_cell_id(self, _indexCellIdArray):
        if (_indexCellIdArray[1] == -1) | (_indexCellIdArray[0] == -1):
            return 0
        _ret = self.mcsTable[_indexCellIdArray[1]][_indexCellIdArray[0]]
        return _ret

    def calculate_throughput(self, assignmentArray: np.ndarray = None):
        # calculation with the assignment matrix
        # calculation with the assignment array
        if assignmentArray is not None:
            _assignmentArray = assignmentArray
        else:
            _assignmentArray = self.assignmentsArray
        _assigmentArrayIndexValueArray = np.array([[_i[0], _v] for _i, _v in np.ndenumerate(_assignmentArray)])
        if len(_assigmentArrayIndexValueArray) == 0:
            return []
        _gnbResourcesByCellIndex = np.vectorize(lambda _cellId: 0 if _cellId==-1 else self.gnbResources[_cellId])(_assignmentArray)
        _gnbNumberAssignedUsersByCellIndex = np.vectorize(lambda _cellId: 0 if _cellId == -1 else
                                                          np.count_nonzero(_assignmentArray == _cellId)) \
                                                        (_assignmentArray)
        _mcsPerUser = np.apply_along_axis(lambda _indexCellIdArray:
                                   self._get_user_mcs_by_index_cell_id(_indexCellIdArray),
                                          1, _assigmentArrayIndexValueArray)
        return _mcsPerUser*_gnbResourcesByCellIndex/_gnbNumberAssignedUsersByCellIndex
        # self.startingThroughput = self.mcsTable*_gnbResourcesByCellIndex/_gnbNumberAssignedUsersByCellIndex

    def cost_function(self, A: np.ndarray):
        # A is the vector of assignments
        # shall return an np array containing the max cost (- gain) for each of the users
        # the number of dimensions is equal to the number of efs
        # number of assigned efs per each cell
        # efs_num_per_cell = np.array([np.count_nonzero(A == cell) for cell in self.allCells])
        # # we have to calculate the destination throughput per user
        _throughputPerUserPerAssignment = np.apply_along_axis(self.calculate_throughput, axis=1, arr=A)
        return np.max(self.startingThroughput - _throughputPerUserPerAssignment, axis=1)

    def get_imsi_positive_mcs_possible_cell_assignment_index(self, imsi: int)-> List[int]:
        _assignment_cell = self.assignmentsArray[self.allImsi.index(imsi)]
        _all_cells = [_assignment_cell]
        for cellMeasurements in self.cellsMeasurements:
            for cellMeas in cellMeasurements.userMeasurements:
                if cellMeas.imsi == imsi:
                    for _neighbourCell in cellMeas.measurements:
                        if _neighbourCell.mcs >0:
                            _all_cells.append(self.allCells.index(_neighbourCell.cellId))
        return _all_cells

    
    def cost_function_greedy(self, A: np.ndarray):
        _throughputPerUserPerAssignment = np.apply_along_axis(self.calculate_throughput, axis=1, arr=A)