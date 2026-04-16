# main.py

from workloads import make_balanced_workload, make_database_workload, make_web_workload, make_ml_workload
from simulator import run_simulation
from fifo import FIFO
from round_robin import RoundRobin
from mlfq import MLFQ
from linux_cfs import LinuxCFS


def run_workload(workload_name, jobs):
    schedulers = [
        FIFO(),
        RoundRobin(),
        MLFQ(quanta=(1, 2, 4), boost_interval=10),
        LinuxCFS(),
    ]

    print("-----------------")
    print(f"WORKLOAD: {workload_name}")
    print("-----------------")


    for scheduler in schedulers:
        print("\n")
        print("**********************")
        print(f"Scheduler: {scheduler.name}")
        print("**********************")

        results = run_simulation(jobs, scheduler, verbose=False)

        for key, value in results.items():
            print(f"{key}: {value}")


def main():
    run_workload("Balanced", make_balanced_workload())
    run_workload("Database", make_database_workload())
    run_workload("Web", make_web_workload())
    run_workload("ML", make_ml_workload())

if __name__ == "__main__":
    main()