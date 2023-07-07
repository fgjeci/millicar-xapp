
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import gymnasium as gym
from gymnasium.spaces.box import Box
from gymnasium.spaces import dict
import networkx as nx
import numpy as np
from graphenv import tf
# from graphenv.examples.tsp.graph_utils import plot_network
from graphenv.vertex import Vertex
from random import shuffle
from collections import OrderedDict

layers = tf.keras.layers

TYPE_KEYWORD = "Type"
AVAILABLE_SYMBOLS_KEYWORD = "AvailableSymbols"
WEIGHT_KEYWORD = 'Weight'
GNB_KEYWORD = "GNB"
UE_KEYWORD = "UE"


class RlAssingState(Vertex):

    def __init__(
        self,
        G: nx.DiGraph = None, 
        nodeAssignments: List[Tuple[int, int]] = [], 
        nodeListExamined: List[int] = [],
        nodeTransferHistory: Dict[int, List[int]] = None,
        lastTransferredNode: int = -1, 
        nodeClosestGnbs: Dict[int, List[int]] = None
    ) -> None:

        super().__init__()

        self.G = G
        self.nodeAssignments = nodeAssignments
        self.nodeListExamined = nodeListExamined
        self.nodeTransferHistory = nodeTransferHistory
        self.lastTransferredNode = lastTransferredNode
        self.nodeClosestGnbs = nodeClosestGnbs

        self.num_nodes = 0 if self.G is None else self.G.number_of_nodes()
    
    @property
    def observation_space(self) -> dict.Dict:
        """Returns the graph env's observation space.
        Returns:
            Dict observation space.
        """
        return dict.Dict(
            {
                "num_efs_gnb_source": Box(
                    low=0, high=100, shape=(1,), dtype=int
                ),
                "num_elastic_sym_gnb_source": Box(
                    low=0, high=14*16*10, shape=(1,), dtype=int
                ),
                "mcs_gnb_source": Box(
                    low=0.0, high=28, shape=(1,), dtype=int
                ),
                "num_efs_gnb_dest": Box(
                    low=0, high=100, shape=(1,), dtype=int
                ),
                "num_elastic_sym_gnb_dest": Box(
                    low=0, high=14*16*10, shape=(1,), dtype=int
                ),
                "mcs_gnb_dest": Box(
                    low=0.0, high=28, shape=(1,), dtype=int
                ),
                "pot_efs_moving_to_gnb_source": Box(
                    low=0, high=400, shape=(1,), dtype=int # unlikely to be higher than 400
                ),
                "pot_efs_moving_to_gnb_dest": Box(
                    low=0, high=400, shape=(1,), dtype=int
                ),
                "node_index": Box(
                    low=-1, high=20, shape=(1,), dtype=int
                ),
            }
        )

    @property
    def root(self) -> "RlAssingState":
        """Returns the root node of the graph env.
        Returns:
            Node with node 0 as the starting point of the tour, and generates a new
            graph using the given constructor
        """
        G = self.G
        nodeListExamined = []
        nodeTransferHistory = {ueNodeId: [gnbNodeIds[0]]  for ueNodeId,gnbNodeIds in self.nodeTransferHistory.items()}
        nodeAssignments = [(ueNodeId, gnbNodeIds[0])  for ueNodeId,gnbNodeIds in self.nodeTransferHistory.items()]
        nodeClosestGnbs = self.nodeClosestGnbs
        return self.new(G, nodeAssignments=nodeAssignments, 
                        nodeListExamined=nodeListExamined, 
                        nodeTransferHistory=nodeTransferHistory, 
                        lastTransferredNode=-1, 
                        nodeClosestGnbs=nodeClosestGnbs)

    @property
    def reward(self) -> float:
        """Returns the graph env reward.
        Returns:
            This returns the reward of transferring an ue node to a gnb
        """
        # the reward in a state shall be the product of number of symbols used by an ef and its mcs
        # Recall that symbols are equally distributed between the efs
        rew = 0
        lastTransferredNode = self.lastTransferredNode
        if(lastTransferredNode == -1):
            return 0
        assignTuple = list(filter(lambda assignment: assignment[0] == lastTransferredNode, self.nodeAssignments))
        # print(f"Assignment tuple {assignTuple}")
        if(len(assignTuple) > 1):
            raise RuntimeError("Node is assigned to multiple GNBs concurrently")
        elif (len(assignTuple) == 0):
            raise RuntimeError("Node is not assigned to any GNBs")
        else:
            ueNode = assignTuple[0][0]
            
            # gnbNode = assignTuple[0][1]
            # get transfer history of node and check the last transfer to define the reward
            transferredToCells = self.nodeTransferHistory.get(ueNode)
            if len(transferredToCells) <2:
                raise RuntimeError("Node has not been transferred any time")
            else:
                fromCell, toCell = transferredToCells[-2:]
                fromCellWeight = self.G[ueNode][fromCell][WEIGHT_KEYWORD]
                toCellWeight = self.G[ueNode][toCell][WEIGHT_KEYWORD]
                # calculating the number of symbols used and being used at the moment
                fromCellAvailSymbols =  self.G.nodes[fromCell][AVAILABLE_SYMBOLS_KEYWORD]
                toCellAvailSymbols =  self.G.nodes[toCell][AVAILABLE_SYMBOLS_KEYWORD]
                # From assignments we take the number of edges whose edge finishes in fromCell
                # Add 1, since the reward is taken after the action has been take, thus the node has been transferred
                # Before, the available resources were shared among all (1 + remaining)
                fromCellNumEfs = 1 + len(list(filter(lambda assignment: assignment[1] == fromCell, self.nodeAssignments)))
                toCellNumEfs = len(list(filter(lambda assignment: assignment[1] == toCell, self.nodeAssignments)))
                rew = toCellWeight*(np.floor(toCellAvailSymbols/toCellNumEfs)) -\
                      fromCellWeight*(np.floor(fromCellAvailSymbols/fromCellNumEfs))
        # print(f"Reward obtained {rew}")
        return rew

        
        # Define the reward of transferring a node from one gnb to another 

        # Get Gnb nodes; the symbols of each of the nodes shall be devided by the assigned users
        # gnbNodes = [(nodeId, nodeData) for nodeId, nodeData in self.G.nodes(data=True) if nodeData[TYPE_KEYWORD] == GNB_KEYWORD]
        
        # for gnbNode in gnbNodes:
        #     # Get all incoming edges
        #     inEdges= self.G.in_edges([gnbNode])
        #     # number of efs of this state to be assigned to this gnb
        #     potentialEfs = len(inEdges)
        #     # Get Gnb Available symbols 
        #     # Access nodeData in the dict nodeid and nodedata
        #     availSymb = gnbNode[1][AVAILABLE_SYMBOLS_KEYWORD]
        #     # iterate over the incoming edges in a node
        #     for inEdge in inEdges:
        #         # Reward = #symbols per ef * weight = log2(mcs)
        #         rew += np.floor(availSymb/potentialEfs)*self.G[inEdge[0]][inEdge[1]][WEIGHT_KEYWORD]
        # return rew

    def new(self,
            G: nx.DiGraph = None, 
            nodeAssignments: List[Tuple[int, int]] = [], 
            nodeListExamined: List[int] = [],
            nodeTransferHistory: Dict[int, np.ndarray] = None,
            lastTransferredNode: int = -1, 
            nodeClosestGnbs: Dict[int, np.ndarray] = None,
            **kwargs):
        
        """Convenience function for duplicating the existing node.
        Args:
            G:  Networkx graph.
            nodeClosestGnbs: List of closest Gnbs a ue nodes can handover to.
        Returns:
            New RlAssingState state.
        """
        # print(f"Creating new ue {lastTransferredNode}")
        return self.__class__(G=G, nodeAssignments=nodeAssignments, 
                              nodeListExamined = nodeListExamined,
                              nodeTransferHistory = nodeTransferHistory,
                              lastTransferredNode = lastTransferredNode,
                              nodeClosestGnbs=nodeClosestGnbs, **kwargs)

    # def render(self) -> Any:
    #     return plot_network(self.G, self.tour, draw_all_edges=False)

    @property
    def info(self) -> Dict:
        return {}

    def _get_children(self) -> Sequence["RlAssingState"]:
        """Yields a sequence of RlAssingState instances associated with the next
        accessible handoverrs.
        Yields:
            New instance of the RlAssingState with the next possible handovers;
            The yields are done on ue basis; i.e. we consider single ue each time 
            and examine possible dest gnb (nodeClosestGnbs) to generate possible states;
            ue selection is node randomly from not examined nodes
        """
        # print("Getting children")
        G = self.G
        nodeAssignments = self.nodeAssignments
        nodeListExamined = self.nodeListExamined
        nodeTransferHistory = self.nodeTransferHistory
        nodeClosestGnbs = self.nodeClosestGnbs
        nodeClosestGnbsKeys = list(nodeClosestGnbs.keys())
        shuffle(nodeClosestGnbsKeys)
        # each ue node in G graph has an attribute of ue
        # from ue we will construct the possible movements
        # for _examNode in self.nodeListExamined:
        #     print(f"Examined node {_examNode}")
        key = next((key for key in nodeClosestGnbsKeys if key not in self.nodeListExamined), -1)
        if key != -1:
            # We haven't considered all the nodes
            # yield all possible action of the current node
            potentialDestCells = nodeClosestGnbs.get(key)
            for potentialHandoverCell in potentialDestCells:
                # Add assignment 
                nodeAssignIndex = [index for index,value in enumerate(nodeAssignments) if value[0] == key]
                if(len(nodeAssignIndex) > 1):
                    raise RuntimeError("Node is assigned to multiple GNBs concurrently")
                elif (len(nodeAssignIndex) == 0):
                    raise RuntimeError("Node is not assigned to any GNBs")
                else:
                    nodeAssignments[nodeAssignIndex[0]] = (key, potentialHandoverCell)  

                # Add node to the examined ones
                nodeListExamined.append(key)
                lastTransferredNode = key
                
                if key in nodeTransferHistory.keys():
                    nodeTransferHistory.get(key).append(potentialHandoverCell)
                # print (f"Yielding data for ue {key} and {potentialHandoverCell}")
                # return a new state in the state space
                yield self.new(G=G, nodeAssignments=nodeAssignments,
                               nodeListExamined=nodeListExamined,
                               nodeTransferHistory=nodeTransferHistory,
                               lastTransferredNode=lastTransferredNode,
                               nodeClosestGnbs=nodeClosestGnbs)
            # # All outgoing edges from a ue node
            # edgesFromNode = G.out_edges([key])
            # # Remove all edges and generate all new possible edges
            # G.remove_edges_from(edgesFromNode)
            # for _possibleHandover in value:
            #     # yield new graph 
            #     yield self.new(G, nodeClosestGnbs)
                

    def _make_observation(self) -> Dict[str, np.ndarray]:
        """Return an observation.  The dict returned here needs to match
        both the self.observation_space in this class, as well as the input
        layer in tsp_model.RlAssignModel
        Returns:
            Observation dict.  
        """

        # cur_node = self.tour[-1]
        # cur_pos = np.array(self.G.nodes[cur_node]["pos"], dtype=float).squeeze()
        # # Compute distance to parent node, or 0 if this is the root.
        # if len(self.tour) == 1:
        #     parent_dist = 0.0
        # else:
        #     parent_dist = self.G[cur_node][self.tour[-2]]["weight"]
        # # Get list of all neighbors that are unvisited.  If none, then the only
        # # remaining neighbor is the root so dist is 0.
        # nbrs = [n for n in self.G.neighbors(cur_node) if n not in self.tour]
        # nbr_dist = 0.0
        # if len(nbrs) > 0:
        #     nbr_dist = np.min([self.G[cur_node][n]["weight"] for n in nbrs])
        # return {
        #     "node_obs": cur_pos,
        #     "node_idx": np.array([cur_node]),
        #     "parent_dist": np.array([parent_dist]),
        #     "nbr_dist": np.array([nbr_dist]),
        # }

        _num_efs_gnb_src = 0
        _num_elastic_sym_gnb_source = 0
        _mcs_gnb_source = 0
        _num_efs_gnb_dest = 0
        _num_elastic_sym_gnb_dest = 0
        _mcs_gnb_dest = 0
        _pot_efs_moving_to_gnb_source = 0
        _pot_efs_moving_to_gnb_dest = 0


        lastTransferredNode = self.lastTransferredNode
        _transferHistory = self.nodeTransferHistory.get(lastTransferredNode)
        nodeAssignments = self.nodeAssignments
        if _transferHistory is not None:
            # Getting the last 2 gnbs
            if len(_transferHistory) > 1:
                _gnb_src, _gnb_dst = _transferHistory[-2:]
                # Source
                _num_efs_gnb_src = 1 + len(list(filter(lambda _tuple: _tuple[1] == _gnb_src, nodeAssignments)))
                _num_elastic_sym_gnb_source = self.G.nodes[_gnb_src][AVAILABLE_SYMBOLS_KEYWORD]
                _mcs_gnb_source = self.G[lastTransferredNode][_gnb_src][WEIGHT_KEYWORD]
                # Destination
                _mcs_gnb_dest = len(list(filter(lambda _tuple: _tuple[1] == _gnb_dst, nodeAssignments)))
                _num_elastic_sym_gnb_dest = self.G.nodes[_gnb_dst][AVAILABLE_SYMBOLS_KEYWORD]
                _mcs_gnb_dest = self.G[lastTransferredNode][_gnb_dst][WEIGHT_KEYWORD]
                
                _pot_efs_moving_to_gnb_source= len(self.G.in_edges([_gnb_src]))
                _pot_efs_moving_to_gnb_dest = len(self.G.in_edges([_gnb_dst]))
    
        return OrderedDict({
            "num_efs_gnb_source": np.array([_num_efs_gnb_src]),
            "num_elastic_sym_gnb_source": np.array([_num_elastic_sym_gnb_source]),
            "mcs_gnb_source": np.array([_mcs_gnb_source]),
            "num_efs_gnb_dest": np.array([_num_efs_gnb_dest]),
            "num_elastic_sym_gnb_dest": np.array([_num_elastic_sym_gnb_dest]),
            "mcs_gnb_dest": np.array([_mcs_gnb_dest]),
            "pot_efs_moving_to_gnb_source": np.array([_pot_efs_moving_to_gnb_source]),
            "pot_efs_moving_to_gnb_dest": np.array([_pot_efs_moving_to_gnb_dest]),
            "node_index": np.array([lastTransferredNode]),
        })
        # return {
        #     "num_efs_gnb_source": np.array([_num_efs_gnb_src]),
        #     "num_elastic_sym_gnb_source": np.array([_num_elastic_sym_gnb_source]),
        #     "mcs_gnb_source": np.array([_mcs_gnb_source]),
        #     "num_efs_gnb_dest": np.array([_num_efs_gnb_dest]),
        #     "num_elastic_sym_gnb_dest": np.array([_num_elastic_sym_gnb_dest]),
        #     "mcs_gnb_dest": np.array([_mcs_gnb_dest]),
        #     "pot_efs_moving_to_gnb_source": np.array([_pot_efs_moving_to_gnb_source]),
        #     "pot_efs_moving_to_gnb_dest": np.array([_pot_efs_moving_to_gnb_dest]),
        #     "node_index": np.array([lastTransferredNode]),
        # }