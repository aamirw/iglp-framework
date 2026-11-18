import os

from loguru import logger
from src.planner import jsonOperations, plannerOperations, schedulingOperations
from src.utils.consts import PLANNER_DEFAULT_ARGS
from src.utils.paths import DATA_PATH
from tqdm import tqdm

logger.remove()


def generate_plans(test_id, args=PLANNER_DEFAULT_ARGS):
    # Process the arguments
    input_filenames = args["input_filenames"]
    algo = args["algo"]
    visualizeFlag = args["visualize"]
    max_cost = args["max_cost"]
    max_plan_search = args["max_plan_search"]

    output_dir_path = DATA_PATH / test_id / "planner_outputs"
    output_dir_path.mkdir(parents=False, exist_ok=True)
    output_dir_path = output_dir_path / "json"
    output_dir_path.mkdir(parents=False, exist_ok=True)

    input_dir_path = DATA_PATH / test_id / "generated_planner_inputs"
    input_files = list(input_dir_path.rglob("*.json"))
    input_files.sort()
    plans_collection = []

    # process all or a selection of files
    pbar = tqdm(input_files, "Generating Plans")
    for input_file in pbar:
        if len(input_filenames) > 0 and input_file not in input_filenames:
            continue
        plan_data = {
            "scenario": None,
            "optCriteria": None,
            "plans": None,
            "output_file_plans": None,
            "output_file_schedules": None,
            "output_file_json": None,
        }
        plan_data["scenario"] = input_file.stem
        # create distinguish output filename if input filename contains 'input' keyword
        # Create corresponding folders for the output files
        pbar.set_postfix_str(f"Processing {input_file.stem}")
        output_path = output_dir_path / f"{input_file.stem}"
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output_file_json = output_path / f"{input_file.stem}.json"
        if visualizeFlag:
            output_file_plans = output_path / "plans"
            os.makedirs(output_file_plans)
            output_file_schedules = output_path / "schedules"
            os.makedirs(output_file_schedules)
            plan_data["output_file_plans"] = output_file_plans
            plan_data["output_file_schedules"] = output_file_schedules

        logger.info("Extract information from the input file.")
        (
            producerObjects,
            stateObjects,
            actionObjects,
            optCriteria,
            initialStates,
            finalStates,
        ) = jsonOperations.jsonReader(input_file)

        # Perform the planning
        plans = plannerOperations.backwardPlanning(
            initialStates, finalStates, actionObjects, algo, max_cost, max_plan_search
        )
        plan_data["optCriteria"] = optCriteria
        plan_data["plans"] = plans
        plan_data["output_file_json"] = output_file_json
        plan_data["producer_limit_pattern"] = args["producer_limit_pattern"]
        plans_collection.append(plan_data)
    return plans_collection


def post_process_plans(
    plans_collection,
    producers_limit_filters=None,
    cost_limit_filters=None,
    args=PLANNER_DEFAULT_ARGS,
):
    printFlag = args["print"]
    visualizeFlag = args["visualize"]
    max_plan_schedule = args["max_plan_schedule"]

    for i, plan_data in enumerate(plans_collection):
        optCriteria = plan_data["optCriteria"]
        plans = plan_data["plans"]
        output_file_plans = plan_data["output_file_plans"]
        output_file_schedules = plan_data["output_file_schedules"]
        output_file_json = plan_data["output_file_json"]
        if producers_limit_filters is not None:
            if plan_data["producer_limit_pattern"] == "alternate":
                producers_limit_filter = producers_limit_filters[
                    i % len(producers_limit_filters)
                ]
            else:
                idx = int(list(plan_data["scenario"])[0]) - 1
                producers_limit_filter = producers_limit_filters[idx]
            # filter plans by num_producer threshold
            plans, residuePlans = plannerOperations.filterPlansByNumProducers(
                plans, producers_limit_filter
            )
        if cost_limit_filters is not None:
            cost_limit_filter = cost_limit_filters[i]
            # filter plans by cost threshold
            plans, residuePlans = plannerOperations.filterPlansByCost(
                plans, cost_limit_filter
            )

        # Sort the plans based on the optimization criteria
        sortedPlans = plannerOperations.sortPlans(plans, optCriteria)
        # Print the plans
        if printFlag:
            plannerOperations.printPlans(sortedPlans)
        # Visualize the plans
        if visualizeFlag:
            plannerOperations.visualizePlans(sortedPlans, output_file_plans)
        # Perform the scheduling
        for planObj in sortedPlans:
            planObj.schedule()
        # Pruning the schedules
        prunedPlans = schedulingOperations.pruneScheduledPlans(
            sortedPlans, max_plan_schedule
        )
        # Print the schedules
        if printFlag:
            schedulingOperations.printSchedules(prunedPlans)
        # Visualize the schedules
        if visualizeFlag:
            schedulingOperations.visualizeSchedules(prunedPlans, output_file_schedules)
        # Write the schedules to a file
        jsonOperations.writeToJson(prunedPlans, output_file_json, optCriteria)
    print(">> Successfully generated plans and schedules.")
