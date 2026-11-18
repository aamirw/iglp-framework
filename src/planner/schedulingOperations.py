from loguru import logger

def visualizeSchedules(plans, output_file_schedules):
    for plan in plans:
        plan.getScheduleVisualization(output_file_schedules)


def printSchedules(plans):
    logger.info(f"Total number of scheduled plans: {len(plans)}")
    print(f"Total number of scheduled plans: {len(plans)}")
    for plan in plans:
        plan.schedulePrinting()
        print("-" * 20)


def pruneScheduledPlans(plans, max_plans_schedule=30):
    logger.info("Pruning the given plans")
    return list(set(plans))[:max_plans_schedule]