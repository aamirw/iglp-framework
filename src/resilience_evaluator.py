import itertools
import math
import random

import matplotlib.pyplot as plt
import numpy as np
from src.input_simulator.plannerInputGenerator import generate_planner_input
from src.input_simulator.value_chain_generator import generate_vc_scenarios
from src.planner.runner import generate_plans, post_process_plans
from src.resilience_analysis.analysis import generate_analysis
from src.resilience_analysis.summarize_tests import show_summary_plot
from src.resilience_analysis.transformOutputToCSV import transform_to_csv
from src.test_configs.experiments import test_scenarios
from src.utils.consts import PLANNER_DEFAULT_ARGS
from src.utils.paths import DATA_PATH


def generate_producers_coordinate(num_producers, enabled=False, producer_map_path=None):
    shipping_distances = {}
    producer_coords = []
    for i in range(num_producers):
        random.seed(i)
        a = random.randint(0, 100)
        b = random.randint(0, 100)
        producer_coords.append((a, b, f"P{i + 1}"))
    for i, p1 in enumerate(producer_coords):
        distances = [math.dist(p2[:-1], p1[:-1]) for p2 in producer_coords]
        shipping_distances[f"Producer_{i + 1}"] = int(round(np.mean(distances), 2))
    x, y, labels = zip(*producer_coords)
    plt.figure()
    plt.scatter(x, y)
    for i, label in enumerate(labels):
        plt.annotate(label, (x[i], y[i]), textcoords="offset points", xytext=(5, 5))
    plt.xlim(0, 100)
    plt.ylim(0, 100)
    plt.grid(True)
    plt.title("2D Map of Simulated Producer Network")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.title("Producers Coordinates")
    plt.savefig(producer_map_path)
    plt.close()
    return shipping_distances


def test_suite_evaluation(test_scenarios):
    for test_id, inputs in test_scenarios.items():
        if not inputs["skip"]:
            print(f"Running test: {test_id}")
            # 1. Generate value chain scenarios from value chain parameters
            generate_vc_scenarios(test_id, inputs)

            # 2. Simulate producer coordinates and distances
            shipping_distance_simulation = inputs["shipping_distance_simulation"]
            shipping_distances_collection = {}
            maxShippingDistances = None
            if shipping_distance_simulation:
                nw_sizes = inputs["nw_sizes"]
                for nw_size in nw_sizes:
                    shippingDistances = None
                    shipping_distances_data = {
                        "meanDistanceAll": None,
                        "shippingDistances": None,
                    }
                    producer_map_path = (
                        DATA_PATH
                        / test_id
                        / f"simulated_producer_map_{max(nw_sizes)}.png"
                    )
                    if maxShippingDistances is None:
                        maxShippingDistances = generate_producers_coordinate(
                            num_producers=max(nw_sizes),
                            enabled=shipping_distance_simulation,
                            producer_map_path=producer_map_path,
                        )
                    shippingDistances = dict(
                        itertools.islice(maxShippingDistances.items(), nw_size)
                    )
                    avg_distance = np.mean(list(shippingDistances.values()))  # debug
                    shipping_distances_data["shippingDistances"] = shippingDistances
                    shipping_distances_data["meanDistanceAll"] = avg_distance
                    shipping_distances_collection[nw_size] = shipping_distances_data

            # 3. Generate planner input for given each value chain scenario
            generate_planner_input(test_id, shipping_distances_collection)

            # 4. Generate plans using planner
            planner_args = PLANNER_DEFAULT_ARGS
            planner_args["max_plan_search"] = inputs["max_plan_search"]
            planner_args["max_plan_schedule"] = inputs["max_plan_schedule"]
            planner_args["producers_limit_filters"] = inputs["producers_limit_filters"]
            planner_args["cost_limit_filters"] = inputs["cost_limit_filters"]
            planner_args["producer_limit_pattern"] = inputs["producer_limit_pattern"]
            plans_collection = generate_plans(test_id, args=planner_args)

            # 5. Filter, sort, schedule and save
            post_process_plans(
                plans_collection,
                planner_args["producers_limit_filters"],
                planner_args["cost_limit_filters"],
                planner_args,
            )

            # 4. Generate analysis data and visualisation for test case
            nw_sizes = inputs["nw_sizes"]
            transform_to_csv(test_id)
            generate_analysis(test_id, nw_sizes)
        else:
            print(f"Skipping test: {test_id}")
    # 5. Generate a summary plot using all test scenario analysis results
    show_summary_plot()


test_suite_evaluation(test_scenarios)

## python -m src.resilience_evaluator
