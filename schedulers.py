# ez FIFO implementation
def fifo(available_jobs, current_job, time_step):
    if current_job is not None:
        return current_job
    if not available_jobs:
        return None
    # smallest arrival time got here first, first in first out 
    min = float("inf")
    chosen_job = None
    for job in available_jobs:
        if job["arrival"] < min:
            min = job["arrival"]
            chosen_job = job
    return chosen_job

# SJF, same as FIFO but remaining_work
def shortest_job_first(available_jobs, current_job, time_step):
    if current_job is not None:
        return current_job
    if not available_jobs:
        return None
    min = float("inf")
    chosen_job = None
    for job in available_jobs:
        if job["remaining_work"] < min:
            min = job["remaining_work"]
            chosen_job = job
    return chosen_job

# we chose jobs with highest value, same as the other two ez
def value_first(available_jobs, current_job, time_step):
    if current_job is not None:
        return current_job
    if not available_jobs:
        return None
    max = float("-inf")
    chosen_job = None
    for job in available_jobs:
        if job["value"] > max:
            max = job["value"]
            chosen_job = job
    return chosen_job

# makes sure that we do not preempt a job that is already pretty fragile.. 
def fragile_aware(available_jobs, current_job, time_step):
    if not available_jobs:
        return None
    if current_job is not None and current_job["fragility"] - time_step < 5:
        return current_job
    
    # go through jobs and calculate (job_value + job_fragility) / job_remaining_work..
    max = float("-inf")
    chosen_job = None
    for job in available_jobs:
        value_to_work_ratio =  (job["value"] + job["fragility"]) / job["remaining_work"]
        if value_to_work_ratio > max:
            max = value_to_work_ratio
            chosen_job = job
    return chosen_job
