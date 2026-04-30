from collections import deque

class FIFO:
    name = "FIFO"
    
    def __init__(self):
        pass
    
    def job_arrival(self, job, time_step):
        pass

    def select_job(self, available_jobs, current_job, time_step):
        if current_job is not None and current_job["remaining_work"] > 0:
                return current_job
        if not available_jobs:
            return None
        # everytime we need to choosen the smallest arrival time bc that means it got here first
        return min(available_jobs, key=lambda j: j["arrival"])

    def during_job_run(self, job, time_step):
        pass

    def job_finish(self, job, time_step):
        pass

    def job_preempted(self, job, time_step):
        pass