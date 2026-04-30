import copy
import json
import random

from simulator import run_simulation

from fifo import FIFO
from round_robin import RoundRobin
from mlfq import MLFQ
from linux_cfs import LinuxCFS

from workloads import (
    make_database_workload,
    make_web_workload,
    make_ml_workload,
)

from work_stealing_strategies import (
    NoStealing,
    AlwaysStealing,
)

# random load distributor experiment to see if stealing helps after random initial placement
def run_random_distribution_experiment(
    workload_name,
    jobs,
    scheduler_classes,
    stealing_strategies,
    num_workers=4,
    num_trials=5,
    lambda_param=1.0,
    seed=0,
):
    rows = []

    print(f"\n{'=' * 90}")
    print(f"WORKLOAD: {workload_name}")
    print(f"{'=' * 90}")

    for trial in range(num_trials):
        trial_seed = seed + trial
        random.seed(trial_seed)

        for scheduler_name, SchedulerClass in scheduler_classes.items():
            for stealing_name, stealing_strategy in stealing_strategies.items():
                schedulers = [SchedulerClass() for _ in range(num_workers)]

                results = run_simulation(
                    copy.deepcopy(jobs),
                    schedulers,
                    verbose=False,
                    num_workers=num_workers,
                    job_distribution="random",
                    work_stealing_strategy=stealing_strategy,
                    lambda_param=lambda_param,
                )

                row = {
                    "workload": workload_name,
                    "scheduler": scheduler_name,
                    "stealing": stealing_name,
                    "trial": trial,
                    "seed": trial_seed,
                    "total_time": results["total_time"],
                    "value": results["value_completed"],
                    "jobs_completed": results["jobs_completed"],
                    "steals": results["total_steals"],
                    "migration_cost": results["total_migration_cost"],
                    "interruptions": results["total_interruptions"],
                    "value_lost": results["total_value_lost"],
                }

                rows.append(row)

    return rows

# take all the metrics and get summary table
def summarize_rows(rows):
    grouped = {}

    for row in rows:
        key = (row["workload"], row["scheduler"], row["stealing"])
        grouped.setdefault(key, []).append(row)

    summary = []

    for (workload, scheduler, stealing), group in grouped.items():
        n = len(group)

        summary.append({
            "workload": workload,
            "scheduler": scheduler,
            "stealing": stealing,
            "trials": n,
            "avg_total_time": sum(r["total_time"] for r in group) / n,
            "min_total_time": min(r["total_time"] for r in group),
            "max_total_time": max(r["total_time"] for r in group),
            "avg_value": sum(r["value"] for r in group) / n,
            "avg_steals": sum(r["steals"] for r in group) / n,
            "avg_migration_cost": sum(r["migration_cost"] for r in group) / n,
        })

    return summary


def print_table(rows, columns):
    if not rows:
        print("No rows to print.")
        return

    def fmt(x):
        if isinstance(x, float):
            return f"{x:.2f}"
        return str(x)

    widths = {
        col: max(len(col), max(len(fmt(row.get(col, ""))) for row in rows))
        for col in columns
    }

    print("  ".join(col.rjust(widths[col]) for col in columns))
    print("  ".join("-" * widths[col] for col in columns))

    for row in rows:
        print("  ".join(fmt(row.get(col, "")).rjust(widths[col]) for col in columns))


def main():
    num_workers = 4
    num_trials = 5
    lambda_param = 1.0
    seed = 42

    scheduler_classes = {
        "FIFO": FIFO,

        "Round Robin": RoundRobin,
        "MLFQ": MLFQ,
        "Linux CFS": LinuxCFS,
    }

    stealing_strategies = {
        "No Stealing": NoStealing(),
        "Always Stealing": AlwaysStealing(),
    }

    workloads = [
        ("Database", make_database_workload()),
        ("Web", make_web_workload()),
        ("ML", make_ml_workload()),
    ]

    all_rows = []

    for workload_name, jobs in workloads:
        rows = run_random_distribution_experiment(
            workload_name=workload_name,
            jobs=jobs,
            scheduler_classes=scheduler_classes,
            stealing_strategies=stealing_strategies,
            num_workers=num_workers,
            num_trials=num_trials,
            lambda_param=lambda_param,
            seed=seed,
        )
        all_rows.extend(rows)

    print("\n" + "=" * 90)
    print("FULL RESULTS: RANDOM DISTRIBUTION")
    print("=" * 90)

    full_columns = [
        "workload",
        "scheduler",
        "stealing",
        "trial",
        "seed",
        "total_time",
        "value",
        "steals",
        "migration_cost",
    ]
    print_table(all_rows, full_columns)

    summary_rows = summarize_rows(all_rows)

    print("\n" + "=" * 90)
    print("SUMMARY: AVERAGE OVERALL TIME ACROSS RANDOM TRIALS")
    print("=" * 90)

    summary_columns = [
        "workload",
        "scheduler",
        "stealing",
        "trials",
        "avg_total_time",
        "min_total_time",
        "max_total_time",
        "avg_value",
        "avg_steals",
        "avg_migration_cost",
    ]
    print_table(summary_rows, summary_columns)

    output_file = "random_distribution_stealing_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "full_results": all_rows,
            "summary": summary_rows,
        }, f, indent=2, default=str)

    print(f"\nResults saved to: {output_file}")
if __name__ == "__main__":
    main()
