from workloads import make_balanced_workload, fifo_solos
from schedulers import fifo, shortest_job_first, value_first, fragile_aware
from simulator import run_simulation_loop


def main():
    jobs = fifo_solos()

    schedulers = {
        "FIFO": fifo,
        "Shortest Job First": shortest_job_first,
        "Value First": value_first,
        "Fragile Aware": fragile_aware,
    }

    for name, scheduler in schedulers.items():
        print("\n" + "=" * 50)
        print(f"Running scheduler: {name}")
        print("=" * 50)

        results = run_simulation_loop(jobs, scheduler, verbose=True)

        print("\nResults:")
        for key, value in results.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()