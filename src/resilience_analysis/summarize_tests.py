import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from src.utils.paths import DATA_PATH


def show_summary_plot():
    csv_data_files = sorted(
        DATA_PATH.rglob("resilience_analysis_data.csv"), reverse=True
    )
    dfs = []
    for i, data_file in enumerate(csv_data_files):
        df = pd.read_csv(data_file)
        df = df[["scenario_id", "scenario_name", "ValueChainCounts"]].copy()
        df["source"] = data_file.parents[1].stem
        if i == 0:
            df["x_label"] = df["scenario_name"] + " (" + df["scenario_id"] + ")"
        else:
            df["x_label"] = dfs[0]["scenario_name"] + " (" + dfs[0]["scenario_id"] + ")"
        dfs.append(df)
    data = pd.concat(dfs)
    results_summary = pd.concat(
        [d.add_suffix(f"_{d['source'].iloc[0]}") for d in dfs],
        axis=1,
        join="outer",
    )
    results_summary = results_summary[
        [
            "scenario_id_no_filters",
            "scenario_name_no_filters",
            "ValueChainCounts_no_filters",
            "ValueChainCounts_filter_producer_limit",
            "ValueChainCounts_filter_producer_cost_limit",
        ]
    ]
    results_summary.to_csv(DATA_PATH / "results_summary.csv", index=False)
    plt.figure(figsize=(10, 5))
    sns.lineplot(
        data=data,
        x="x_label",
        y="ValueChainCounts",
        hue="source",
        style="source",
        markers=True,
        dashes=True,
        alpha=1,
    )
    plt.ylabel("Number of value chains")
    plt.xlabel("Scenarios")  # rename x_label back to Scenarios
    plt.grid(True, linestyle="-", alpha=0.4)
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(DATA_PATH / "summary_plot.png", bbox_inches="tight")
    print(">> Successfully saved summary plot.")


# python -m src.resilience_analysis.summarize_tests
