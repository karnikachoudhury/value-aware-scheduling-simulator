from metrics import compute_results

def run_simulation_loop (jobs, scheduler, verbose = True):
    # copy jobs so references not fucked up
    jobs_copy = []
    for job in jobs:
        jobs_copy.append({
            "id": job["id"],
            "arrival": job["arrival"],
            "work": job["work"],
            "remaining_work": job["work"],
            "value": job["value"],
            "effective_value": job["value"],
            "fragility": job["fragility"],
            "interruptions": 0,
            "completed": False,
            "completion_time": None,
        })
    
    time_step = 0
    current_job = None
    total_interruptions = 0
    total_value_lost = 0

    unfinished_jobs = []
    available_jobs = []
    while True:
        # populate unfinished_jobs array
        unfinished_jobs = []
        for job in jobs_copy:
            if job["remaining_work"] > 0:
                unfinished_jobs.append(job)
        if not unfinished_jobs:
            break

        # populate available jobs depending on arrival and if there is remaining work left
        available_jobs = []
        for job in jobs_copy:
            if job["arrival"] <= time_step and job["remaining_work"] > 0:
                available_jobs.append(job)
        if not available_jobs:
            if verbose:
                print(f"Time {time_step}: no jobs idle af")
            time_step += 1
            continue
    
        # consider the next job from scheduler
        next_job = scheduler(available_jobs, current_job, time_step)

        # update interrupts and value lost
        if current_job is not None and next_job is not None and current_job["id"] != next_job["id"]:
            if current_job["remaining_work"] > 0:
                current_job["interruptions"] += 1
                total_interruptions += 1
                
                penalty = min(current_job["fragility"], current_job["remaining_work"])
                current_job["effective_value"] -= penalty
                total_value_lost += penalty

                if verbose:
                    print(f"t={time_step}: interrupted {current_job['id']}, " f"lost {penalty} value")
        current_job = next_job

        if(current_job is not None):
            current_job["remaining_work"] -= 1
            if verbose:
                print(f"t={time_step}: working on {current_job['id']}, " f"remaining work {current_job['remaining_work']}")
            if(current_job["remaining_work"] == 0):
                current_job["completed"] = True
                current_job["completion_time"] = time_step
                if verbose:
                    print(f"t={time_step}: completed {current_job['id']}")
                current_job = None
        
        time_step += 1
    return compute_results(jobs_copy, total_interruptions, total_value_lost, time_step)
    


            

    