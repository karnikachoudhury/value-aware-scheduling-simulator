import copy
import json
import matplotlib.pyplot as plt

from workloads import (
    make_database_workload,
    make_web_workload,
    make_ml_workload,
)
from simulator import run_simulation
from fifo import FIFO
from work_stealing_strategies import NoStealing, AlwaysStealing, CostAwareStealing


STRATEGIES = {
    "No Stealing": NoStealing,
    "Always Stealing": AlwaysStealing,
    "Cost-Aware Stealing": CostAwareStealing,
}

COLORS = {
    "No Stealing": "blue",
    "Always Stealing": "red",
    "Cost-Aware Stealing": "green",
}


# run simulation acorss time stamps to see metrics
def run_fixed_cost_time_series_experiment(
    workload_name,
    jobs,
    num_workers=4,
    lambda_param=1.0,
    job_distribution="one",
):
    """
    Run one workload with its built-in migration_cost values.
    Does not overwrite migration_cost.
    """
    print(f"\n{'=' * 70}")
    print(f"TIME-SERIES WORKLOAD: {workload_name}")
    print(f"{'=' * 70}")

    workload_results = {}

    for strategy_name, strategy_cls in STRATEGIES.items():
        schedulers = [FIFO() for _ in range(num_workers)]
        strategy = strategy_cls()

        sim_results = run_simulation(
            copy.deepcopy(jobs),
            schedulers,
            verbose=False,
            num_workers=num_workers,
            job_distribution=job_distribution,
            work_stealing_strategy=strategy,
            lambda_param=lambda_param,
        )

        workload_results[strategy_name] = sim_results

        print(
            f"{strategy_name:22s} | "
            f"value={sim_results['value_completed']:6.1f} | "
            f"steals={sim_results['total_steals']:3d} | "
            f"migration_cost={sim_results['total_migration_cost']:6.1f} | "
            f"time={sim_results['total_time']:4d} | "
            f"avg_psi={sim_results.get('avg_cost_aware_potential', 0):8.2f}"
        )

    return workload_results


# get completed value from results
def reconstruct_completed_value_over_time(result):
    total_time = result.get("total_time", 0)

    completed_jobs = (
        result.get("completed_jobs")
        or result.get("all_completed")
        or result.get("jobs")
        or []
    )

    values_by_time = [0 for _ in range(total_time + 1)]

    if completed_jobs:
        for job in completed_jobs:
            completion_time = job.get("completion_time")
            if completion_time is None:
                continue

            value = job.get("effective_importance", job.get("importance", 0))

            t = min(max(int(completion_time), 0), total_time)
            values_by_time[t] += value

        cumulative = []
        running = 0
        for t in range(total_time + 1):
            running += values_by_time[t]
            cumulative.append(running)

        return list(range(total_time + 1)), cumulative

    return [0, total_time], [0, result.get("value_completed", 0)]


# organize and return time stamp results
def get_timeline(result):
    log = result.get("potential_log", [])

    times = [row["time"] for row in log]
    remaining_work = [sum(row.get("loads", [])) for row in log]
    psi = [row.get("psi", row.get("phi", 0)) for row in log]

    value_time, completed_value = reconstruct_completed_value_over_time(result)

    return {
        "time": times,
        "remaining_work": remaining_work,
        "psi": psi,
        "value_time": value_time,
        "completed_value": completed_value,
    }


# fix y limit should not vary
def safe_set_ylim(ax, all_values):
    if not all_values:
        return

    min_val = min(all_values)
    max_val = max(all_values)

    if min_val == max_val:
        if max_val == 0:
            ax.set_ylim(0, 1)
        else:
            ax.set_ylim(0, max_val * 1.1)
        return

    pad = 0.08 * (max_val - min_val)
    lower = min(0, min_val - pad)
    upper = max_val + pad
    ax.set_ylim(lower, upper)

# plot across time stamps
def plot_time_series(all_results, output_file="work_stealing_value_time_series.png"):
    workloads = list(all_results.keys())
    num_workloads = len(workloads)

    metric_specs = [
        ("completed_value", "Completed Value", "Cumulative completed value"),
        ("remaining_work", "Remaining Work", "Total remaining work"),
        ("psi", "Cost-Aware Potential", "Psi = Phi + lambda C"),
    ]

    fig, axes = plt.subplots(
        num_workloads,
        len(metric_specs),
        figsize=(16, 4.2 * num_workloads),
        constrained_layout=True,
    )

    if num_workloads == 1:
        axes = axes.reshape(1, -1)

    for row_idx, workload_name in enumerate(workloads):
        workload_results = all_results[workload_name]

        timelines = {
            strategy_name: get_timeline(result)
            for strategy_name, result in workload_results.items()
        }

        for col_idx, (metric_key, metric_title, y_label) in enumerate(metric_specs):
            ax = axes[row_idx, col_idx]

            all_values = []

            for strategy_name in STRATEGIES.keys():
                timeline = timelines[strategy_name]

                if metric_key == "completed_value":
                    x = timeline["value_time"]
                    y = timeline["completed_value"]
                else:
                    x = timeline["time"]
                    y = timeline[metric_key]

                all_values.extend(y)

                ax.plot(
                    x,
                    y,
                    label=strategy_name,
                    color=COLORS[strategy_name],
                    linewidth=2,
                )

            ax.set_title(f"{workload_name}\n{metric_title}", fontsize=11, pad=8)
            ax.set_xlabel("Time step")
            ax.set_ylabel(y_label)
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8, loc="best")
            safe_set_ylim(ax, all_values)

    fig.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved to: {output_file}")
    plt.show()


def save_results(all_results, output_file="work_stealing_value_time_series_results.json"):
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"Results saved to: {output_file}")


def main():
    num_workers = 4
    lambda_param = 1.0

    job_distribution = "one"

    workloads = [
        ("Database", make_database_workload()),
        ("Web", make_web_workload()),
        # ("ML", make_ml_workload()),
    ]

    all_results = {}

    for workload_name, jobs in workloads:
        all_results[workload_name] = run_fixed_cost_time_series_experiment(
            workload_name=workload_name,
            jobs=jobs,
            num_workers=num_workers,
            lambda_param=lambda_param,
            job_distribution=job_distribution,
        )

    save_results(all_results)
    plot_time_series(all_results)

    print("\n" + "=" * 70)
    print("TIME-SERIES EXPERIMENT SUMMARY")
    print("=" * 70)

if __name__ == "__main__":
    main()
