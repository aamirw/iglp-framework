import argparse
import os
from pathlib import Path

import jsonOperations
import plannerOperations
import schedulingOperations
from loguru import logger
from root_path import rootpath

logger.remove(0)
logger.add(
    "logs/file_{time}.log",
    level="INFO",
    format="{time:MMMM D, YYYY > HH:mm:ss} | {level} | {message}",
)

logger.info("Starting Program. Parsing Arguments.")
parser = argparse.ArgumentParser()
# General parameters
parser.add_argument(
    "--input-dir",
    type=str,
    required=False,
    help="Name of the input directory which contains input_files.",
)
parser.add_argument(
    "--input-filenames",
    type=list[str],
    required=False,
    default=[],
    help="List of input filename(s) without .json file extension.",
)
parser.add_argument(
    "--algo",
    type=str,
    required=False,
    default="BFS",
    help="The algorithm to be used for planning. For now, only BFS is supported.",
)
parser.add_argument(
    "--print",
    action="store_true",
    default=False,
    help="Print the plans or not. If yes, it will print the plans.",
)
parser.add_argument(
    "--visualize",
    action="store_true",
    default=False,
    help="Visualize the plans or not. If yes, it will visualize the plans.",
)
parser.add_argument(
    "--output",
    type=str,
    required=False,
    help="The address to which the output file should be written.",
)
parser.add_argument(
    "--max-cost",
    type=int,
    required=False,
    default=-1,
    help="The maximum cost for searching the plans.",
)
parser.add_argument(
    "--io-path",
    type=str,
    required=False,
    default=-1,
    help="The path to directory where input and output folders should be stored.",
)
parser.add_argument(
    "--max-plan-search",
    type=int,
    default=1000,
    help="The maximum number of plans to be searched.",
)
parser.add_argument(
    "--max-plan-schedule",
    type=int,
    default=30,
    help="The maximum number of plans to schedule.",
)
logger.info("Arguments parsed sucessfully.")

if __name__ == "__main__":
    args = parser.parse_args()
    # Process the arguments
    input_dir = args.input_dir
    input_filenames = args.input_filenames
    algo = args.algo
    printFlag = args.print
    visualizeFlag = args.visualize
    output_subdir = args.output
    max_cost = args.max_cost
    io_path = args.io_path
    max_plan_search = args.max_plan_search
    max_plan_schedule = args.max_plan_schedule

    if io_path != -1:  # user provided I/O directory path is available
        basepath = Path(io_path)
    else:  # default I/O directory path
        basepath = rootpath

    input_dir_path = basepath / "inputs/planner" / input_dir

    input_files = [file.stem for file in list(input_dir_path.rglob("*.json"))]

    # process all or a selection of files
    for input_file in input_files:
        if len(input_filenames) > 0 and input_file not in input_filenames:
            continue
        # create distinguish output filename if input filename contains 'input' keyword
        output_file = input_file.replace("input", "output")

        input_file = input_dir_path / f"{input_file}.json"

        # Create corresponding folders for the output files
        output_path = basepath / "outputs/planner" / output_subdir / output_file
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output_file_json = output_path / f"{output_file}.json"
        if visualizeFlag:
            output_file_plans = output_path / "plans"
            os.makedirs(output_file_plans)
            output_file_schedules = output_path / "schedules"
            os.makedirs(output_file_schedules)

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
