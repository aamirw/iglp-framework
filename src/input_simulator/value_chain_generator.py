# Generates value chains and saves in text and json format
# inputs: (low_hor,3),(low_ver,3,3),(medium_hor,5),(medium_ver,4,3,3,3),(high_hor,6,3),(high_ver,4,4,4,3,3)
import itertools
import json

import pandas as pd
from src.utils.paths import DATA_PATH


def num_to_char(n):
    return chr(ord("A") + n)


def get_trades(n):
    trades = []
    for i in range(n):
        trade = num_to_char(i)
        trades.append(trade)
    return trades


def save_json(data, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f)


def gen_vc(
    input,
    nw_size,
    scenario_id,
    scenario_name,
    enterprise_split,
    producers_limit_filter,
    cost_limit_filter,
):
    vc_type = input[0]
    vc_dim = input[1]
    trades = get_trades(len(vc_dim))

    vc_json = {
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "n_producers": nw_size,
        "enterprise_split": enterprise_split,
        "trades": trades,
        "producers_limit_filter": producers_limit_filter,
        "cost_limit_filter": cost_limit_filter,
        "value_chain": [],
        "value_chain_print": "",
    }
    for i, level in enumerate(vc_dim):
        sub_chain = []
        for j in range(level):
            node = {
                "id": None,
                "name": None,
                "isStartState": False,
                "isFinalState": False,
                "index": j + 1,
            }
            suff = j
            if j == 0:
                node["id"] = i + 1
                node["isStartState"] = True
                suff = "start"
            elif j == level - 1:
                node["id"] = sum(vc_dim) - (len(vc_dim) - 1)
                node["isFinalState"] = True
                suff = "end"
            else:
                node["id"] = i + 1 + (len(vc_dim) * j)
                suff = f"middle{j}"

            # add trade label to suffix
            trade_suff = f"_{num_to_char(i)}"
            if "end" in suff:
                trade_suff = ""
            node_name = f"{vc_type}_{suff}{trade_suff}"
            node["name"] = node_name

            vc_json["value_chain_print"] += node_name
            if "end" not in node_name:
                vc_json["value_chain_print"] += " -> "

            sub_chain.append(node)
        vc_json["value_chain"].append(sub_chain)
        vc_json["value_chain_print"] += "\n"
    id = 1
    for j in range(max(vc_dim)):
        for i in range(len(vc_json["value_chain"])):
            if j < len(vc_json["value_chain"][i]) and (
                "end" not in vc_json["value_chain"][i][j]["name"]
            ):
                vc_json["value_chain"][i][j]["id"] = id
                id += 1
    return vc_json


def generate_vc_scenarios(test_id, inputs):
    outpath = DATA_PATH / test_id / "generated_vc_scenarios"
    outpath.mkdir(parents=True, exist_ok=True)
    vc_params = inputs["vc_params"]
    enterprise_splits = inputs["enterprise_splits"]
    nw_sizes = inputs["nw_sizes"]
    producers_limit_filters = inputs["producers_limit_filters"]
    cost_limit_filters = inputs["cost_limit_filters"]
    producer_limit_pattern = inputs["producer_limit_pattern"]

    scenarios_df_data = {
        "scenario_id": [],
        "scenario_name": [],
        "product_complexity": [],
        "network_type": [],
        "network_size": [],
        "enterprise_ratio": [],
        "producer_limit": [],
        "cost_limit": [],
    }
    scenario_names = [
        "med_hor_12_50-50_3",
        "med_hor_18_50-50_3",
        "med_hor_12_25-75_3",
        "med_hor_18_25-75_3",
        "med_hor_12_75-25_3",
        "med_hor_18_75-25_3",
        "med_ver_12_50-50_5",
        "med_ver_18_50-50_5",
        "med_ver_12_25-75_5",
        "med_ver_18_25-75_5",
        "med_ver_12_75-25_5",
        "med_ver_18_75-25_5",
        "high_hor_12_50-50_4",
        "high_hor_18_50-50_4",
        "high_hor_12_25-75_4",
        "high_hor_18_25-75_4",
        "high_hor_12_75-25_4",
        "high_hor_18_75-25_4",
        "high_ver_12_50-50_7",
        "high_ver_18_50-50_7",
        "high_ver_12_25-75_7",
        "high_ver_18_25-75_7",
        "high_ver_12_75-25_7",
        "high_ver_18_75-25_7",
    ]
    scenario_list = [
        f"{s[0]}{s[1]}"
        for s in itertools.product([1, 2, 3, 4], ["a", "b", "c", "d", "e", "f"])
    ]
    # print(scenarios_list)
    for i, data1 in enumerate(
        itertools.product(vc_params, enterprise_splits, nw_sizes)
    ):
        vc_input = data1[0]
        enterprise_split = data1[1]
        nw_size = data1[2]
        scenario_id = scenario_list[i]
        scenario_name = scenario_names[i]
        if producers_limit_filters is None:
            producers_limit_filter = None
        else:
            if producer_limit_pattern == "alternate":
                producers_limit_filter = producers_limit_filters[
                    i % len(producers_limit_filters)
                ]
            else:
                idx = int(list(scenario_id)[0]) - 1
                producers_limit_filter = producers_limit_filters[idx]
        if cost_limit_filters is not None:
            cost_limit_filter = cost_limit_filters[i]
        else:
            cost_limit_filter = None
        # print(i, scenario_name, producers_limit_filter, cost_limit_filter)
        vc_json = gen_vc(
            vc_input,
            nw_size,
            scenario_id,
            scenario_name,
            enterprise_split,
            producers_limit_filter,
            cost_limit_filter,
        )
        save_json(
            vc_json,
            f"{outpath}/{scenario_id}.json",
        )

        scenarios_df_data["scenario_id"].append(vc_json["scenario_id"])
        scenarios_df_data["scenario_name"].append(vc_json["scenario_name"])
        scenarios_df_data["product_complexity"].append(vc_input[0].split("_")[0])
        scenarios_df_data["network_type"].append(vc_input[0].split("_")[1])
        scenarios_df_data["network_size"].append(nw_size)
        scenarios_df_data["enterprise_ratio"].append(enterprise_split)
        scenarios_df_data["producer_limit"].append(producers_limit_filter)
        scenarios_df_data["cost_limit"].append(cost_limit_filter)
    scenarios_df = pd.DataFrame(data=scenarios_df_data)
    scenarios_df.to_csv(f"{outpath}/scenarios_data.csv", index=False)
    print(">> Successfully generated VC scenarios")


# input template : (vc_type, num_producer/nw_size, vc_dim)

## python -m src.input_simulator.value_chain_generator
