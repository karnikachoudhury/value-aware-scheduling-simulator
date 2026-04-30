# compute results basic on completed jobs and other metrics
def compute_results_simple (jobs, total_interruptions, total_value_lost, total_preemption_cost, total_time):
    jobs_completed = sum (1 for job in jobs if job["remaining_work"] <= 0)
    work_completed = sum(job["work"] for job in jobs if job["remaining_work"] <= 0)
    value_completed = sum(job["effective_importance"] for job in jobs if job["remaining_work"] <= 0)
    
    # calculate weighted completion time
    weighted_completion_time = 0
    avg_response_time = 0
    for job in jobs:
        if job["remaining_work"] <= 0:
            response_time = job["completion_time"] - job["arrival"]
            weighted_completion_time += response_time * job["importance"]
            avg_response_time += response_time
    
    if jobs_completed > 0:
        avg_response_time /= jobs_completed

    return {
        "jobs_completed": jobs_completed,
        "work_completed": work_completed,
        "value_completed": value_completed,
        "total_interruptions": total_interruptions,
        "total_value_lost": total_value_lost,
        "total_preemption_cost": total_preemption_cost,
        "total_time": total_time,
        "weighted_completion_time": weighted_completion_time,
        "avg_response_time": avg_response_time,
    }

# compile all the results and return
def compute_results (jobs, total_interruptions, total_value_lost, total_migration_cost, total_time, total_steals=0):
    jobs_completed = sum (1 for job in jobs if job["remaining_work"] <= 0)
    work_completed = sum(job["work"] for job in jobs if job["remaining_work"] <= 0)
    value_completed = sum(job["effective_importance"] for job in jobs if job["remaining_work"] <= 0)
    
    # Calculate weighted completion time (response time from arrival to completion)
    weighted_completion_time = 0
    avg_response_time = 0
    for job in jobs:
        if job["remaining_work"] <= 0:
            response_time = job["completion_time"] - job["arrival"]
            weighted_completion_time += response_time * job["importance"]
            avg_response_time += response_time
    
    if jobs_completed > 0:
        avg_response_time /= jobs_completed

    return {
        "jobs_completed": jobs_completed,
        "work_completed": work_completed,
        "value_completed": value_completed,
        "total_interruptions": total_interruptions,
        "total_value_lost": total_value_lost,
        "total_migration_cost": total_migration_cost,
        "total_steals": total_steals,
        "total_time": total_time,
        "weighted_completion_time": weighted_completion_time,
        "avg_response_time": avg_response_time,
    }