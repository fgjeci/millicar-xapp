import scenario_creation
import trasform
import ipso_formulation
import numpy as np

import matplotlib;

from ipso.greddy_formulation import GreedyFormulation

matplotlib.use("TkAgg")

import pyswarms as ps
from pyswarms.utils.functions import single_obj as fx
from pyswarms.utils.plotters import plot_cost_history, plot_contour, plot_surface
import matplotlib.pyplot as plt
from pyswarms.utils.plotters.formatters import Mesher, Designer

if __name__ == '__main__':
    _gnbPositions = scenario_creation.getSizePositions()
    _efPos = scenario_creation.getRandomPositionNode(10, len(_gnbPositions), -100, 100, -100, 100)
    _closestEnbForEf = scenario_creation.attachClosestEnb(_efPos, _gnbPositions)
    _threeClosestEnb = scenario_creation.getThreeClosestEnb(_efPos, _gnbPositions)

    assign_encoder, measurement_encoder, resources_encoder = scenario_creation.encode_data(_gnbPositions,
                                                                                           _closestEnbForEf,
                                                                                           _threeClosestEnb,
                                                                                           _efPos)

    gnbMeasurements = scenario_creation.decode_measurements_data(measurement_encoder.output())
    gnbResources = scenario_creation.decode_gnb_resources_data(resources_encoder.output())
    gnbAssignments = scenario_creation.decode_assignment_data(assign_encoder.output())

    EfDataPrep = trasform.EfAssignDataPreparation(assignments=gnbAssignments,
                                                  gnbAvailableResources=gnbResources,
                                                  measurements=gnbMeasurements,
                                                  )


    # Creating the optimization
    # n_particles = EfDataPrep.nrGnbs * EfDataPrep.nrEfs
    # n_particles = 100
    # dimensions = EfDataPrep.nrEfs
    # # Set-up hyperparameters
    # options = {'c1': 0.5, 'c2': 0.3, 'w': 0.3, 'k':1, 'p':2}
    # # setting the initial position
    # # random from 0:3
    # init_pos = np.random.randint(3, size=(n_particles, dimensions))
    #
    # ipso = ipso_formulation.IntegerPSO(n_particles, dimensions, options=options, velocity_clamp=(-3, 3), init_pos=init_pos)
    # # Perform optimization
    # cost, pos = ipso.optimize(EfDataPrep.cost_function, iters=100)
    #
    # # Plot the cost
    # plot_cost_history(ipso.cost_history)
    # # plt.show()
    #
    # m = Mesher(func=fx.sphere,
    #            limits=[(-3, 3), (-3, 3)])
    # # Adjust figure limits
    # d = Designer(limits=[(-3, 3), (-3, 3), (-100000, 100)],
    #              label=['x-axis', 'y-axis', 'z-axis'])
    #
    # # ani = plot_contour(pos_history=ipso.pos_history, mesher=m, designer=d, mark=(0, 0))
    #
    # pos_history_3d = m.compute_history_3d(ipso.pos_history)  # preprocessing
    # animation3d = plot_surface(pos_history=pos_history_3d,
    #                            mesher=m, designer=d,
    #                            mark=(0, 0, 0))
    # #
    # plt.show()

    # Greedy algorithm
    greedy = GreedyFormulation(allUsers=EfDataPrep.allImsi, mcsTable=EfDataPrep.mcsTable,
                               gnbResources=EfDataPrep.gnbResources, startingAssignment=EfDataPrep.assignmentsTable)

    _optimized_assign_list = greedy.optimize()

    
