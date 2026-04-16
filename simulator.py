from metrics import compute_results

# initialize 
def prepare_jobs(jobs):
    sim_jobs = []
    for job in jobs:
        sim_jobs.append({
            "id": job["id"],
            "arrival": job["arrival"],
            "work": job["work"],
            "remaining_work": job["work"],
            "importance": job["importance"],
            "effective_importance": job["importance"],
            "fragility": job["fragility"],
            "preemption_cost": job.get("preemption_cost", 0),
            "completion_time": None,
            "interruptions": 0,
            "preemption_cost_incurred": 0,
            "service_received": 0,
            "vruntime": 0.0,
            "weight": 1024,   # Linux-like default nice weight
        })
    return sim_jobs


def run_simulation(jobs, scheduler, verbose=True):
    sim_jobs = prepare_jobs(jobs)

    time_step = 0
    current_job = None
    total_interruptions = 0
    total_value_lost = 0
    total_preemption_cost = 0
    seen_arrivals = set()

    while True:
        # create arrays for unfinished and available jobs
        unfinished_jobs = [job for job in sim_jobs if job["remaining_work"] > 0]
        if not unfinished_jobs:
            break
        available_jobs = [
            job for job in sim_jobs
            if job["arrival"] <= time_step and job["remaining_work"] > 0
        ]

        # notify scheduler of new arrivals
        for job in available_jobs:
            if job["id"] not in seen_arrivals:
                scheduler.job_arrival(job, time_step)
                seen_arrivals.add(job["id"])

        if not available_jobs:
            if verbose:
                print(f"t={time_step}: idle")
            time_step += 1
            continue

        next_job = scheduler.select_job(available_jobs, current_job, time_step)

        if next_job is None:
            if verbose:
                print(f"t={time_step}: idle")
            time_step += 1
            continue

        # preemption 
        if current_job is not None and current_job["id"] != next_job["id"] and current_job["remaining_work"] > 0:
            current_job["interruptions"] += 1
            total_interruptions += 1

            # Apply fragility penalty to value
            fragility_penalty = min(current_job["fragility"], current_job["effective_importance"])
            current_job["effective_importance"] -= fragility_penalty
            total_value_lost += fragility_penalty

            # Apply preemption cost
            preemption_penalty = current_job["preemption_cost"]
            current_job["preemption_cost_incurred"] += preemption_penalty
            total_preemption_cost += preemption_penalty

            scheduler.job_preempted(current_job, time_step)

            if verbose:
                print(f"t={time_step}: interrupted {current_job['id']}, fragility penalty={fragility_penalty}, preemption cost={preemption_penalty}")

        current_job = next_job

        # run a timestep
        current_job["remaining_work"] -= 1
        current_job["service_received"] += 1
        scheduler.during_job_run(current_job, time_step)

        if verbose:
            print(
                f"t={time_step}: running {current_job['id']} "
                f"(remaining={current_job['remaining_work']})"
            )

        if current_job["remaining_work"] == 0:
            current_job["completion_time"] = time_step + 1
            scheduler.job_finish(current_job, time_step)
            if verbose:
                print(
                    f"t={time_step}: completed {current_job['id']} "
                    f"with value {current_job['effective_importance']}"
                )
            current_job = None

        time_step += 1

    return compute_results(sim_jobs, total_interruptions, total_value_lost, total_preemption_cost, time_step)