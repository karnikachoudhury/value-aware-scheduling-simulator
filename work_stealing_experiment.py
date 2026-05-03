import json
import matplotlib.pyplot as plt

from workloads import (
    make_balanced_workload, make_database_workload,
    make_web_workload, make_ml_workload,
    make_fork_join_workload, make_bursty_workload, make_skewed_importance_workload,
    make_always_stealing_wins_workload, make_cost_aware_wins_workload
)
from simulator import run_simulation
from fifo import FIFO
from work_stealing_strategies import NoStealing, AlwaysStealing, CostAwareStealing


# for decision table printing
def print_cost_aware_decision_table(sim_results):
    summary = sim_results.get("decision_summary")
    if not summary:
        print("    No decision summary found.")
        return

    print(
        f"    Decision Table: "
        f"opp={summary['opportunities']:3d}  "
        f"accepted={summary['accepted']:3d}  "
        f"rejected={summary['rejected']:3d}  "
        f"bad_accepts={summary['bad_accepts']:3d}  "
        f"bad_rejects={summary['bad_rejects']:3d}  "
        f"avg_benefit={summary['avg_benefit']:8.2f}  "
        f"avg_cost={summary['avg_cost']:8.2f}  "
        f"avg_margin={summary['avg_margin']:8.2f}  "
        f"accept_rate={summary['accept_rate']:.2f}"
    )


# run experiment with varying migration costs and strategies and summarize results
def run_experiment(workload_name, jobs, migration_costs, num_workers=4, lambda_param=1.0):
    strategies = {
        "No Stealing": NoStealing(),
        "Always Stealing": AlwaysStealing(),
        "Cost-Aware Stealing": CostAwareStealing(),
    }

    results = {strategy_name: [] for strategy_name in strategies.keys()}

    print(f"\n{'=' * 70}")
    print(f"WORKLOAD: {workload_name}")
    print(f"{'=' * 70}\n")

    for migration_cost in migration_costs:
        print(f"Migration Cost: {migration_cost}")
        print("-" * 50)

        for job in jobs:
            job["migration_cost"] = migration_cost

        for strategy_name, strategy in strategies.items():
            schedulers = [FIFO() for _ in range(num_workers)]

            sim_results = run_simulation(
                jobs,
                schedulers,
                verbose=True,
                num_workers=num_workers,
                job_distribution="one",
                work_stealing_strategy=strategy,
                lambda_param=lambda_param,
            )

            results[strategy_name].append(sim_results)

            print(
                f"  {strategy_name:20s} - "
                f"Value: {sim_results['value_completed']:6.0f}  "
                f"Steals: {sim_results['total_steals']:3d}  "
                f"Cost: {sim_results['total_migration_cost']:6.0f}  "
                f"Time: {sim_results['total_time']:4d}"
            )

            if strategy_name == "Cost-Aware Stealing":
                print_cost_aware_decision_table(sim_results)

        print()

    return results


# shorten long workload names so stop overlapping on plots
def short_workload_name(name):
    replacements = {
        "Small Workload Jobs, All at Once": "Small Jobs\nAll at Once",
        "Large Workload Jobs, Periodic": "Large Jobs\nPeriodic",
    }
    return replacements.get(name, name.replace(", ", "\n"))


# matplotlib plotting code
def plot_results(all_results, migration_costs, output_file="work_stealing_experiment.png"):
    strategies = ["No Stealing", "Always Stealing", "Cost-Aware Stealing"]
    colors = {
        "No Stealing": "blue",
        "Always Stealing": "red",
        "Cost-Aware Stealing": "green",
    }

    workloads = list(all_results.keys())
    num_workloads = len(workloads)

    num_cols = 3
    fig, axes = plt.subplots(
        num_workloads,
        num_cols,
        figsize=(18, 4.2 * num_workloads),
        constrained_layout=True,
    )

    if num_workloads == 1:
        axes = axes.reshape(1, -1)

    global_value = []
    global_makespan = []
    global_potential = []

    for workload_results in all_results.values():
        for strategy_name in strategies:
            for result in workload_results[strategy_name]:
                global_value.append(result["value_completed"])
                global_makespan.append(result["total_time"])
                global_potential.append(result.get("avg_normalized_cost_aware_potential", result.get("avg_potential", 0)))

    def safe_ylim(values, allow_negative=False):
        if not values:
            return (0, 1)

        min_val = min(values)
        max_val = max(values)

        if allow_negative and min_val < 0:
            pad = 0.08 * (max_val - min_val if max_val != min_val else 1)
            return (min_val - pad, max_val + pad)

        if max_val <= 0:
            return (0, 1)

        return (0, max_val * 1.08)

    metric_specs = [
        {
            "key": "value_completed",
            "title": "Value",
            "ylabel": "Total Value Completed",
            "ylim": safe_ylim(global_value, allow_negative=True),
        },
        {
            "key": "total_time",
            "title": "Makespan",
            "ylabel": "Total Time",
            "ylim": safe_ylim(global_makespan),
        },
        {
            "key": "avg_normalized_cost_aware_potential",
            "fallback_key": "avg_potential",
            "title": "Cost-Aware Potential",
            "ylabel": "Psi = Phi + lambda C",
            "ylim": safe_ylim(global_potential),
        },
    ]

    for workload_idx, workload_name in enumerate(workloads):
        workload_results = all_results[workload_name]
        pretty_name = short_workload_name(workload_name)

        for col_idx, spec in enumerate(metric_specs):
            ax = axes[workload_idx, col_idx]

            for strategy in strategies:
                values = []
                for result in workload_results[strategy]:
                    if spec["key"] in result:
                        values.append(result[spec["key"]])
                    else:
                        values.append(result.get(spec.get("fallback_key", ""), 0))

                ax.plot(
                    migration_costs,
                    values,
                    marker="o",
                    label=strategy,
                    color=colors[strategy],
                    linewidth=2,
                )

            ax.set_xlabel("Migration Cost (c)")
            ax.set_ylabel(spec["ylabel"])
            ax.set_title(f"{pretty_name}\n{spec['title']}", fontsize=11, pad=8)
            ax.set_ylim(spec["ylim"])
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8, loc="best")

    fig.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved to: {output_file}")
    plt.show()


def main():
    migration_costs = [0, 10, 30, 50, 100, 200, 500, 1000, 2000, 4000]
    num_workers = 4
    lambda_param = 1.0

    workloads = [
        ("Small Workload Jobs, All at Once", make_always_stealing_wins_workload()),
        ("Large Workload Jobs, Periodic", make_cost_aware_wins_workload()),
    ]

    all_results = {}

    for workload_name, jobs in workloads:
        import copy
        jobs_copy = copy.deepcopy(jobs)

        results = run_experiment(
            workload_name,
            jobs_copy,
            migration_costs,
            num_workers=num_workers,
            lambda_param=lambda_param,
        )
        all_results[workload_name] = results

    output_file = "work_stealing_experiment_results.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")

    plot_results(all_results, migration_costs)

    print("\n" + "=" * 70)
    print("EXPERIMENT SUMMARY")
    print("=" * 70)


if __name__ == "__main__":
    main()
