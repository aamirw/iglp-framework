import json

import pandas as pd
from src.utils.paths import DATA_PATH


def transform_to_csv(test_id):
    output_path = DATA_PATH / test_id / "planner_outputs"
    csv_output_path = output_path / "csv"
    csv_output_path.mkdir(exist_ok=True, parents=False)

    json_output_path = output_path / "json"
    output_files = list(json_output_path.rglob("*.json"))
    output_files.sort()
    for output_file in output_files:
        with open(output_file, "r", encoding="utf-8") as f:
            output_data = json.load(f)
            if "plans" in output_data:
                output_data["totalPlans"] = len(output_data["plans"])
                df_norm = pd.json_normalize(
                    output_data,
                    ["plans", "actions", "preconditions"],
                    [
                        ["plans", "planId"],
                        ["plans", "planValue"],
                        ["plans", "actions", "id"],
                        ["plans", "actions", "finalStateId", "id"],
                        ["plans", "actions", "finalStateId", "name"],
                        ["plans", "actions", "finalStateId", "isStartState"],
                        ["plans", "actions", "finalStateId", "isFinalState"],
                        ["plans", "actions", "costs"],
                        ["plans", "actions", "startingPoint"],
                        ["plans", "actions", "endingPoint"],
                        ["plans", "actions", "producerId", "id"],
                        ["plans", "actions", "producerId", "name"],
                        ["plans", "actions", "producerId", "trade"],
                        ["plans", "actions", "producerId", "enterprise"],
                        ["plans", "actions", "producerId", "valueChainParameters"],
                        ["plans", "actions", "processingTimeInWeeks"],
                        ["plans", "actions", "workingTimeInHours"],
                        "optimizeFor",
                        "minimumPlan",
                        "maximumPlan",
                        "numberOfPlans",
                        "totalPlans",
                    ],
                    errors="ignore",
                )
                df_norm.to_csv(csv_output_path / f"{output_file.stem}.csv")
            else:
                df = pd.DataFrame(
                    columns=["totalPlans", "minimumPlan", "maximumPlan"],
                    data=[[0, 0, 0]],
                )
                df.to_csv(csv_output_path / f"{output_file.stem}.csv")
    print(">> Successfully transformed planner json output to csv.")
