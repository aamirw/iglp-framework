import copy
import csv
import json
import math
import random
from itertools import combinations

import matplotlib.pyplot as plt
import numpy as np
from src.utils.consts import (
    PCU,
    PRECON_DELIVERYTIME_LATEST_IN_WEEKS,
    PTU,
    TCU,
    TTU,
    WORKING_TIME_IN_HOURS,
)
from src.utils.paths import DATA_PATH


def extend_enterprises_list(n_producers, micro_percent, small_percent):
    enterprises = []
    # add remaining num to enterprise with smaller ratio
    if micro_percent < small_percent:
        num_micro = math.ceil(n_producers * micro_percent)
        num_small = math.floor(n_producers * small_percent)
    else:
        num_micro = math.floor(n_producers * micro_percent)
        num_small = math.ceil(n_producers * small_percent)
    num_remaining = n_producers - (num_micro + num_small)
    enterprises.extend(["micro"] * num_micro)
    enterprises.extend(["small"] * num_small)
    # extend with remaning enterprises if any in an alternate manner
    if num_remaining > 0:
        for i in range(num_remaining):
            if i % 2 == 0:
                enterprises.append(["micro"])
            else:
                enterprises.append(["small"])

    return enterprises


def generate_producers_coordinate(num_producers, enabled=False, producer_map_path=None):
    shipping_distances = {}
    producer_coords = []
    for i in range(num_producers):
        random.Random(i)
        a = random.randint(0, 100)
        b = random.randint(0, 100)
        producer_coords.append((a, b))
    for i, p1 in enumerate(producer_coords):
        distances = [math.dist(p2, p1) for p2 in producer_coords]
        shipping_distances[f"Producer_{i + 1}"] = int(round(np.mean(distances), 2))
    xs, ys = zip(*producer_coords)
    plt.figure()
    plt.scatter(xs, ys)
    plt.grid(True)
    plt.title("2D Map of Simulated Producer Network")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.title("Producers Coordinates")
    plt.savefig(producer_map_path)
    plt.close()
    return shipping_distances


def generate_producers(
    trades,
    n_producers,
    micro_percent=0.5,
    small_percent=0.5,
    shipping_distances=None,
):
    """
    Generates synthetic producer data.
    trades: list of trades (producer's speciality)
    n_producers: number of producers to generate
    """
    valueChainParameters = {
        "socialCommitment": 3.5,
        "familyFriendly": 4,
        "sustainability": 2,
    }

    # distribute enterprises based on percentage ratio
    enterprises = extend_enterprises_list(n_producers, micro_percent, small_percent)

    # create a list of producers with required parameters
    producers = []
    trade_id = 0

    for i in range(n_producers):
        producer_name = f"Producer_{i + 1}"
        producer = {
            "id": i + 1,
            "name": producer_name,
            "trade": trades[trade_id],
            "enterprise": enterprises[i],
            "valueChainParameters": valueChainParameters,
        }
        if shipping_distances:
            producer["meanShippingDistance"] = shipping_distances[f"Producer_{i + 1}"]
        producers.append(producer)
        trade_id += 1
        # reset trade_id to 0 when it exceeds list of trades
        if trade_id >= len(trades):
            trade_id = 0
    return producers


def get_preconditions_final_state(value_chain, trade):
    """
    Create final states with preconditions.

    trade: producer's speciality
    value_chain: list of product states representing value chain
    """
    preconditions_final_state = []
    for states in value_chain:
        for i, state in enumerate(states):
            current_trade = states[i - 1]["name"].split("_")[-1]
            if state["isFinalState"] and trade != current_trade:
                preconditions_final_state.append(
                    {
                        "id": states[i - 1]["id"],
                        "deliveryTimeLatestInWeeks": PRECON_DELIVERYTIME_LATEST_IN_WEEKS,
                    }
                )
    return preconditions_final_state


def generate_process_steps(value_chain):
    """
    Create all possible process steps using given value chain product states.

    value_chain: list of product states representing value chain
    """

    # begin by creating a list of all possible sate pairs
    state_combos = []
    for states in value_chain:
        state_combos.append(list(combinations(states, 2)))

    # create list of process steps using state combos by adding additional attributes for producer assignment later on
    process_steps = []
    for state_combo in state_combos:
        for state_pair in state_combo:
            process_step = {}
            process_step["initialStateId"] = state_pair[0]["id"]
            process_step["initialStateName"] = state_pair[0]["name"]
            process_step["finalStateId"] = state_pair[1]["id"]
            process_step["finalStateName"] = state_pair[1]["name"]
            process_step["stepsRequired"] = abs(
                state_pair[0]["index"] - state_pair[1]["index"]
            )
            process_step["tradeRequired"] = state_pair[0]["name"].split("_")[-1]
            process_step["preconditions"] = None
            if state_pair[0]["isFinalState"] or state_pair[1]["isFinalState"]:
                process_step["isFinalStep"] = True
                # define preconditions if a state if final state and length of value chain > 1
                if len(value_chain) > 1:
                    preconditions_final_state = get_preconditions_final_state(
                        value_chain, process_step["tradeRequired"]
                    )
                    process_step["preconditions"] = preconditions_final_state
            else:
                process_step["isFinalStep"] = False
            process_steps.append(process_step)
    return process_steps


def add_producer_to_process_step(producers, process_steps):
    """
    Assign producer to each of the process_steps following the assumption conditions.

    producers: list of producers
    process_steps: list of process_steps
    """

    # optimised process steps list extension
    process_steps_extended = []
    for i in range(len(producers)):
        for step in process_steps:
            process_steps_extended.append(copy.deepcopy(step))
    process_steps = process_steps_extended

    added_producers_to_step = []
    new_process_steps = []

    # assign each producer a process step such that step has not already been executed and producer is allowed enough steps to complete it
    for producer in producers:
        # define number of steps that can be executed by micro and small enterprises
        if producer["enterprise"] == "micro":
            allowed_combinations = 1
        elif producer["enterprise"] == "small":
            allowed_combinations = 2

        # when all process steps are exhausted clear process steps assigned list for remaining producer assignment
        if len(added_producers_to_step) == len(process_steps):
            added_producers_to_step = []

        # assign producer along with other required parameters following assumptions listed in paper
        processed_step = None
        for i, process_step in enumerate(process_steps):
            if (i in added_producers_to_step) or (
                process_step["tradeRequired"] != producer["trade"]
            ):
                continue
            if (
                process_step["initialStateId"],
                process_step["finalStateId"],
            ) == processed_step:
                continue
            # dynamic tcu calculation
            tcu = TCU
            ttu = TTU
            if "meanShippingDistance" in producer:
                tcu = producer["meanShippingDistance"] * TCU
                ttu = producer["meanShippingDistance"] * TTU
            if process_step["stepsRequired"] == 1 and producer["enterprise"] == "micro":
                process_step["producerId"] = producer["id"]
                if not process_step["isFinalStep"]:
                    costs = PCU + tcu
                    processingTimeInWeeks = PTU + ttu
                else:
                    costs = PCU
                    processingTimeInWeeks = PTU
                process_step["costs"] = costs
                process_step["processingTimeInWeeks"] = processingTimeInWeeks
                process_step["workingTimeInHours"] = WORKING_TIME_IN_HOURS
                new_process_steps.append(process_step)
                added_producers_to_step.append(i)
                processed_step = (
                    process_step["initialStateId"],
                    process_step["finalStateId"],
                )
                allowed_combinations -= 1
                if allowed_combinations == 0:
                    break
            elif (
                process_step["stepsRequired"] >= 1 and producer["enterprise"] == "small"
            ):
                process_step["producerId"] = producer["id"]
                if not process_step["isFinalStep"]:
                    costs = PCU * process_step["stepsRequired"] + tcu
                    processingTimeInWeeks = PTU * process_step["stepsRequired"] + ttu
                else:
                    costs = PCU * process_step["stepsRequired"]
                    processingTimeInWeeks = PTU * process_step["stepsRequired"]
                process_step["costs"] = costs
                process_step["processingTimeInWeeks"] = processingTimeInWeeks
                process_step["workingTimeInHours"] = WORKING_TIME_IN_HOURS
                new_process_steps.append(process_step)
                added_producers_to_step.append(i)
                processed_step = (
                    process_step["initialStateId"],
                    process_step["finalStateId"],
                )
                allowed_combinations -= 1
                if allowed_combinations == 0:
                    break
            else:
                continue

    return new_process_steps


def generate_csv_files(value_chain, producers, process_steps, output_file="sample"):
    """
    Represent planner input in csv format for better readability and manual verification
    """
    with open(f"{output_file}.csv", "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Value chain states:"])
        writer.writeheader()

        fieldnames = value_chain[0][0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, states in enumerate(value_chain):
            if i < len(value_chain) - 1:
                states = states[:-1]
            for state in states:
                writer.writerow(state)

    with open(f"{output_file}.csv", "a", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Producers:"])
        writer.writeheader()

        fieldnames = producers[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for producer in producers:
            writer.writerow(producer)

    with open(f"{output_file}.csv", "a", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Process steps:"])
        writer.writeheader()

        fieldnames = process_steps[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for process_step in process_steps:
            writer.writerow(process_step)


def generate_json_files(value_chain, producers, process_steps, output_file="sample"):
    """Save planner input in JSON format as required by planner"""

    # Remove additional attributes from value chain product states, producers and process_steps
    flat_value_chain = []
    for i, states in enumerate(value_chain):
        for state in states:
            if state["isFinalState"] and i < len(value_chain) - 1:
                continue
            if not state["isStartState"]:
                state.pop("isStartState")
            if not state["isFinalState"]:
                state.pop("isFinalState")
            state.pop("index")
            flat_value_chain.append(state)
    flat_value_chain.sort(key=lambda x: x["id"])

    for i, process_step in enumerate(process_steps):
        process_step["id"] = i + 1
        if process_step["preconditions"] is None:
            process_step.pop("preconditions")
        process_step.pop("initialStateName")
        process_step.pop("finalStateName")
        process_step.pop("stepsRequired")
        process_step.pop("tradeRequired")
        process_step.pop("isFinalStep")

    output_json = {
        "optimizeFor": "cost",
        "producer": producers,
        "states": flat_value_chain,
        "processSteps": process_steps,
    }
    with open(f"{output_file}.json", "w", encoding="utf-8") as f:
        json.dump(output_json, f)


def fetch_input(filepath):
    """Load resilience input file and return extracted attributes"""

    with open(filepath, encoding="utf-8") as f:
        input_json = json.load(f)
        return (
            input_json["scenario_id"],
            input_json["scenario_name"],
            input_json["n_producers"],
            input_json["enterprise_split"],
            input_json["trades"],
            input_json["value_chain"],
            input_json["value_chain_print"],
        )


def generate_planner_input(test_id, shipping_distances_collection=None):
    input_path = DATA_PATH / test_id / "generated_vc_scenarios"
    output_path = DATA_PATH / test_id / "generated_planner_inputs"

    csv_output_path = output_path / "csv"
    csv_output_path.mkdir(exist_ok=True, parents=True)

    json_output_path = output_path / "json"
    json_output_path.mkdir(exist_ok=True, parents=True)

    input_files = list(input_path.rglob("*.json"))

    for input_file in input_files:
        (
            scenario_id,
            scenario_name,
            n_producers,
            enterprise_split,
            trades,
            value_chain,
            value_chain_print,
        ) = fetch_input(input_file)
        micro_percent, small_percent = enterprise_split

        shipping_distances = shipping_distances_collection[n_producers][
            "shippingDistances"
        ]
        producers = generate_producers(
            trades,
            n_producers,
            micro_percent,
            small_percent,
            shipping_distances,
        )
        process_steps = generate_process_steps(value_chain)

        process_steps = add_producer_to_process_step(producers, process_steps)

        generate_csv_files(
            value_chain,
            producers,
            process_steps,
            csv_output_path / f"{scenario_id}",
        )

        generate_json_files(
            value_chain,
            producers,
            process_steps,
            json_output_path / f"{scenario_id}",
        )
    print(">> Successfully generated planner input.")


# gen_planner_input()

## python -m src.input_simulator.plannerInputGenerator
