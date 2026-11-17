# Pre-defined planner input generator parameters
PCU = 200  # Production cost unit
PTU = 3  # Production time unit
TCU = 1.5  # Transport cost unit
TTU = 0.5  # Transport time unit
PRECON_DELIVERYTIME_LATEST_IN_WEEKS = 1
WORKING_TIME_IN_HOURS = 8.5

PLANNER_DEFAULT_ARGS = {
    "input_dir": "default",
    "input_filenames": [],
    "algo": "BFS",
    "print": False,
    "visualize": False,
    "output": "default",
    "max_cost": -1,
    "io_path": -1,
    "max_plan_search": 1000,
    "max_plan_schedule": 1000,
    "producers_limit_filters": None,
    "producer_limit_pattern": "alternate",
    "cost_limit_filters": None,
}
