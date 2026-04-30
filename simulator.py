from metrics import compute_results, compute_results_simple
from worker import Worker
from work_stealing_strategies import AlwaysStealing
import random


def compute_worker_load(worker):
    """Total worker load = queued work + currently running job."""
    queue_load = worker.get_queue_info()["total_work"]

    current_load = 0
    if worker.current_job is not None and worker.current_job["remaining_work"] > 0:
        current_load = worker.current_job["remaining_work"]

    return queue_load + current_load


def compute_imbalance_potential(workers):
    """Phi = sum_i (L_i - L_avg)^2."""
    loads = [compute_worker_load(w) for w in workers]
    if not loads:
        return 0

    avg_load = sum(loads) / len(loads)
    return sum((load - avg_load) ** 2 for load in loads)


def compute_normalized_phi(phi, total_initial_work):
    if total_initial_work <= 0:
        return 0
    return phi / (total_initial_work ** 2)


def compute_normalized_cost(total_migration_cost, total_possible_value):
    if total_possible_value <= 0:
        return 0
    return total_migration_cost / total_possible_value


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
            "migration_cost": job.get("migration_cost", 0),
            "completion_time": None,
            "interruptions": 0,
            "migration_cost_incurred": 0,
            "service_received": 0,
            "vruntime": 0.0,
            "weight": 1024,
            "worker_id": None,
        })
    return sim_jobs


def distribute_job(workers, job, strategy="random", time_step=0):
    """
    Assign a newly arrived job to a worker.

    Supported strategies:
      - "one" / "single_worker": all jobs go to worker 0
      - "round_robin": simple deterministic spreading
      - "power_of_two": sample two workers and choose less loaded
      - "random": random worker
    """
    if strategy == "round_robin":
        worker = workers[len(job["id"]) % len(workers)]

    elif strategy == "power_of_two":
        sample = random.sample(workers, min(2, len(workers)))
        worker = min(sample, key=lambda w: compute_worker_load(w))

    elif strategy == "random":
        worker = random.choice(workers)

    elif strategy in ("one", "single_worker"):
        worker = workers[0]

    else:
        worker = workers[0]

    job["worker_id"] = worker.worker_id
    worker.assign_job(job)
    return worker


def summarize_decision_log(decision_log):
    if not decision_log:
        return {
            "opportunities": 0,
            "accepted": 0,
            "rejected": 0,
            "bad_accepts": 0,
            "bad_rejects": 0,
            "avg_benefit": 0.0,
            "avg_cost": 0.0,
            "avg_margin": 0.0,
            "accept_rate": 0.0,
        }

    accepted = [d for d in decision_log if d["decision"]]
    rejected = [d for d in decision_log if not d["decision"]]
    bad_accepts = [d for d in decision_log if d["decision"] and d["margin"] <= 0]
    bad_rejects = [d for d in decision_log if (not d["decision"]) and d["margin"] > 0]

    n = len(decision_log)
    return {
        "opportunities": n,
        "accepted": len(accepted),
        "rejected": len(rejected),
        "bad_accepts": len(bad_accepts),
        "bad_rejects": len(bad_rejects),
        "avg_benefit": sum(d["benefit"] for d in decision_log) / n,
        "avg_cost": sum(d["cost"] for d in decision_log) / n,
        "avg_margin": sum(d["margin"] for d in decision_log) / n,
        "accept_rate": len(accepted) / n,
    }


def clean_completed_jobs_from_worker(worker):
    """Remove completed jobs from queue so they cannot run below zero."""
    worker.local_queue = [job for job in worker.local_queue if job["remaining_work"] > 0]
def run_simulation_simple(jobs, scheduler, verbose=True):
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

    return compute_results_simple(sim_jobs, total_interruptions, total_value_lost, total_preemption_cost, time_step)

def run_simulation(
    jobs,
    schedulers,
    verbose=True,
    num_workers=4,
    job_distribution="one",
    work_steal_threshold=0.3,
    work_stealing_strategy=None,
    lambda_param=1.0,
):
    """
    Run the scheduling simulation.

    job_distribution is intentionally exposed because the experiments depend on it.
    Common values:
      job_distribution="one"          # spawned/local imbalance case
      job_distribution="random"
      job_distribution="round_robin"
      job_distribution="power_of_two"
    """
    if work_stealing_strategy is None:
        work_stealing_strategy = AlwaysStealing()

    if len(schedulers) != num_workers:
        raise ValueError(f"Must provide {num_workers} schedulers for {num_workers} workers")

    sim_jobs = prepare_jobs(jobs)
    workers = [Worker(i, schedulers[i]) for i in range(num_workers)]

    total_initial_work = sum(job["work"] for job in sim_jobs)
    total_possible_value = sum(job["importance"] for job in sim_jobs)

    time_step = 0
    total_interruptions = 0
    total_value_lost = 0
    total_migration_cost = 0
    total_steals = 0
    decision_log = []
    potential_log = []
    timeline_log = []
    seen_arrivals = set()

    while True:
        unfinished_jobs = [job for job in sim_jobs if job["remaining_work"] > 0]
        if not unfinished_jobs:
            break

        arriving_jobs = [
            job for job in sim_jobs
            if job["arrival"] == time_step and job["id"] not in seen_arrivals
        ]

        for job in arriving_jobs:
            seen_arrivals.add(job["id"])
            distribute_job(
                workers,
                job,
                strategy=job_distribution,
                time_step=time_step,
            )

        for worker in workers:
            clean_completed_jobs_from_worker(worker)

            if worker.current_job is not None and worker.current_job["remaining_work"] <= 0:
                worker.current_job = None

            if worker.local_queue or worker.current_job is not None:
                next_job = worker.select_job(time_step)

                if next_job is None or next_job["remaining_work"] <= 0:
                    if next_job is not None and next_job in worker.local_queue:
                        worker.local_queue.remove(next_job)
                    if worker.current_job is not None and worker.current_job.get("remaining_work", 0) <= 0:
                        worker.current_job = None
                    continue

                if (
                    worker.current_job is not None
                    and worker.current_job["id"] != next_job["id"]
                    and worker.current_job["remaining_work"] > 0
                ):
                    current = worker.current_job
                    current["interruptions"] += 1
                    worker.interruptions += 1
                    total_interruptions += 1

                    fragility_penalty = min(current["fragility"], current["effective_importance"])
                    current["effective_importance"] -= fragility_penalty
                    worker.value_lost += fragility_penalty
                    total_value_lost += fragility_penalty

                    worker.scheduler.job_preempted(current, time_step)

                worker.current_job = next_job

                next_job["remaining_work"] -= 1
                next_job["service_received"] += 1
                worker.scheduler.during_job_run(next_job, time_step)

                if next_job["remaining_work"] == 0:
                    next_job["completion_time"] = time_step + 1
                    worker.scheduler.job_finish(next_job, time_step)
                    worker.completed_jobs.append(next_job)
                    worker.current_job = None

                    if next_job in worker.local_queue:
                        worker.local_queue.remove(next_job)

            clean_completed_jobs_from_worker(worker)

        # Work stealing.
        idle_workers = [w for w in workers if w.being_useless()]
        for idle_worker in idle_workers:
            non_idle_workers = [w for w in workers if w != idle_worker and not w.being_useless()]
            if not non_idle_workers:
                continue

            victim = max(non_idle_workers, key=lambda w: compute_worker_load(w))
            victim_info = victim.get_queue_info()

            stolen_job = victim_info["max_value_job"]
            if stolen_job is None or stolen_job.get("remaining_work", 0) <= 0:
                continue

            migration_cost = stolen_job["migration_cost"]

            victim_load_x = compute_worker_load(victim)
            steal_amount_s = stolen_job["remaining_work"]

            benefit = 2 * steal_amount_s * (victim_load_x - steal_amount_s)
            cost = lambda_param * migration_cost
            margin = benefit - cost

            normalized_benefit = compute_normalized_phi(benefit, total_initial_work)
            normalized_cost_for_this_steal = lambda_param * compute_normalized_cost(
                migration_cost,
                total_possible_value,
            )
            normalized_margin = normalized_benefit - normalized_cost_for_this_steal

            decision = work_stealing_strategy.should_steal(
                idle_worker,
                victim,
                stolen_job,
                migration_cost,
                time_step,
                lambda_param,
            )

            decision_log.append({
                "time": time_step,
                "idle_worker": idle_worker.worker_id,
                "victim_worker": victim.worker_id,
                "job_id": stolen_job["id"],
                "victim_load_x": victim_load_x,
                "steal_amount_s": steal_amount_s,
                "benefit": benefit,
                "cost": cost,
                "margin": margin,
                "normalized_benefit": normalized_benefit,
                "normalized_cost": normalized_cost_for_this_steal,
                "normalized_margin": normalized_margin,
                "decision": decision,
            })

            if decision:
                if victim.remove_job_from_queue(stolen_job):
                    migration_penalty = migration_cost
                    stolen_job["effective_importance"] -= migration_penalty
                    total_migration_cost += migration_penalty
                    stolen_job["migration_cost_incurred"] += migration_penalty

                    idle_worker.steal_job(stolen_job)
                    stolen_job["worker_id"] = idle_worker.worker_id
                    total_steals += 1

        phi = compute_imbalance_potential(workers)
        normalized_phi = compute_normalized_phi(phi, total_initial_work)
        normalized_total_cost = compute_normalized_cost(total_migration_cost, total_possible_value)

        avg_migration_cost_so_far = total_migration_cost / (time_step + 1)
        raw_psi = phi + lambda_param * avg_migration_cost_so_far
        normalized_psi = normalized_phi + lambda_param * normalized_total_cost

        completed_so_far = []
        for worker in workers:
            completed_so_far.extend(worker.completed_jobs)

        completed_value_so_far = sum(job["effective_importance"] for job in completed_so_far)
        jobs_completed_so_far = len(completed_so_far)
        remaining_work = sum(max(job["remaining_work"], 0) for job in sim_jobs)

        potential_entry = {
            "time": time_step,
            "phi": phi,
            "normalized_phi": normalized_phi,
            "migration_cost_so_far": total_migration_cost,
            "avg_migration_cost_per_time": avg_migration_cost_so_far,
            "normalized_cost": normalized_total_cost,
            "psi": raw_psi,
            "normalized_psi": normalized_psi,
            "loads": [compute_worker_load(w) for w in workers],
        }

        potential_log.append(potential_entry)
        timeline_log.append({
            **potential_entry,
            "completed_value": completed_value_so_far,
            "jobs_completed": jobs_completed_so_far,
            "remaining_work": remaining_work,
            "total_steals": total_steals,
        })

        time_step += 1

    all_completed = []
    for worker in workers:
        all_completed.extend(worker.completed_jobs)

    results = compute_results(
        all_completed,
        total_interruptions,
        total_value_lost,
        total_migration_cost,
        time_step,
        total_steals,
    )

    results["completed_jobs"] = all_completed
    results["decision_log"] = decision_log
    results["decision_summary"] = summarize_decision_log(decision_log)
    results["potential_log"] = potential_log
    results["timeline_log"] = timeline_log

    results["total_initial_work"] = total_initial_work
    results["total_possible_value"] = total_possible_value

    if potential_log:
        results["avg_potential"] = sum(p["phi"] for p in potential_log) / len(potential_log)
        results["max_potential"] = max(p["phi"] for p in potential_log)
        results["final_potential"] = potential_log[-1]["phi"]

        results["avg_normalized_potential"] = (
            sum(p["normalized_phi"] for p in potential_log) / len(potential_log)
        )
        results["max_normalized_potential"] = max(p["normalized_phi"] for p in potential_log)
        results["final_normalized_potential"] = potential_log[-1]["normalized_phi"]

        results["avg_migration_cost_per_time"] = (
            total_migration_cost / time_step if time_step > 0 else 0
        )
        results["normalized_cost"] = compute_normalized_cost(
            total_migration_cost,
            total_possible_value,
        )

        results["avg_cost_aware_potential"] = (
            results["avg_potential"]
            + lambda_param * results["avg_migration_cost_per_time"]
        )
        results["avg_timestep_cost_aware_potential"] = (
            sum(p["psi"] for p in potential_log) / len(potential_log)
        )

        results["avg_normalized_cost_aware_potential"] = (
            sum(p["normalized_psi"] for p in potential_log) / len(potential_log)
        )
        results["final_normalized_cost_aware_potential"] = potential_log[-1]["normalized_psi"]

    else:
        results["avg_potential"] = 0
        results["max_potential"] = 0
        results["final_potential"] = 0
        results["avg_normalized_potential"] = 0
        results["max_normalized_potential"] = 0
        results["final_normalized_potential"] = 0
        results["avg_migration_cost_per_time"] = 0
        results["normalized_cost"] = 0
        results["avg_cost_aware_potential"] = 0
        results["avg_timestep_cost_aware_potential"] = 0
        results["avg_normalized_cost_aware_potential"] = 0
        results["final_normalized_cost_aware_potential"] = 0

    return results


# from metrics import compute_results
# from worker import Worker
# from work_stealing_strategies import AlwaysStealing
# import random


# def compute_worker_load(worker):
#     """Total worker load = queued work + currently running job."""
#     queue_load = worker.get_queue_info()["total_work"]

#     current_load = 0
#     if worker.current_job is not None and worker.current_job["remaining_work"] > 0:
#         current_load = worker.current_job["remaining_work"]

#     return queue_load + current_load


# def compute_imbalance_potential(workers):
#     """Phi = sum_i (L_i - L_avg)^2."""
#     loads = [compute_worker_load(w) for w in workers]
#     if not loads:
#         return 0

#     avg_load = sum(loads) / len(loads)
#     return sum((load - avg_load) ** 2 for load in loads)


# def debug_print_loads(time_step, workers, label):
#     """Print worker load/running/queue state when verbose=True."""
#     loads = [compute_worker_load(w) for w in workers]
#     running = [
#         w.current_job["id"] if w.current_job is not None else None
#         for w in workers
#     ]
#     queues = [
#         [job["id"] for job in w.local_queue if job["remaining_work"] > 0]
#         for w in workers
#     ]
#     queue_remaining = [
#         [(job["id"], job["remaining_work"]) for job in w.local_queue if job["remaining_work"] > 0]
#         for w in workers
#     ]

#     print(f"\n[t={time_step}] {label}")
#     print(f"  loads:           {loads}")
#     print(f"  running:         {running}")
#     print(f"  queues:          {queues}")
#     print(f"  queue_remaining: {queue_remaining}")


# def prepare_jobs(jobs):
#     sim_jobs = []
#     for job in jobs:
#         sim_jobs.append({
#             "id": job["id"],
#             "arrival": job["arrival"],
#             "work": job["work"],
#             "remaining_work": job["work"],
#             "importance": job["importance"],
#             "effective_importance": job["importance"],
#             "fragility": job["fragility"],
#             "migration_cost": job.get("migration_cost", 0),
#             "completion_time": None,
#             "interruptions": 0,
#             "migration_cost_incurred": 0,
#             "service_received": 0,
#             "vruntime": 0.0,
#             "weight": 1024,
#             "worker_id": None,
#         })
#     return sim_jobs


# def distribute_job(workers, job, strategy, time_step=0):
#     if strategy == "round_robin":
#         worker = workers[len(job["id"]) % len(workers)]
#     elif strategy == "power_of_two":
#         sample = random.sample(workers, min(2, len(workers)))
#         worker = min(sample, key=lambda w: compute_worker_load(w))
#     elif strategy == "random":
#         worker = random.choice(workers)
#     elif strategy in ("one", "single_worker"):
#         worker = workers[0]
#     else:
#         worker = workers[0]

#     job["worker_id"] = worker.worker_id
#     worker.assign_job(job)
#     return worker


# def summarize_decision_log(decision_log):
#     if not decision_log:
#         return {
#             "opportunities": 0,
#             "accepted": 0,
#             "rejected": 0,
#             "bad_accepts": 0,
#             "bad_rejects": 0,
#             "avg_benefit": 0.0,
#             "avg_cost": 0.0,
#             "avg_margin": 0.0,
#             "accept_rate": 0.0,
#         }

#     accepted = [d for d in decision_log if d["decision"]]
#     rejected = [d for d in decision_log if not d["decision"]]
#     bad_accepts = [d for d in decision_log if d["decision"] and d["margin"] <= 0]
#     bad_rejects = [d for d in decision_log if (not d["decision"]) and d["margin"] > 0]

#     n = len(decision_log)
#     return {
#         "opportunities": n,
#         "accepted": len(accepted),
#         "rejected": len(rejected),
#         "bad_accepts": len(bad_accepts),
#         "bad_rejects": len(bad_rejects),
#         "avg_benefit": sum(d["benefit"] for d in decision_log) / n,
#         "avg_cost": sum(d["cost"] for d in decision_log) / n,
#         "avg_margin": sum(d["margin"] for d in decision_log) / n,
#         "accept_rate": len(accepted) / n,
#     }


# def print_decision_summary_table(rows):
#     if not rows:
#         print("No rows to print.")
#         return

#     columns = [
#         "c", "value", "time", "steals", "opportunities", "accepted", "rejected",
#         "bad_accepts", "bad_rejects", "avg_benefit", "avg_cost", "avg_margin",
#         "accept_rate", "avg_potential", "avg_migration_cost_per_time",
#         "avg_cost_aware_potential"
#     ]
#     columns = [col for col in columns if any(col in row for row in rows)]

#     def fmt(value):
#         if isinstance(value, float):
#             return f"{value:.2f}"
#         return str(value)

#     widths = {}
#     for col in columns:
#         widths[col] = max(len(col), max(len(fmt(row.get(col, ""))) for row in rows))

#     print("  ".join(col.rjust(widths[col]) for col in columns))
#     print("  ".join("-" * widths[col] for col in columns))
#     for row in rows:
#         print("  ".join(fmt(row.get(col, "")).rjust(widths[col]) for col in columns))


# def clean_completed_jobs_from_worker(worker):
#     """
#     Defensive cleanup: remove completed jobs from the queue so schedulers cannot
#     accidentally select them again.
#     """
#     worker.local_queue = [job for job in worker.local_queue if job["remaining_work"] > 0]


# def run_simulation(
#     jobs,
#     schedulers,
#     verbose=True,
#     num_workers=4,
#     job_distribution="random",
#     work_steal_threshold=0.3,
#     work_stealing_strategy=None,
#     lambda_param=1.0
# ):
#     if work_stealing_strategy is None:
#         work_stealing_strategy = AlwaysStealing()

#     if len(schedulers) != num_workers:
#         raise ValueError(f"Must provide {num_workers} schedulers for {num_workers} workers")

#     sim_jobs = prepare_jobs(jobs)
#     workers = [Worker(i, schedulers[i]) for i in range(num_workers)]

#     time_step = 0
#     total_interruptions = 0
#     total_value_lost = 0
#     total_migration_cost = 0
#     total_steals = 0
#     decision_log = []
#     potential_log = []
#     timeline_log = []
#     seen_arrivals = set()

#     while True:
#         unfinished_jobs = [job for job in sim_jobs if job["remaining_work"] > 0]
#         if not unfinished_jobs:
#             break

#         arriving_jobs = [
#             job for job in sim_jobs
#             if job["arrival"] == time_step and job["id"] not in seen_arrivals
#         ]

#         for job in arriving_jobs:
#             seen_arrivals.add(job["id"])
#             distribute_job(workers, job, strategy=job_distribution, time_step=time_step)

#         if verbose and arriving_jobs:
#             debug_print_loads(time_step, workers, "after arrivals")

#         # Run/schedule one tick on each worker.
#         for worker in workers:
#             clean_completed_jobs_from_worker(worker)

#             # If the current job is already done, clear it defensively.
#             if worker.current_job is not None and worker.current_job["remaining_work"] <= 0:
#                 worker.current_job = None

#             if worker.local_queue or worker.current_job is not None:
#                 next_job = worker.select_job(time_step)

#                 # IMPORTANT: do not run completed jobs.
#                 if next_job is None or next_job["remaining_work"] <= 0:
#                     if next_job is not None and next_job in worker.local_queue:
#                         worker.local_queue.remove(next_job)
#                     if worker.current_job is not None and worker.current_job.get("remaining_work", 0) <= 0:
#                         worker.current_job = None
#                     continue

#                 if (
#                     worker.current_job is not None
#                     and worker.current_job["id"] != next_job["id"]
#                     and worker.current_job["remaining_work"] > 0
#                 ):
#                     current = worker.current_job
#                     current["interruptions"] += 1
#                     worker.interruptions += 1
#                     total_interruptions += 1

#                     fragility_penalty = min(current["fragility"], current["effective_importance"])
#                     current["effective_importance"] -= fragility_penalty
#                     worker.value_lost += fragility_penalty
#                     total_value_lost += fragility_penalty

#                     worker.scheduler.job_preempted(current, time_step)

#                     if verbose:
#                         print(
#                             f"t={time_step} w{worker.worker_id}: preempted {current['id']}, "
#                             f"fragility penalty={fragility_penalty}"
#                         )

#                 worker.current_job = next_job

#                 # Run one unit of work, but never below zero.
#                 if next_job["remaining_work"] > 0:
#                     next_job["remaining_work"] -= 1
#                     next_job["service_received"] += 1
#                     worker.scheduler.during_job_run(next_job, time_step)

#                 if verbose:
#                     print(
#                         f"t={time_step} w{worker.worker_id}: running {next_job['id']} "
#                         f"(remaining={next_job['remaining_work']})"
#                     )

#                 if next_job["remaining_work"] == 0:
#                     next_job["completion_time"] = time_step + 1
#                     worker.scheduler.job_finish(next_job, time_step)
#                     worker.completed_jobs.append(next_job)

#                     if verbose:
#                         print(
#                             f"t={time_step} w{worker.worker_id}: completed {next_job['id']} "
#                             f"(value={next_job['effective_importance']})"
#                         )

#                     worker.current_job = None
#                     if next_job in worker.local_queue:
#                         worker.local_queue.remove(next_job)

#             clean_completed_jobs_from_worker(worker)

#         if verbose:
#             debug_print_loads(time_step, workers, "after running jobs")

#         # Work stealing.
#         idle_workers = [w for w in workers if w.being_useless()]
#         for idle_worker in idle_workers:
#             non_idle_workers = [w for w in workers if w != idle_worker and not w.being_useless()]
#             if non_idle_workers:
#                 victim = max(non_idle_workers, key=lambda w: compute_worker_load(w))
#                 victim_info = victim.get_queue_info()

#                 # Only steal jobs that still have work and are in the queue.
#                 candidate = victim_info["max_value_job"]
#                 if candidate is not None and candidate.get("remaining_work", 0) <= 0:
#                     candidate = None

#                 if candidate:
#                     stolen_job = candidate
#                     migration_cost = stolen_job["migration_cost"]

#                     victim_load_x = compute_worker_load(victim)
#                     steal_amount_s = stolen_job["remaining_work"]
#                     benefit = 2 * steal_amount_s * (victim_load_x - steal_amount_s)
#                     cost = lambda_param * migration_cost
#                     margin = benefit - cost

#                     decision = work_stealing_strategy.should_steal(
#                         idle_worker, victim, stolen_job, migration_cost, time_step, lambda_param
#                     )

#                     decision_log.append({
#                         "time": time_step,
#                         "idle_worker": idle_worker.worker_id,
#                         "victim_worker": victim.worker_id,
#                         "job_id": stolen_job["id"],
#                         "victim_load_x": victim_load_x,
#                         "steal_amount_s": steal_amount_s,
#                         "benefit": benefit,
#                         "cost": cost,
#                         "margin": margin,
#                         "decision": decision,
#                     })

#                     if verbose:
#                         print(
#                             f"\n[t={time_step}] steal decision: "
#                             f"idle=w{idle_worker.worker_id}, victim=w{victim.worker_id}, "
#                             f"job={stolen_job['id']}, x={victim_load_x}, s={steal_amount_s}, "
#                             f"benefit={benefit:.2f}, cost={cost:.2f}, margin={margin:.2f}, "
#                             f"decision={decision}"
#                         )
#                         debug_print_loads(time_step, workers, "before steal")

#                     if decision:
#                         if victim.remove_job_from_queue(stolen_job):
#                             migration_penalty = migration_cost
#                             stolen_job["effective_importance"] -= migration_penalty
#                             total_migration_cost += migration_penalty
#                             stolen_job["migration_cost_incurred"] += migration_penalty

#                             old_worker_id = stolen_job["worker_id"]
#                             idle_worker.steal_job(stolen_job)
#                             stolen_job["worker_id"] = idle_worker.worker_id
#                             total_steals += 1

#                             if verbose:
#                                 print(
#                                     f"t={time_step}: w{idle_worker.worker_id} stole "
#                                     f"{stolen_job['id']} from w{old_worker_id}, "
#                                     f"migration cost={migration_penalty}"
#                                 )
#                                 debug_print_loads(time_step, workers, "after steal")
#                         elif verbose:
#                             print(
#                                 f"t={time_step}: w{idle_worker.worker_id} tried to steal "
#                                 f"{stolen_job['id']}, but it could not be removed from victim queue"
#                             )
#                     elif verbose:
#                         print(
#                             f"t={time_step}: w{idle_worker.worker_id} rejected steal of "
#                             f"{stolen_job['id']} from w{victim.worker_id}"
#                         )

#         # Log potential and timeline metrics at end of each timestep.
#         phi = compute_imbalance_potential(workers)
#         avg_migration_cost_so_far = total_migration_cost / (time_step + 1)
#         psi = phi + lambda_param * avg_migration_cost_so_far

#         completed_so_far = []
#         for worker in workers:
#             completed_so_far.extend(worker.completed_jobs)

#         completed_value_so_far = sum(job["effective_importance"] for job in completed_so_far)
#         jobs_completed_so_far = len(completed_so_far)
#         remaining_work = sum(max(job["remaining_work"], 0) for job in sim_jobs)

#         potential_entry = {
#             "time": time_step,
#             "phi": phi,
#             "migration_cost_so_far": total_migration_cost,
#             "avg_migration_cost_per_time": avg_migration_cost_so_far,
#             "psi": psi,
#             "loads": [compute_worker_load(w) for w in workers],
#         }

#         potential_log.append(potential_entry)
#         timeline_log.append({
#             **potential_entry,
#             "completed_value": completed_value_so_far,
#             "jobs_completed": jobs_completed_so_far,
#             "remaining_work": remaining_work,
#             "total_steals": total_steals,
#         })

#         if verbose:
#             print(
#                 f"[t={time_step}] potential: "
#                 f"phi={phi:.2f}, migration_cost_so_far={total_migration_cost:.2f}, "
#                 f"avg_cost_per_time={avg_migration_cost_so_far:.2f}, psi={psi:.2f}, "
#                 f"remaining_work={remaining_work}"
#             )

#         time_step += 1

#     all_completed = []
#     for worker in workers:
#         all_completed.extend(worker.completed_jobs)

#     results = compute_results(
#         all_completed,
#         total_interruptions,
#         total_value_lost,
#         total_migration_cost,
#         time_step,
#         total_steals
#     )

#     results["completed_jobs"] = all_completed
#     results["decision_log"] = decision_log
#     results["decision_summary"] = summarize_decision_log(decision_log)
#     results["potential_log"] = potential_log
#     results["timeline_log"] = timeline_log

#     if potential_log:
#         results["avg_potential"] = sum(p["phi"] for p in potential_log) / len(potential_log)
#         results["max_potential"] = max(p["phi"] for p in potential_log)
#         results["final_potential"] = potential_log[-1]["phi"]
#         results["avg_migration_cost_per_time"] = (
#             total_migration_cost / time_step if time_step > 0 else 0
#         )
#         results["avg_cost_aware_potential"] = (
#             results["avg_potential"]
#             + lambda_param * results["avg_migration_cost_per_time"]
#         )
#         results["avg_timestep_cost_aware_potential"] = (
#             sum(p["psi"] for p in potential_log) / len(potential_log)
#         )
#     else:
#         results["avg_potential"] = 0
#         results["max_potential"] = 0
#         results["final_potential"] = 0
#         results["avg_migration_cost_per_time"] = 0
#         results["avg_cost_aware_potential"] = 0
#         results["avg_timestep_cost_aware_potential"] = 0

#     return results
