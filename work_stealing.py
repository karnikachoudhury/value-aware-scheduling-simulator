from collections import deque
import random

class WorkStealing:
    name = "Work Stealing"
    
    def __init__(self):
        self.preemption_cost_caused = 0
    
    # why the fuck does this need to be here stop erroring
    def job_arrival(self, job, time_step):
        pass
    
    def select_job(self, available_jobs, current_job, time_step):
        # Continue running job if available
        if current_job is not None and current_job["remaining_work"] > 0:
            return current_job
        
        if not available_jobs:
            return None
        
        # pick highest value job from local queue (worker will steal if it's better elsewhere)
        # importance / remaining work is value ratio
        return max(available_jobs, key=lambda j: j["importance"] / max(j["remaining_work"], 1))
    
    def during_job_run(self, job, time_step):
        pass
    
    def job_finish(self, job, time_step):
        pass
    
    def job_preempted(self, job, time_step):
        pass
