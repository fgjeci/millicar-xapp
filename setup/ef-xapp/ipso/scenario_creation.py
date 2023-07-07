import binascii
import json
import os
from typing import List, Union
import numpy as np
import math
from itertools import permutations, combinations, product
from functools import partial
# import matplotlib.pyplot as plt
from operator import itemgetter
import socket
import asn1

from . import trasform


def getSizePositions():
    siteDistances = [0, 1, 1, 1, 1, 1, 1, np.sqrt(3), np.sqrt(3), np.sqrt(3), np.sqrt(3), np.sqrt(3), np.sqrt(3), 2, 2,
                     2, 2, 2, 2]
    siteAngles = [0, 30, 90, 150, 210, 270, 330, 0, 60, 120, 180, 240, 300, 30, 90, 150, 210, 270, 330]
    bsDistance = 100
    hexagonalRadius = bsDistance / 3
    numBs = 21
    gnbSitePoints = []
    for cellId in range(numBs):
        siteIndex = int(cellId / 3)
        sectorIndex = int(cellId % 3)
        dist = siteDistances[siteIndex]
        angleRad = siteAngles[siteIndex] * math.pi / 180
        point = np.array([bsDistance * dist * math.cos(angleRad), bsDistance * dist * math.sin(angleRad), 0])
        antennaOrientation = 120 * (sectorIndex + 0.5)
        # Add Antenna offset; not same pos
        point[0] += -1 * math.cos(antennaOrientation * math.pi / 180)
        point[1] += -1 * math.sin(antennaOrientation * math.pi / 180)

        #     if (sectorIndex == 0):
        #         point[0] += hexagonalRadius * np.sqrt (0.75)
        #         point[1] += hexagonalRadius / 2
        #     elif (sectorIndex == 1):
        #         point[0] -= hexagonalRadius * np.sqrt (0.75)
        #         point[1] += hexagonalRadius / 2
        #     elif (sectorIndex == 2):
        #         point[1] -= hexagonalRadius;
        gnbSitePoints.append((cellId, point))
    return gnbSitePoints


def attachClosestEnb(efPos, gnbPositions):
    return list(map(lambda ef_pos:
                    np.argmin(list(map(lambda gnbPos: np.linalg.norm(gnbPos[1] - ef_pos[1]),
                                       gnbPositions))), efPos))


def getThreeClosestEnb(efPos, gnbPositions):
    threeClosestEnb = []
    for efpos in efPos:
        _list = list(map(lambda gnbPos: (gnbPos[0],
                                         np.linalg.norm(gnbPos[1] - efpos[1])), gnbPositions))
        _sorted = [_ind for (_ind, _dis) in sorted(_list, key=itemgetter(1))[:3]]
        #         threeClosestEnb.append((efpos[0], efpos[1], _sorted))
        threeClosestEnb.append(_sorted)
    return threeClosestEnb


def getRandomPositionNode(nr_efs, nr_bs, min_x, max_x, min_y, max_y):
    range_x = max_x - min_x
    range_y = max_y - min_y
    efs_pos = []
    for ef in range(nr_bs + 1, nr_bs + nr_efs):
        _x = np.random.uniform() * range_x + min_x
        _y = np.random.uniform() * range_y + min_y
        efs_pos.append((ef, np.array([_x, _y, 0])))
    return efs_pos


def getGain(delta_throughput):
    _v_log_base = 10
    _v_slope = 10
    if (delta_throughput >= 0):
        return float(_v_slope * delta_throughput)
    else:
        return float(-math.log(-delta_throughput + 1, _v_log_base))


def getSingleCellScenario(nr_efs=-1):
    _v_mu = 4
    _v_max_symbols = 14 * pow(2, _v_mu) * 10
    # uniform distribution - we take for granted that at least 15% of symbols are used at a given time
    _v_nr_sym_static = int(np.random.uniform(0.20) * _v_max_symbols)
    # normal distribution
    _v_nr_efs_in_cell = nr_efs
    if _v_nr_efs_in_cell == -1:
        _v_nr_efs_in_cell = 0 if abs(np.random.normal()) <= 0.5 else 1 if abs(np.random.normal()) <= 1.5 else 2 if abs(
            np.random.normal()) <= 2.5 else 3

    _v_nr_sym_per_ef = 0 if _v_nr_efs_in_cell == 0 else int((_v_max_symbols - _v_nr_sym_static) / _v_nr_efs_in_cell)
    _l_return_list = [_v_nr_sym_static, _v_nr_efs_in_cell, _v_nr_sym_per_ef]
    for i in range(3):
        if i < _v_nr_efs_in_cell:
            _v_mcs_three_closets_cells = [int(np.random.uniform(0.2, 0.29) * 100),
                                          int(np.random.uniform(0.1, 0.29) * 100),
                                          int(np.random.uniform(0.1, 0.29) * 100)]
            _l_return_list.append(_v_mcs_three_closets_cells)
        else:
            _l_return_list.append([0, 0, 0])
    return _l_return_list


def getThreeCellsScenario():
    return [getSingleCellScenario(),
            getSingleCellScenario(),
            getSingleCellScenario()]


def getEfCellPermutations(nr_efs, nr_cells):
    if ((nr_efs == 0) | (nr_cells == 0)):
        return []
    _l_ef_positions_perm = np.zeros(nr_cells, dtype=int)
    _l_ef_positions_perm[0] = 1
    _l_ef_positions_perm = [list(_perm) for _perm in set(permutations(_l_ef_positions_perm))]
    return [list(_perm) for _perm in list(product(_l_ef_positions_perm, repeat=nr_efs))]


def getDestStatesSymbols(destStates, symbolsPerCellPerEf, nrEfs):
    if ((len(destStates) == 0) or (len(symbolsPerCellPerEf) == 0) or (nrEfs == 0)):
        return []
    # print(destStates)
    _tmp2 = np.sum(destStates, axis=1, dtype=int)
    _l_possible_dest_states_symbols = np.floor_divide(symbolsPerCellPerEf, _tmp2, out=np.zeros_like(_tmp2),
                                                      where=_tmp2 != 0)
    _l_possible_dest_states_symbols = np.repeat(_l_possible_dest_states_symbols, nrEfs, axis=0)
    _l_possible_dest_states_symbols = np.reshape(_l_possible_dest_states_symbols,
                                                 (int(_l_possible_dest_states_symbols.shape[0] / nrEfs),
                                                  nrEfs,
                                                  _l_possible_dest_states_symbols.shape[1]))
    return _l_possible_dest_states_symbols * np.array(destStates)


def getAllCombinations(threeCellsScenario):
    _t_mcs = []
    _v_max_symbols = 14 * pow(2, 4) * 10
    _t_available_resources = []
    _v_nr_active_efs = sum([cellScenario[1] for cellScenario in threeCellsScenario])
    _l_symbols_per_cell_per_ef = np.array([cellScenario[2] for cellScenario in threeCellsScenario], dtype=int)
    _l_symbols_per_cell = np.array([cellScenario[2] * cellScenario[1] for cellScenario in threeCellsScenario],
                                   dtype=int)
    #     _t_start_alloc = np.zeros(_v_nr_active_efs, len(_v_three_cells_scen))
    _t_start_alloc_binary = []
    _t_start_alloc_symbols = []

    _l_possible_dest_states = getEfCellPermutations(_v_nr_active_efs, len(threeCellsScenario))

    _l_possible_dest_states_symbols = getDestStatesSymbols(_l_possible_dest_states,
                                                           _l_symbols_per_cell,
                                                           _v_nr_active_efs)

    for cellid, cellScenario in enumerate(threeCellsScenario):
        _v_nr_efs = cellScenario[1]
        for mcs_ind, _user_count in enumerate(list(range(_v_nr_efs))):
            _t_mcs.append(cellScenario[3 + mcs_ind])  # (cellid+1), _user_count,
            _v_tmp = np.zeros(len(threeCellsScenario))
            _v_tmp[cellid] = 1
            _t_start_alloc_binary.append(_v_tmp)
    if len(_t_start_alloc_binary) == 0:
        _t_start_alloc_symbols = []
    else:
        _t_start_alloc_symbols = np.array(_t_start_alloc_binary, dtype=int) * _l_symbols_per_cell_per_ef

    return np.array(_t_mcs), _t_start_alloc_symbols, _l_possible_dest_states_symbols


def getTbSizeFromMcs(mcs):
    McsEcrTable1 = [
        0.12, 0.15, 0.19, 0.25, 0.30, 0.37, 0.44, 0.51, 0.59, 0.66,
        0.33, 0.37, 0.42, 0.48, 0.54, 0.60, 0.64,
        0.43, 0.46, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.89, 0.93
    ]
    McsMTable1 = [
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
        4, 4, 4, 4, 4, 4, 4,
        6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6
    ]
    return 132 * 11 * McsEcrTable1[mcs] * McsMTable1[mcs]


_v_nr_efs = 4
_v_nr_cells = 3


def obj_func(mcs, nr_sym_bs, X):
    _v_mcs_reshape = mcs
    _v_S_reshape = X[:_v_nr_efs * _v_nr_cells]
    _v_A_reshape = X[_v_nr_efs * _v_nr_cells:]
    _v_S_reshape = _v_S_reshape.reshape(_v_nr_efs, _v_nr_cells)
    _v_A_reshape = _v_A_reshape.reshape(_v_nr_efs, _v_nr_cells)
    _v_mcs_reshape = mcs.reshape(_v_nr_efs, _v_nr_cells)
    pen = 0
    # First constraint: Assignment constraint: All efs should be assigned exatly to one gnb
    if (np.sum(_v_A_reshape, axis=1) != 1).any():
        pen += 5 * 2240 * _v_nr_efs * _v_nr_cells
    # Second constraint: All efs users assigned to a bs shall have the same number of symbols
    if not np.isin(_v_S_reshape, np.array([[0, x] for x in _v_S_reshape.max(axis=0)])).all():
        pen = 5 * 2240 * _v_nr_efs * _v_nr_cells
    # Third constraint: The sum of used symbols by users shall be equal to available symbols at the bs
    if (np.sum(_v_A_reshape * _v_S_reshape, axis=1) != np.sum(_v_A_reshape * nr_sym_bs, axis=1)).any():
        pen = 5 * 2240 * _v_nr_efs * _v_nr_cells
    return -np.sum(_v_S_reshape * _v_mcs_reshape) + pen


def value_to_string(value):
    if isinstance(value, bytes):
        return '0x' + str(binascii.hexlify(value).upper())
    elif isinstance(value, str):
        return value
    else:
        return repr(value)


def pretty_print(input_stream, indent=0):
    """Pretty print ASN.1 data."""
    while not input_stream.eof():
        tag = input_stream.peek()
        if tag.typ == asn1.Types.Primitive:
            tag, value = input_stream.read()
            print(' ' * indent)
            print('[{}] {}: {}\n'.format(tag.cls, (tag.nr), (tag.nr, value)))
        elif tag.typ == asn1.Types.Constructed:
            print(' ' * indent)
            print('[{}] {}\n'.format((tag.cls), (tag.nr)))
            input_stream.enter()
            pretty_print(input_stream, indent + 2)
            input_stream.leave()


def encode_data(gnbPositions#: List[tuple[int, np.ndarray]]
                ,
                _closestEnbForEf: List[int], threeClosestEnb: List[List[int]],
                efPos#:  list[tuple[int, np.ndarray]]
                ) -> asn1.Encoder:
    assign_encoder = asn1.Encoder()
    assign_encoder.start()
    assign_encoder.enter(nr=asn1.Numbers.Sequence, cls=asn1.Classes.Application)

    # Measurements part
    measurement_encoder = asn1.Encoder()
    measurement_encoder.start()
    measurement_encoder.enter(nr=asn1.Numbers.Sequence, cls=asn1.Classes.Application)

    # Gnb Resources
    resources_encoder = asn1.Encoder()
    resources_encoder.start()
    resources_encoder.enter(nr=asn1.Numbers.Sequence, cls=asn1.Classes.Application)

    #    size: nr_efs * nr_neighbours
    _neighbourCellsIndex = list(np.array(threeClosestEnb).T[1:].T)

    for gnbPosition in gnbPositions:
        # Writing the cell id first
        #         print("e1: {}".format(gnbPosition[0]))
        # assignment of a gnb
        assign_encoder.write(gnbPosition[0], nr=asn1.Numbers.Integer)
        # assignment details of a user (imsi/nodeid) & mcs
        assign_encoder.enter(asn1.Numbers.Sequence, asn1.Classes.Context)
        # for each gnb we write the data of assignment
        # shall return a list of tuples with (index_list, cellid)
        _filter_efs_by_cellid = list(filter(lambda _tuple: _tuple[1] == gnbPosition[0], enumerate(_closestEnbForEf)))

        _nr_efs = min(len(_filter_efs_by_cellid), 2)

        # gnb cell id
        measurement_encoder.write(gnbPosition[0], nr=asn1.Numbers.Integer)
        # measurements list/sequence per user
        measurement_encoder.enter(asn1.Numbers.Sequence, asn1.Classes.Context)

        if _nr_efs == 0:
            # when there is no efs we serialize the next gnb
            assign_encoder.leave()
            measurement_encoder.leave()
        else:
            _scen = getSingleCellScenario(_nr_efs)
            #             print("Scenario")
            #             print(_scen)
            # Writing the number of available symbols
            assign_encoder.write(_scen[0], asn1.Numbers.Integer)

            # Resouces pai
            resources_encoder.enter(asn1.Numbers.Sequence, asn1.Classes.Context)
            # cellid
            resources_encoder.write(gnbPosition[0], nr=asn1.Numbers.Integer)
            # resouces
            resources_encoder.write(_scen[0], nr=asn1.Numbers.Integer)
            resources_encoder.leave()

            for _ef_ind in range(_nr_efs):
                # Writing the node id and mcs for each assigned user
                assign_encoder.enter(asn1.Numbers.Sequence, asn1.Classes.Private)
                # the imsi id of the efs -> available in the efPos vector
                _imsi = efPos[_filter_efs_by_cellid[_ef_ind][0]][0]
                assign_encoder.write(_imsi, asn1.Numbers.Integer)
                # mcs - > available in the first position for each ef of getSingleCellScenario
                try:
                    assign_encoder.write(_scen[3 + _ef_ind][0], asn1.Numbers.Integer)
                except IndexError:
                    print(_scen)
                    print(_ef_ind)
                assign_encoder.leave()

                # Measurement encoding
                # Encoding the imsi of the ue who has made the measurements
                measurement_encoder.write(efPos[_filter_efs_by_cellid[_ef_ind][0]][0], asn1.Numbers.Integer)
                # we have a sequence of measurements for each imsi(user)
                #                 measurement_encoder.enter(asn1.Numbers.Sequence, asn1.Classes.Private)
                # individual measurments (cellid and mcs measured - in practice shall be SINR)
                # iterate over neighbourcells
                for _cellInd, _neighbourCellId in np.ndenumerate(
                        _neighbourCellsIndex[_filter_efs_by_cellid[_ef_ind][0]]):
                    # print(_scen)
                    # print(_ef_ind)
                    _mcs = _scen[3 + _ef_ind][_cellInd[0] + 1]
                    # print(gnbPosition[0], _imsi, _neighbourCellId, _mcs)
                    # Writing pair mcs and cell id
                    measurement_encoder.enter(asn1.Numbers.Sequence, asn1.Classes.Application)
                    measurement_encoder.write(_neighbourCellId, asn1.Numbers.Integer)
                    measurement_encoder.write(_mcs, asn1.Numbers.Integer)
                    measurement_encoder.leave()

            #                 measurement_encoder.leave()

            measurement_encoder.leave()
            assign_encoder.leave()
    #         measurement_encoder.leave()

    assign_encoder.leave()
    resources_encoder.leave()
    measurement_encoder.leave()
    return assign_encoder, measurement_encoder, resources_encoder


def decode_assignment_data(encoded_bytes: Union[bytes, bytes]):
    _gnb_assignments = []
    decoder = asn1.Decoder()
    decoder.start(encoded_bytes)
    tag = decoder.peek()
    if tag.cls == asn1.Classes.Application:
        decoder.enter()
        while (decoder.peek() is not None):  # and ( )
            #             print("d1: {}".format(tag))
            # first layer-> cell layer
            _gnbCellId = -1
            tag, value = decoder.read()
            if tag.typ == asn1.Types.Primitive:
                _gnbCellId = value
                # if _gnbCellId == 7:
                #     print("d2: {} {}".format(tag, value_to_string(value)))
                tag = decoder.peek()
                # if _gnbCellId == 7:
                #     print("d3: {} {}".format(tag, value_to_string(value)))
            if tag.typ == asn1.Types.Constructed:
                # gnb assignment filling
                _efs_list = []
                _availableGnbResources = 0
                while (decoder.peek() is not None) and (tag.cls == asn1.Classes.Context):
                    # if _gnbCellId == 7:
                    #     print("d3_4: {} {}".format(decoder.peek(), value))
                    decoder.enter()
                    # if _gnbCellId == 7:
                    #     print("d3_4_2: {} {}".format(decoder.peek(), value))
                    if decoder.peek() is None:
                        decoder.leave()
                        tag = decoder.peek()
                        break
                    tag, value = decoder.read()
                    # if _gnbCellId == 7:
                    #     print("d4: {} {}".format(tag, value_to_string(value)))
                    if tag.typ == asn1.Types.Primitive:
                        _availableGnbResources = value

                    tag = decoder.peek()
                    # if _gnbCellId == 7:
                    #     print("d6: {} {}".format(tag, value))
                    if tag.typ == asn1.Types.Constructed:
                        while (decoder.peek() is not None) and (decoder.peek().cls == asn1.Classes.Private):
                            # if _gnbCellId == 7:
                            #     print("d7: {} {}".format(tag, value_to_string(value)))
                            _efNodeId, _efNodeMcs = -1, -1
                            decoder.enter()
                            tag, value = decoder.read()
                            # if _gnbCellId == 7:
                            #     print("d8: {} {}".format(tag, value_to_string(value)))
                            if tag.typ == asn1.Types.Primitive:
                                _efNodeId = value
                            tag, value = decoder.read()
                            # if _gnbCellId == 7:
                            #     print("d9: {} {}".format(tag, value_to_string(value)))
                            if tag.typ == asn1.Types.Primitive:
                                _efNodeMcs = value
                            decoder.leave()
                            # appending a tuple
                            _efs_list.append({trasform._IMSI_FIELD: _efNodeId, trasform._MCS_FIELD: _efNodeMcs})
                            #                             print(_efs_list)
                            #                             tag = decoder.peek()
                            # if _gnbCellId == 7:
                            #     print("d10: {} {}".format(tag, value_to_string(value)))
                    decoder.leave()
                # if _gnbCellId == 7:
                #     print("d3_4_3: {} {}".format(tag, value_to_string(value)))
                #                 if tag is None:
                #                     break
                # Add assignment to list
                _gnb_assignments.append({trasform._CELLID_FIELD: _gnbCellId,
                                         trasform._USER_ASSIGNMENTS_FIELD: _efs_list})
                #             tag, value = decoder.read()
                # if _gnbCellId == 7:
                #     print("d3_4_4: {} {}".format(decoder.peek(), value_to_string(value)))
    #         decoder.leave()
    #         if tag is None:
    #             break
    with open("assign.json", "w") as outfile:
        json.dump(_gnb_assignments, outfile)
    return _gnb_assignments


def decode_measurements_data(encoded_bytes: Union[bytes, bytes]):
    # _gnb_measurements: list[dict[str, Union[int, list[dict[str, Union[int, list]]]]]] = []
    _gnb_measurements = []

    decoder = asn1.Decoder()
    decoder.start(encoded_bytes)
    tag = decoder.peek()
    if tag.cls == asn1.Classes.Application:
        # decoder.enter()
        while decoder.peek() is not None:
            # print("d1: {}".format(tag))
            # first layer-> cell layer
            if decoder.peek().typ == asn1.Types.Constructed:
                decoder.enter()
            _gnbCellId = -1
            tag, value = decoder.read()
            if tag.typ == asn1.Types.Primitive:
                _gnbCellId = value
                # print("d2: {} {}".format(tag, value_to_string(value)))
                # print("d3: {} {}".format(decoder.peek(), value_to_string(value)))
            if decoder.peek().cls == asn1.Classes.Context:
                # gnb assignment filling
                # print("d3_1: {} {}".format(decoder.peek(), value_to_string(value)))
                _efs_list = []
                _ef_imsi = 0
                while decoder.peek() is not None:
                    # print("d3_4: {} {}".format(decoder.peek(), value))
                    if decoder.peek().typ == asn1.Types.Constructed:
                        decoder.enter()
                    # decoder.enter()
                    # print("d3_4_2: {} {}".format(decoder.peek(), value))
                    if decoder.peek() is None:
                        # Means there is no data for this gnb so we insert empty list
                        break
                    tag, value = decoder.read()
                    # print("d4: {} {}".format(tag, value_to_string(value)))
                    if tag.typ == asn1.Types.Primitive:
                        _ef_imsi = value
                    # print("d6: {} {}".format(decoder.peek(), value))
                    _neighbour_list = []
                    # We have only the sequence of cellid - mcs pair in meas
                    if decoder.peek().cls == asn1.Classes.Application:
                        # print("d8_0: {} {}".format(decoder.peek(), value_to_string(value)))
                        # we have to make distinguishment of diff imsi
                        # attached to the same cell
                        _nr_neighbor_cell_per_user = 0
                        while decoder.peek() is not None:
                            if decoder.peek().typ == asn1.Types.Constructed:
                                decoder.enter()
                            _neighNodeId, _neighNodeMcs = -1, -1
                            tag, value = decoder.read()
                            # print("d8: {} {}".format(tag, value_to_string(value)))
                            if tag.typ == asn1.Types.Primitive:
                                _neighNodeId = value
                            tag, value = decoder.read()
                            # print("d9: {} {}".format(tag, value_to_string(value)))
                            if tag.typ == asn1.Types.Primitive:
                                _neighNodeMcs = value
                            _neighbour_list.append(
                                {trasform._CELLID_FIELD: _neighNodeId, trasform._MCS_FIELD: _neighNodeMcs})
                            # print("d10: {} {}".format(decoder.peek(), value_to_string(value)))


                            _nr_neighbor_cell_per_user += 1
                            if _nr_neighbor_cell_per_user == 2:
                                decoder.leave()
                                _nr_neighbor_cell_per_user = 0
                                break

                            if decoder.peek() is None:
                                decoder.leave()

                    _efs_list.append({trasform._IMSI_FIELD: _ef_imsi, trasform._MEASUREMENTS_FIELD: _neighbour_list})
                    # print("d11: {} {}".format(decoder.peek(), value_to_string(value)))
                    if decoder.peek() is None:
                        decoder.leave()
                        break

            # print("d3_4_3: {} {}".format(tag, value_to_string(value)))
            _item_added_map = {trasform._CELLID_FIELD: _gnbCellId,
                               trasform._USER_MEASUREMENTS_FIELD: _efs_list}
            # print(_item_added_map)
            _gnb_measurements.append(_item_added_map)
            gnbMeasurements = _gnb_measurements

            with open("meas.json", "w") as outfile:
                json.dump(gnbMeasurements, outfile)
            # print(gnbMeasurements)
            # print("d3_4_4: {} {}".format(decoder.peek(), value_to_string(value)))
            if decoder.peek() is None:
                decoder.leave()
                # break
    return _gnb_measurements


def decode_gnb_resources_data(encoded_bytes: Union[bytes, bytes]):
    # _gnb_resources: list[dict[str, int]] = []
    _gnb_resources = []
    decoder = asn1.Decoder()
    decoder.start(encoded_bytes)
    tag = decoder.peek()
    if tag.cls == asn1.Classes.Application:
        while decoder.peek() is not None:
            # print("d1: {}".format(tag))
            # first layer-> cell layer
            if decoder.peek().typ == asn1.Types.Constructed:
                decoder.enter()
            if decoder.peek().cls == asn1.Classes.Context:
                # gnb assignment filling
                while decoder.peek() is not None:
                    if decoder.peek().typ == asn1.Types.Constructed:
                        decoder.enter()
                    _nodeId, _nodeResources = -1, -1
                    tag, value = decoder.read()
                    # print("d8: {} {}".format(tag, value_to_string(value)))
                    if tag.typ == asn1.Types.Primitive:
                        _nodeId = value
                    tag, value = decoder.read()
                    # print("d9: {} {}".format(tag, value_to_string(value)))
                    if tag.typ == asn1.Types.Primitive:
                        _nodeResources = value
                    _gnb_resources.append({trasform._CELLID_FIELD: _nodeId, trasform._GNB_RESOUCES: _nodeResources})
                    if decoder.peek() is None:
                        decoder.leave()
            if decoder.peek() is None:
                decoder.leave()
    return _gnb_resources


# if __name__ == '__main__':
#     _v_three_cells_scen = getThreeCellsScenario()
#     _v_three_cells_scen

#     # print(_v_three_cells_scen)

#     _t_mcs, _t_start_alloc_symbols, _t_dest_states_symbols = getAllCombinations(_v_three_cells_scen)
#     _v_sym_per_bs = np.array([16 * 14 * 10 - cellScenario[0] for cellScenario in _v_three_cells_scen])
#     _v_parameterized_obj_func = partial(obj_func, _t_mcs, _v_sym_per_bs)

#     # Assuming we have 3 cells and 4 efs = 12 possible #symbols used from user i from bs j
#     varbound=np.array([[0,2240]]*_v_nr_efs*_v_nr_cells)

#     varbound = np.array([[0, 2240]] * _v_nr_efs * _v_nr_cells + [[0, 1]] * _v_nr_efs * _v_nr_cells)
#     vartype = np.array(['int'] * _v_nr_efs * _v_nr_cells + ['int'] * _v_nr_efs * _v_nr_cells)
#     gnbPositions = getSizePositions()
#     efPos = getRandomPositionNode(10, len(gnbPositions), -100, 100, -100, 100)
#     _closestEnbForEf = attachClosestEnb(efPos, gnbPositions)
#     threeClosestEnb = getThreeClosestEnb(efPos, gnbPositions)
#     plt.plot([x for (ind, (x, y, z)) in gnbPositions], [y for (ind, (x, y, z)) in gnbPositions], 'g.',
#             [x for (ind, (x, y, z)) in efPos], [y for (ind, (x, y, z)) in efPos], 'r.', )
#     gnbPositions

#     print(threeClosestEnb)

#     assign_encoder, measurement_encoder, resources_encoder = encode_data(gnbPositions, _closestEnbForEf,
#                                                                         threeClosestEnb)

#     encoded_bytes = measurement_encoder.output()
    # encoded_bytes = resources_encoder.output()

    # decoder = asn1.Decoder()
    # decoder.start(encoded_bytes)

    # pretty_print(decoder)

    # gnbAssignments = decode_data(encoded_bytes)

    # gnbAssignments

    # gnbMeasurements = decode_measurements_data(encoded_bytes)
    # print(gnbMeasurements)

    # gnbResources = decode_gnb_resources_data(encoded_bytes)
    # print(gnbResources)
