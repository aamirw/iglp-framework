# ### Prerequisite
# [Required only once] Please run transformOutputToCSV script, if haven't already, to transform JSON formatted planner output into CSV format which is used for generating plots.
# Command: `python -m src.resilience.analysis.transformOutputToCSV`


import matplotlib.pyplot as plt
import pandas as pd
from src.utils.paths import DATA_PATH

COUNT_BY_VC = False  # Flag to compute redundacy anad flexibility based on value chain (cluster) count or plans (value chain alternatives) count


# create new summary_df by aggregating producers and costs involved in completing each step of a given combinedStatesName
def summarize_plans(df_view):
    grouped_df = df_view.groupby("plans.planId")
    summary_df = pd.DataFrame(
        columns=[
            "planId",
            "combinedStatesName",
            "producers",
            "totalCost",
            "stepRedundancyCount",
        ]
    )
    planId = []
    combinedStatesName = []
    producers = []
    totalCost = []
    stepRedundancyCount = []
    for name, group in grouped_df:
        producer_group = []
        combinedNames = ""
        costs = 0
        locplanId = None
        if len(group) > 1:
            for i in range(len(group)):
                element = group.iloc[i]
                locplanId = element["plans.planId"]
                combinedNames += (
                    f"{element['name']}-{element['plans.actions.finalStateId.name']}-"
                )
                producer_group.append(element["plans.actions.producerId.name"])
                costs = element["plans.planValue"]
            planId.append(locplanId)
            combinedStatesName.append(combinedNames[:-1])
            totalCost.append(costs)
            producers.append(producer_group)
        else:
            element = group.iloc[0]
            planId.append(element["plans.planId"])
            combinedStatesName.append(
                f"{element['name']}-{element['plans.actions.finalStateId.name']}"
            )
            producers.append([element["plans.actions.producerId.name"]])
            totalCost.append(element["plans.planValue"])
        stepRedundancyCount.append(group["stepRedundancyCount"].values)
    summary_df["planId"] = planId
    summary_df["combinedStatesName"] = combinedStatesName
    summary_df["stepRedundancyCount"] = stepRedundancyCount
    summary_df["valueChainsCount"] = [
        len(summary_df.groupby("combinedStatesName"))
    ] * len(summary_df)
    summary_df["producers"] = producers
    summary_df["totalCost"] = totalCost
    return summary_df


# compute number of bottleneck, weakly, moderately and strongly flexible chains by VC count
def get_flexibile_vc_counts(summary_df):
    bottleneckChains = 0
    weakFlexibleChains = 0
    moderateFlexibleChains = 0
    strongFlexibleChains = 0

    # bottleneckchains - chains with 0 replacement for the least flexible step of a plan
    # weakFlexibleChains - chains with 1 replacement for the least flexible step of a plan
    # moderateFlexibleChains - chains with 2 replacements for the least flexible step of a plan
    # strongFlexibleChains - chains with 3 or 4 replacements for the least flexible step of a plan
    for name, group in summary_df.groupby("combinedStatesName"):
        bottleneckPlanCounts = group[
            group["stepRedundancyCount"].apply(lambda x: min(x) == 1)
        ].shape[0]
        singleReplacementPlanCounts = group[
            group["stepRedundancyCount"].apply(lambda x: min(x) == 2)
        ].shape[0]
        doubleReplacementPlanCounts = group[
            group["stepRedundancyCount"].apply(lambda x: min(x) == 3)
        ].shape[0]
        multipleReplacementPlanCounts = group[
            group["stepRedundancyCount"].apply(lambda x: min(x) >= 4)
        ].shape[0]

        if bottleneckPlanCounts > 0:
            bottleneckChains += 1

        if singleReplacementPlanCounts > 0:
            weakFlexibleChains += 1

        if doubleReplacementPlanCounts > 0:
            moderateFlexibleChains += 1

        if multipleReplacementPlanCounts > 0:
            strongFlexibleChains += 1

    return (
        bottleneckChains,
        weakFlexibleChains,
        moderateFlexibleChains,
        strongFlexibleChains,
    )


# compute number of bottleneck, weakly, moderately and strongly flexible chains by alternative VC count
def get_flexible_alternative_vc_counts(summary_df):
    # bottleneckchains - chains with 0 replacement for the least flexible step of a plan
    # weakFlexibleChains - chains with 1 replacement for the least flexible step of a plan
    # moderateFlexibleChains - chains with 2 replacements for the least flexible step of a plan
    # strongFlexibleChains - chains with 3 or 4 replacements for the least flexible step of a plan
    bottleneckChains = summary_df[
        summary_df["stepRedundancyCount"].apply(lambda x: min(x) == 1)
    ].shape[0]
    weakFlexibleChains = summary_df[
        summary_df["stepRedundancyCount"].apply(lambda x: min(x) == 2)
    ].shape[0]
    moderateFlexibleChains = summary_df[
        summary_df["stepRedundancyCount"].apply(lambda x: min(x) == 3)
    ].shape[0]
    strongFlexibleChains = summary_df[
        summary_df["stepRedundancyCount"].apply(lambda x: min(x) >= 4)
    ].shape[0]

    return (
        bottleneckChains,
        weakFlexibleChains,
        moderateFlexibleChains,
        strongFlexibleChains,
    )


# Add new columns combinedStepName, i.e. initialStateName_finalStateName, and stepRedundancyCount, i.e. total occurrences of combinedStateName in df
def augment_df(df):
    df.loc[:, "combinedStepName"] = (
        df["name"] + "_" + df["plans.actions.finalStateId.name"]
    )
    stepCounts = df["combinedStepName"].value_counts()
    stepCountSeries = []
    for stepName in df["combinedStepName"]:
        stepCountSeries.append(int(stepCounts[stepName]))
    df.loc[:, "stepRedundancyCount"] = stepCountSeries
    return df


def process_output_csv(input_csv_paths, output_path, scenarios_data_path, nw_sizes):
    # Load the flattened planner outputs for all 18 scenarios as csv
    csv_paths = input_csv_paths
    csv_paths = list(csv_paths.rglob("*.csv"))
    csv_paths.sort()

    # COUNT_BY_VC = False  # Flag to compute redundacy anad flexibility based on value chain (cluster) count or plans (value chain alternatives) count
    scenarios = []
    total_plans = []

    totalValueChainCounts = []

    totalBottleneckPercentage = []
    totalSingleReplPercentage = []
    totalDoubleReplPercentage = []
    totalMultiReplPercentage = []
    avgCost = []
    minPlanValue = []
    maxPlanValue = []

    # loop through each output file
    for csv_path in csv_paths:
        scenario_id = csv_path.stem.split("_")[-1]
        # print(scenario_name)

        df = pd.read_csv(csv_path)

        if int(df["totalPlans"].iloc[0]) == 0:
            scenarios.append(scenario_id)
            total_plans.append(int(df["totalPlans"].iloc[0]))

            totalBottleneckPercentage.append(0)
            totalSingleReplPercentage.append(0)
            totalDoubleReplPercentage.append(0)
            totalMultiReplPercentage.append(0)
            totalValueChainCounts.append(0)
            avgCost.append(0)
            minPlanValue.append(0)
            maxPlanValue.append(0)
            continue

        df = augment_df(df)

        df_view = df[
            [
                "numberOfPlans",
                "totalPlans",
                "plans.planId",
                "plans.planValue",
                "combinedStepName",
                "stepRedundancyCount",
                "name",
                "isStartState",
                "plans.actions.finalStateId.name",
                "plans.actions.finalStateId.isFinalState",
                "plans.actions.costs",
                "plans.actions.producerId.name",
                "plans.actions.producerId.trade",
                "plans.actions.producerId.enterprise",
                "minimumPlan",
                "maximumPlan",
            ]
        ]

        scenarios.append(scenario_id)
        total_plans.append(int(df_view["totalPlans"].iloc[0]))
        minPlanValue.append(int(df_view["minimumPlan"].iloc[0]))
        maxPlanValue.append(int(df_view["maximumPlan"].iloc[0]))
        summarize_df = summarize_plans(df_view)
        (output_path / "summarized_planner_outputs").mkdir(parents=False, exist_ok=True)
        summarize_df.to_csv(
            output_path / "summarized_planner_outputs" / f"{scenario_id}.csv",
            index=False,
        )  # save summarize df data for debugging
        if COUNT_BY_VC:
            (
                bottleneckChains,
                weakFlexibleChains,
                moderateFlexibleChains,
                strongFlexibleChains,
            ) = get_flexibile_vc_counts(summarize_df)
        else:
            (
                bottleneckChains,
                weakFlexibleChains,
                moderateFlexibleChains,
                strongFlexibleChains,
            ) = get_flexible_alternative_vc_counts(summarize_df)
        totalBottleneckPercentage.append(bottleneckChains)
        totalSingleReplPercentage.append(weakFlexibleChains)
        totalDoubleReplPercentage.append(moderateFlexibleChains)
        totalMultiReplPercentage.append(strongFlexibleChains)
        if COUNT_BY_VC:
            totalValueChainCounts.append(summarize_df["valueChainsCount"].iloc[0])
        else:
            totalValueChainCounts.append(int(df_view["totalPlans"].iloc[0]))
        avgCost.append(summarize_df["totalCost"].mean().round(2))

    # Create new results_df consolidating data required for creating plots
    results_df = pd.DataFrame(
        columns=[
            "scenario_id",
            "TotalPlans",
            "ValueChainCounts",
            "BottleneckValueChainCounts",
            "WeakValueChainCounts",
            "ModerateValueChainCounts",
            "StrongValueChainCounts",
            "avgPlanCost",
            "minPlanCost",
            "maxPlanCost",
        ]
    )
    results_df["scenario_id"] = scenarios
    results_df["TotalPlans"] = total_plans
    if COUNT_BY_VC:
        results_df["ValueChainCounts"] = totalValueChainCounts
    else:
        results_df["ValueChainCounts"] = total_plans
    results_df["BottleneckValueChainCounts"] = totalBottleneckPercentage
    results_df["WeakValueChainCounts"] = totalSingleReplPercentage
    results_df["ModerateValueChainCounts"] = totalDoubleReplPercentage
    results_df["StrongValueChainCounts"] = totalMultiReplPercentage
    results_df["avgPlanCost"] = avgCost
    results_df["minPlanCost"] = minPlanValue
    results_df["maxPlanCost"] = maxPlanValue
    results_df["avgPlanCostMod"] = (
        results_df["avgPlanCost"]
        + (0.2 * (results_df["maxPlanCost"] - results_df["minPlanCost"]))
    ).astype(int)
    # sort results_df by scenarios essentially sorting by production network size, used for grouping in next step
    results_df = results_df.sort_values("scenario_id")
    # merge scenarios data with analysis results
    scenarios_df = pd.read_csv(scenarios_data_path)
    results_df = pd.merge(scenarios_df, results_df, on="scenario_id", how="outer")

    results_df.to_csv(
        output_path / "resilience_analysis_data.csv", encoding="utf-8", index=False
    )
    return results_df  # exclude mean of avgCosts


def show_value_chain_count(dfs, output_path):
    # Set desired figure size (width, height)
    fig, ax = plt.subplots(figsize=(15, 8))

    # Bar plot show casing value chain redundancy
    dfs.plot.bar(
        x="x_label",
        y="ValueChainCounts",
        stacked=False,
        ax=ax,
    )

    # Set y-axis label and rotate xticks by 45 degrees
    ax.set_ylabel("Number of value chains")
    ax.set_xlabel("Scenarios")
    legend = ax.get_legend()
    legend.get_texts()[0].set_text("Value chain count")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path / "value_chain_count_barchart.png")


def show_value_chain_flexibility(dfs, output_path):
    # Set desired figure size (width, height)
    fig, ax = plt.subplots(figsize=(15, 8))

    # Bar plot show casing flexibility
    colors = ["red", "orange", "yellow", "green"]
    dfs.plot.bar(
        x="x_label",
        y=[
            "BottleneckValueChainCounts",
            "WeakValueChainCounts",
            "ModerateValueChainCounts",
            "StrongValueChainCounts",
        ],
        stacked=True,
        ax=ax,
        color=colors,
        alpha=0.7,
    )

    # Rename legend labels
    legend = ax.get_legend()
    legend.get_texts()[0].set_text("Bottleneck Chain")
    legend.get_texts()[1].set_text("Weak Flexiblity Chain")
    legend.get_texts()[2].set_text("Moderate Flexiblity Chain")
    legend.get_texts()[3].set_text("High Flexiblity Chain")

    # Set y-axis label and rotate xticks by 45 degrees
    ax.set_ylabel("Number of value chains")
    ax.set_xlabel("Scenarios")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path / "value_chain_flexibility_barchart.png")


def show_value_chain_flexibility_with_broken_axis(dfs, output_path):
    # Set desired figure size (width, height)
    fig, axs = plt.subplots(
        2, 1, figsize=(15, 8), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
    )

    colors = ["red", "orange", "yellow", "green"]

    # Create an upper bar plot showcasing number of plans above broken y-axis
    dfs.plot.bar(
        x="x_label",
        y=[
            "BottleneckValueChainCounts",
            "WeakValueChainCounts",
            "ModerateValueChainCounts",
            "StrongValueChainCounts",
        ],
        stacked=True,
        ax=axs[0],  # Assign the subplot axis
        color=colors,
        alpha=0.7,
    )

    # Create an upper bar plot showcasing number of plans below broken y-axis
    dfs.plot.bar(
        x="x_label",
        y=[
            "BottleneckValueChainCounts",
            "WeakValueChainCounts",
            "ModerateValueChainCounts",
            "StrongValueChainCounts",
        ],
        stacked=True,
        ax=axs[1],  # Assign the subplot axis
        color=colors,
        alpha=0.7,
    )

    # Break point of y-axis
    if COUNT_BY_VC:
        break_point = 10
    else:
        break_point = 15
    axs[0].set_ylim(
        break_point, axs[0].get_ylim()[1]
    )  # Upper limit is automatically set
    axs[1].set_ylim(0, break_point)

    # Remove spines and ticks from the top subplot's bottom and the bottom subplot's top
    for spine in ["bottom"]:
        axs[0].spines[spine].set_visible(False)
    axs[0].tick_params(axis="x", which="both", length=0)
    for spine in ["top"]:
        axs[1].spines[spine].set_visible(False)

    # Set labels, label fontsize and rotate xtikcs by 45 degrees
    plt.xticks(rotation=45)
    axs[0].tick_params(axis="both", labelsize=14)
    axs[0].set_ylabel("Number of value chains", fontsize=14)

    axs[1].tick_params(axis="both", labelsize=14)
    axs[1].set_xlabel("Scenarios", fontsize=14)
    axs[1].set_xticklabels(axs[1].get_xticklabels(), rotation=45, ha="right")
    d = 0.5  # proportion of vertical to horizontal extent of the slanted line
    kwargs = dict(
        marker=[(-1, -d), (1, d)],
        markersize=12,
        linestyle="none",
        color="k",
        mec="k",
        mew=1,
        clip_on=False,
    )
    axs[0].plot([0, 1], [0, 0], transform=axs[0].transAxes, **kwargs)
    axs[0].legend(fontsize=14)

    # Rename legend labels
    legend = axs[0].get_legend()
    legend.get_texts()[0].set_text("Bottleneck Chain")
    legend.get_texts()[1].set_text("Weak Flexiblity Chain")
    legend.get_texts()[2].set_text("Moderate Flexiblity Chain")
    legend.get_texts()[3].set_text("High Flexiblity Chain")

    axs[1].plot([0, 1], [1, 1], transform=axs[1].transAxes, **kwargs)

    # remove plot legend from lower subplot
    axs[1].get_legend().remove()

    plt.tight_layout()
    plt.savefig(output_path / "value_chain_flexibility_barchart_brokenaxis.png")


def generate_analysis(test_id, nw_sizes):
    output_path = DATA_PATH / test_id / "analysis_outputs"
    output_path.mkdir(parents=False, exist_ok=True)
    input_csv_paths = DATA_PATH / test_id / "planner_outputs" / "csv"
    scenarios_data_path = (
        DATA_PATH / test_id / "generated_vc_scenarios" / "scenarios_data.csv"
    )
    dfs = process_output_csv(
        input_csv_paths, output_path, scenarios_data_path, nw_sizes
    )
    dfs["x_label"] = dfs["scenario_name"] + " (" + dfs["scenario_id"] + ")"
    show_value_chain_count(dfs, output_path)
    show_value_chain_flexibility(dfs, output_path)
    show_value_chain_flexibility_with_broken_axis(dfs, output_path)
    print(">> Successfully saved analysis output data and plots.")
