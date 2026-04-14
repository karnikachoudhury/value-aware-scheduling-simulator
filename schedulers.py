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
    if not available_jobs:
        return None
    max = float("-inf")
    chosen_job = None
    for job in available_jobs:
        if job["value"] > min:
            min = job["value"]
            chosen_job = job
    return chosen_job