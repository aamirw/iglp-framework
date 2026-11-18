from loguru import logger
from src.planner import plan
from src.planner.fringe import Fringe


def applicable(stateSet, actionPrecon):
    """
    This function is used in a progression planner where we want to see if a
    specific action can be applied based on the current set of states. For this,
    All pre-conditions of an action should be present among current states.
    """
    precons = set([x["state_object"] for x in actionPrecon])
    if precons.issubset(stateSet):
        return True
    return False


def apply(actionPrecon, actionEffect, currentStateSet):
    """
    This function will be called whenever a specific action is applicable.
    Firstly, the preconditions of that action are removed (assumption of consuming pre-conditions),
    and all effects of that action are also added.
    Input arguments:
       actionPrecon: set of objects of an action's preconditions
       actionEffect: set of objects of an action's effects
       currentStateSet: set contains all current states
    """
    precons = set([x["state_object"] for x in actionPrecon])
    newStateSet = currentStateSet.difference(precons)
    newStateSet.add(actionEffect)
    return newStateSet


def applicableBackward(stateSet, actionEffect):
    """
    This function checks if all effects of an action are present in the current states.
    If so, it means we can backtrack from this action.
    """
    actioEffectSet = set()
    actioEffectSet.add(actionEffect)
    if actioEffectSet.issubset(stateSet):
        return True
    return False


def applyBackward(actionPrecon, actionEffect, currentStateSet):
    """
    This function applies an action in the backward fashion. So, firstly, all
    effects of the action are removed and then all of its preconditions are added.
    """
    actionEffectSet = set()
    actionEffectSet.add(actionEffect)
    newStateSet = currentStateSet.difference(actionEffectSet)
    for precon in actionPrecon:
        newStateSet.add(precon["state_object"])
    return newStateSet


def isMaximumCostExceeded(actionSeq, newAction, max_cost):
    """
    This function checks if the cost of a plan is exceeded the maximum cost.
    """
    current_cost = sum(action.getObjectives()["cost"] for action in actionSeq)
    current_cost += newAction.getObjectives()["cost"]
    if max_cost != -1 and current_cost > max_cost:
        return True
    return False


def forwardPlanning(initialStates, finalStates, actionObjects, traversalMethod):
    """
    This function performs the forward planning, by considering a fringe where its element is a list
    with two elements [stateset,actionsequence], where stateset shows current states and actionsequence
    shows which actions have been taken that we reached this set of states. Then iteratively, all actions
    are tested to see if we can go backward or not.
    Input arguments:
          initialStates: set contains initial states
          finalsStates: set contains final states
          actionObjects: list of all objetcs of actions
          traversalMethod: how we traverse the planning graph, for now only BFS is supported
    """
    # Setting Fringe Parameters
    fringe = Fringe()
    fringe.set_traversal_method(traversalMethod)
    fringe.init_fringe()
    # Fringe initialization
    fringe.insert([initialStates, []])
    visited = set([tuple(initialStates)])
    plans = []
    while not fringe.is_empty():
        # Each fringe element has this shape [stateSet, actionSequence]
        pathInfo = fringe.pop()
        stateSet = pathInfo[0]
        actionSequence = pathInfo[1]
        for act in actionObjects:
            # if action is applicable
            if applicable(stateSet, act.preconditions):
                # Apply the function
                newStateSet = apply(act.preconditions, act.finalState, stateSet)
                newActionSequence = actionSequence.copy()
                if finalStates.issubset(newStateSet):
                    # if stateListOperations.isGoalAchieved(newStateSet,
                    # finalStates):
                    newActionSequence.append(act)
                    plans.append(newActionSequence)
                else:
                    newActionSequence.append(act)
                    fringe.insert([newStateSet, newActionSequence])
                    visited.add(tuple(newStateSet))
    return plans


def backwardPlanning(
    initialStates,
    finalStates,
    actionObjects,
    traversalMethod,
    max_cost=-1,
    max_plan_search=1000,
):
    """
    This function, similar to the forward version, provides the algorithm to backtrack
    all the way to the initial state.
    """
    logger.info("Setting Fringe Parameters.")
    fringe = Fringe()
    fringe.set_traversal_method(traversalMethod)
    fringe.init_fringe()
    logger.info("Starting planning.")
    fringe.insert([finalStates, []])
    visited = set([tuple(finalStates)])
    plans = []

    while len(plans) < max_plan_search and not fringe.is_empty():
        pathInfo = fringe.pop()
        stateSet = pathInfo[0]
        actionSequence = pathInfo[1]
        for act in actionObjects:
            if applicableBackward(stateSet, act.finalState) and (
                not isMaximumCostExceeded(actionSequence, act, max_cost)
            ):
                newStateSet = applyBackward(act.preconditions, act.finalState, stateSet)
                newActionSequence = actionSequence.copy()
                if newStateSet.issubset(initialStates):
                    # if
                    # stateListOperations.isGoalAchievedBackward(newStateSet,
                    # initialStates):
                    newActionSequence.append(act)
                    # plans.append(newActionSequence)
                    plans.append(plan.Plan(actionSequence=newActionSequence))
                    logger.info(plans[-1])
                    # print(plans[-1])
                else:
                    newActionSequence.append(act)
                    fringe.insert([newStateSet, newActionSequence])
                    visited.add(tuple(newStateSet))
    return plans


def visualizePlans(plans, output_file_plans):
    for p in plans:
        p.getPlanVisualization(output_file_plans)


def printPlans(sortedPlans):
    logger.info(f"Total number of plans: {len(sortedPlans)}")
    print(f"Total number of plans: {len(sortedPlans)}")
    for p in sortedPlans:
        print(p)
        print("-" * 20)


def sortPlans(plans, optCriteria):
    # sortedPlans = sorted(plans, key=lambda plan: sum(action.getObjectives()[optCriteria] for action in plan))
    sortedPlans = sorted(plans, key=lambda plan: plan.computePlanValue(optCriteria))
    # criteria_values = [plan.getPlanValue(optCriteria) for plan in sortedPlans]
    logger.info("Plans Sorted")
    return sortedPlans


def filterPlansByNumProducers(plans, num_producer_limit):
    if num_producer_limit is None or len(plans) == 0:
        return plans
    filteredPlans = []
    residuePlans = []
    for i, p in enumerate(plans):
        if len(p.actionSequence) <= num_producer_limit:
            filteredPlans.append(p)
        else:
            residuePlans.append(p)
    return filteredPlans, residuePlans


def filterPlansByCost(plans, cost_limit):
    if cost_limit is None or len(plans) == 0:
        return plans
    filteredPlans = []
    residuePlans = []
    for i, p in enumerate(plans):
        if p.getPlanValue() <= cost_limit:
            filteredPlans.append(p)
        else:
            residuePlans.append(p)
    return filteredPlans, residuePlans
