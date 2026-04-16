# compile all the results and return
def compute_results (jobs, total_interruptions, total_value_lost, total_time):
    jobs_completed = sum (1 for job in jobs if job["remaining_work"] <= 0)
    work_completed = sum(job["work"] for job in jobs if job["remaining_work"] <= 0)
    value_completed = sum(job["effective_value"] for job in jobs if job["remaining_work"] <= 0)
    
    # Calculate weighted completion time (response time from arrival to completion)
    weighted_completion_time = 0
    avg_response_time = 0
    for job in jobs:
        if job["remaining_work"] <= 0:
            response_time = job["completion_time"] - job["arrival"]
            weighted_completion_time += response_time * job["value"]
            avg_response_time += response_time
    
    if jobs_completed > 0:
        avg_response_time /= jobs_completed

    return {
        "jobs_completed": jobs_completed,
        "work_completed": work_completed,
        "value_completed": value_completed,
        "total_interruptions": total_interruptions,
        "total_value_lost": total_value_lost,
        "total_time": total_time,
        "weighted_completion_time": weighted_completion_time,
        "avg_response_time": avg_response_time,
    }