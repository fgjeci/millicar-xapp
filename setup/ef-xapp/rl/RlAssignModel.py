from typing import Tuple

from graphenv import tf
from graphenv.graph_model import GraphModel
from graphenv.graph_model_bellman_mixin import GraphModelBellmanMixin
from ray.rllib.algorithms.dqn.distributional_q_tf_model import DistributionalQTFModel
from ray.rllib.models.tf.tf_modelv2 import TFModelV2
from ray.rllib.utils.typing import TensorStructType, TensorType

layers = tf.keras.layers


class BaseRlAssignModel(GraphModel):
    def __init__(
        self,
        *args,
        num_nodes: int,
        hidden_dim: int = 32,
        embed_dim: int = 32,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.base_model = self._create_base_model(num_nodes, hidden_dim, embed_dim)

    @staticmethod
    def _create_base_model(
        num_nodes: int, hidden_dim: int = 32, embed_dim: int = 32
    ) -> tf.keras.Model:
        
        num_efs_gnb_source = layers.Input(shape=(1,), name="num_efs_gnb_source", dtype=tf.float32) #int32
        num_elastic_sym_gnb_source = layers.Input(shape=(1,), name="num_elastic_sym_gnb_source", dtype=tf.float32) #int32
        mcs_gnb_source = layers.Input(shape=(1,), name="mcs_gnb_source", dtype=tf.float32) #int32

        num_efs_gnb_dest = layers.Input(shape=(1,), name="num_efs_gnb_dest", dtype=tf.float32) #int32
        num_elastic_sym_gnb_dest = layers.Input(shape=(1,), name="num_elastic_sym_gnb_dest", dtype=tf.float32) #int32
        mcs_gnb_dest = layers.Input(shape=(1,), name="mcs_gnb_dest", dtype=tf.float32) #int32

        pot_efs_moving_to_gnb_source = layers.Input(shape=(1,), name="pot_efs_moving_to_gnb_source", dtype=tf.float32) #int32
        pot_efs_moving_to_gnb_dest = layers.Input(shape=(1,), name="pot_efs_moving_to_gnb_dest", dtype=tf.float32) #int32

        node_index = layers.Input(shape=(1,), name="node_index", dtype=tf.float32) #int32

        embed_layer = layers.Embedding(
            num_nodes, embed_dim, name="embed_layer", input_length=1
        )

        hidden_layer_1 = layers.Dense(
            hidden_dim, name="hidden_layer_1", activation="relu"
        )
        hidden_layer_2 = layers.Dense(
            hidden_dim, name="hidden_layer_2", activation="linear"
        )
        action_value_output = layers.Dense(
            1, name="action_value_output", bias_initializer="ones"
        )
        action_weight_output = layers.Dense(
            1, name="action_weight_output", bias_initializer="ones"
        )

        # Process the positional node data.  Here we need to expand the
        # middle axis to match the embedding output dimension.
        x = layers.Concatenate(axis=-1)([num_efs_gnb_source, num_elastic_sym_gnb_source, mcs_gnb_source,
                                         num_efs_gnb_dest, num_elastic_sym_gnb_dest, mcs_gnb_dest,
                                         pot_efs_moving_to_gnb_source, pot_efs_moving_to_gnb_dest])
        hidden = layers.Reshape((1, hidden_dim))(hidden_layer_1(x))

        # Process the embedding.
        embed = embed_layer(node_index)

        # Concatenate and flatten for dense output layers.
        out = layers.Concatenate(axis=-1)([hidden, embed])
        out = layers.Flatten()(out)
        out = hidden_layer_2(out)

        # Action values and weights for RLLib algorithms
        action_values = action_value_output(out)
        action_weights = action_weight_output(out)

        return tf.keras.Model(
            [num_efs_gnb_source, num_elastic_sym_gnb_source, mcs_gnb_source, 
             num_efs_gnb_dest, num_elastic_sym_gnb_dest, mcs_gnb_dest,
             pot_efs_moving_to_gnb_source, pot_efs_moving_to_gnb_dest,
             node_index], 
             [action_values, action_weights]
        )
    def forward_vertex(
        self,
        input_dict: TensorStructType,
    ) -> Tuple[TensorType, TensorType]:
        return tuple(self.base_model(input_dict))


class RlAssignModel(BaseRlAssignModel, TFModelV2):
    pass


class RlAssignQModel(BaseRlAssignModel, DistributionalQTFModel):
    pass


class TSPQModelBellman(GraphModelBellmanMixin, BaseRlAssignModel, DistributionalQTFModel):
    pass