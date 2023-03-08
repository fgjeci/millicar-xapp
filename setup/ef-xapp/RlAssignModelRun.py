import argparse
import logging
import os
from pathlib import Path

import ray
from graphenv.graph_env import GraphEnv
from networkx.algorithms.approximation.traveling_salesman import greedy_tsp
from ray import tune
from ray.rllib.algorithms.a3c import A3CConfig
from ray.rllib.algorithms.dqn import DQNConfig
from ray.rllib.algorithms.marwil import MARWILConfig
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.models import ModelCatalog
from ray.rllib.utils.framework import try_import_tf
from ray.tune.registry import register_env

from RlAssignModel import RlAssignQModel, RlAssignModel
import RlAssignState

import networkx as nx

tf1, tf, tfv = try_import_tf()

parser = argparse.ArgumentParser()
parser.add_argument(
    "--run",
    type=str,
    default="PPO",
    choices=["PPO", "DQN", "A3C", "MARWIL"],
    help="The RLlib-registered algorithm to use.",
)
parser.add_argument("--N", type=int, default=16, help="Number of nodes in TSP network")
parser.add_argument(
    "--use-gnn", action="store_true", help="use the nfp state and gnn model"
)
parser.add_argument(
    "--max-num-neighbors",
    type=int,
    default=5,
    help="Number of nearest neighbors for the gnn model",
)
parser.add_argument(
    "--seed", type=int, default=0, help="Random seed used to generate networkx graph"
)
parser.add_argument(
    "--num-workers", type=int, default=1, help="Number of rllib workers"
)
parser.add_argument("--num-gpus", type=int, default=0, help="Number of GPUs")
parser.add_argument("--lr", type=float, default=1e-4, help="learning rate")
parser.add_argument(
    "--entropy-coeff", type=float, default=0.0, help="entropy coefficient"
)
parser.add_argument(
    "--rollouts-per-worker",
    type=int,
    default=1,
    help="Number of rollouts for each worker to collect",
)
parser.add_argument(
    "--stop-iters", type=int, default=50, help="Number of iterations to train."
)
parser.add_argument(
    "--stop-timesteps", type=int, default=100000, help="Number of timesteps to train."
)
parser.add_argument(
    "--stop-reward", type=float, default=0.0, help="Reward at which we stop training."
)
parser.add_argument(
    "--local-mode",
    action="store_true",
    help="Init Ray in local mode for easier debugging.",
)
parser.add_argument("--log-level", type=str, default="INFO")


if __name__ == "__main__":

    args = parser.parse_args()
    print(f"Running with following CLI options: {args}")

    logging.basicConfig(level=args.log_level.upper())

    ray.init(local_mode=args.local_mode)

    N = args.N

    # Compute the reward baseline with heuristic
    # creating the graph
    # list_edges = [(, 2)]
    G = nx.DiGraph()
    # Create gnb nodes
    G.add_node(1, **{RlAssignState.AVAILABLE_SYMBOLS_KEYWORD:600, RlAssignState.TYPE_KEYWORD:RlAssignState.GNB_KEYWORD})
    G.add_node(2, **{RlAssignState.AVAILABLE_SYMBOLS_KEYWORD:400, RlAssignState.TYPE_KEYWORD:RlAssignState.GNB_KEYWORD})
    G.add_node(3, **{RlAssignState.AVAILABLE_SYMBOLS_KEYWORD:100, RlAssignState.TYPE_KEYWORD:RlAssignState.GNB_KEYWORD})
    G.add_node(4, **{RlAssignState.AVAILABLE_SYMBOLS_KEYWORD:600, RlAssignState.TYPE_KEYWORD:RlAssignState.GNB_KEYWORD})
    G.add_node(5, **{RlAssignState.AVAILABLE_SYMBOLS_KEYWORD:400, RlAssignState.TYPE_KEYWORD:RlAssignState.GNB_KEYWORD})
    G.add_node(6, **{RlAssignState.AVAILABLE_SYMBOLS_KEYWORD:100, RlAssignState.TYPE_KEYWORD:RlAssignState.GNB_KEYWORD})
    G.add_node(7, **{RlAssignState.AVAILABLE_SYMBOLS_KEYWORD:600, RlAssignState.TYPE_KEYWORD:RlAssignState.GNB_KEYWORD})
    G.add_node(8, **{RlAssignState.AVAILABLE_SYMBOLS_KEYWORD:400, RlAssignState.TYPE_KEYWORD:RlAssignState.GNB_KEYWORD})
    G.add_node(9, **{RlAssignState.AVAILABLE_SYMBOLS_KEYWORD:600, RlAssignState.TYPE_KEYWORD:RlAssignState.GNB_KEYWORD})
    G.add_node(10, **{RlAssignState.AVAILABLE_SYMBOLS_KEYWORD:400, RlAssignState.TYPE_KEYWORD:RlAssignState.GNB_KEYWORD})

    G.add_node(11, **{RlAssignState.TYPE_KEYWORD:RlAssignState.UE_KEYWORD})
    G.add_node(12, **{RlAssignState.TYPE_KEYWORD:RlAssignState.UE_KEYWORD})
    G.add_node(13, **{RlAssignState.TYPE_KEYWORD:RlAssignState.UE_KEYWORD})
    G.add_node(14, **{RlAssignState.TYPE_KEYWORD:RlAssignState.UE_KEYWORD})
    G.add_node(15, **{RlAssignState.TYPE_KEYWORD:RlAssignState.UE_KEYWORD})
    G.add_node(16, **{RlAssignState.TYPE_KEYWORD:RlAssignState.UE_KEYWORD})
    # G.add_node(17, **{RlAssignState.TYPE_KEYWORD:RlAssignState.UE_KEYWORD})

    connections = {11: [{"id": 1, RlAssignState.WEIGHT_KEYWORD: 3}, 
                        {"id": 2, RlAssignState.WEIGHT_KEYWORD: 3}, 
                        {"id": 3, RlAssignState.WEIGHT_KEYWORD: 5}], 
                   12: [{"id": 2, RlAssignState.WEIGHT_KEYWORD: 5}, 
                        {"id": 3, RlAssignState.WEIGHT_KEYWORD: 5}, 
                        {"id": 4, RlAssignState.WEIGHT_KEYWORD: 2}], 
                   13: [{"id": 3, RlAssignState.WEIGHT_KEYWORD: 2}, 
                        {"id": 4, RlAssignState.WEIGHT_KEYWORD: 2}, 
                        {"id": 7, RlAssignState.WEIGHT_KEYWORD: 2}],
                   14: [{"id": 3, RlAssignState.WEIGHT_KEYWORD: 3}, 
                        {"id": 10, RlAssignState.WEIGHT_KEYWORD: 3}], 
                   15: [{"id": 4, RlAssignState.WEIGHT_KEYWORD: 6}, 
                        {"id": 5, RlAssignState.WEIGHT_KEYWORD: 6}, 
                        {"id": 6, RlAssignState.WEIGHT_KEYWORD: 6}], 
                   16: [{"id": 3, RlAssignState.WEIGHT_KEYWORD: 6}, 
                        {"id": 7, RlAssignState.WEIGHT_KEYWORD: 3}, 
                        {"id": 10, RlAssignState.WEIGHT_KEYWORD: 3}]}
    
    for ueIndex, idMcsPairList in connections.items():
        for idMcsPair in idMcsPairList:
            gnbId = idMcsPair["id"]
            weight = idMcsPair[RlAssignState.WEIGHT_KEYWORD]
            G.add_edge(ueIndex, gnbId, 
                       **{RlAssignState.WEIGHT_KEYWORD: weight})
    

    nodeAssignments = [
        (11, 1),
        (12, 2),
        (15, 5),
        (13, 4),
        (14, 3),
        (16, 7)
    ]

    nodeTransferHistory = {
        assignmentTuple[0]: [assignmentTuple[1]] for assignmentTuple in nodeAssignments
    }

    nodeClosestGnbs = {
        assignmentTuple[0]: [edge[1] for edge in G.out_edges([assignmentTuple[0]])]
        for assignmentTuple in nodeAssignments
    }

    # Algorithm-specific config, common ones are in the main config dict below
    if args.run == "PPO":
        run_config = PPOConfig()
        train_batch_size = args.rollouts_per_worker * N * args.num_workers
        sgd_minibatch_size = 16 if train_batch_size > 16 else 2
        run_config.training(entropy_coeff=args.entropy_coeff,
                            sgd_minibatch_size=sgd_minibatch_size,
                            num_sgd_iter=5,
        )
    elif args.run in ["DQN"]:
        run_config = DQNConfig()
        # Update here with custom config
        run_config.training(hiddens=False,
                        dueling=False
        )
        run_config.exploration(exploration_config={"epsilon_timesteps": 250000})
    elif args.run == "A3C":
        run_config = A3CConfig()
    elif args.run == "MARWIL":
        run_config = MARWILConfig()
    else:
        raise ValueError(f"Import agent {args.run} and try again")

    # Define custom_model, config, and state based on GNN yes/no
    # if args.use_gnn:
    #     custom_model = "TSPGNNModel"
    #     custom_model_config = {"num_messages": 3, "embed_dim": 32}
    #     ModelCatalog.register_custom_model(custom_model, TSPGNNModel)
    #     _tag = "gnn"
    #     state = TSPNFPState(
    #         lambda: make_complete_planar_graph(N=N),
    #         max_num_neighbors=args.max_num_neighbors,
        # )
    # For the moment we focus on the simple model and then user nfp
    if True:
        custom_model_config = {"hidden_dim": 32, "embed_dim": 32, "num_nodes": N}
        custom_model = "RlAssignModel"
        Model = RlAssignQModel if args.run in ["DQN", "R2D2"] else RlAssignModel
        ModelCatalog.register_custom_model(custom_model, Model)
        _tag = f"basic{args.run}"
        state = RlAssignState.RlAssingState(G, nodeAssignments=nodeAssignments,
                                            nodeListExamined=[], 
                                            nodeTransferHistory=nodeTransferHistory,
                                            lastTransferredNode=-1,
                                            nodeClosestGnbs=nodeClosestGnbs
                                            )

    # Register env name with hyperparams that will help tracking experiments
    # via tensorboard
    # env_name = f"graphenv_{N}_{_tag}_lr={args.lr}"
    env_name = f"graphenv_{N}-v{0.1}"
    register_env(env_name, lambda config: GraphEnv(config))

    run_config = (
        run_config
        .resources(num_gpus=args.num_gpus)
        .framework("tf2")
        .rollouts(num_rollout_workers=args.num_workers, 
                  # a multiple of N (collect whole episodes)
                  rollout_fragment_length=N)
        .environment(env=env_name,
                     env_config={"state": state, 
                                 "max_num_children": G.number_of_nodes()}
                  )
        .training(lr=args.lr,
                  train_batch_size=args.rollouts_per_worker * N * args.num_workers,
                  model={"custom_model": custom_model, 
                         "custom_model_config": custom_model_config}
                  )
        .evaluation(evaluation_config={"explore": False},
                    evaluation_interval=1, 
                    evaluation_duration=100,
                  )
        .debugging(log_level=args.log_level)
        .framework(eager_tracing=True)
    )

    stop = {
        "training_iteration": args.stop_iters,
        "timesteps_total": args.stop_timesteps,
        "episode_reward_mean": args.stop_reward,
    }

    tune.run(
        args.run,
        config=run_config.to_dict(),
        stop=stop,
        local_dir=Path(os.getcwd(), "ray_results"),
    )

    ray.shutdown()