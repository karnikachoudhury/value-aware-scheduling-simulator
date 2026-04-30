import random

class PowerOfTwoChoices:
    name = "Power of 2 Choices"
    
    def __init__(self, metric="value_to_work", seed=None):
        self.metric = metric
        self.preemption_cost_caused = 0
        if seed is not None:
            random.seed(seed)
    
    # pls let me compile without this useless ass method wtf
    def job_arrival(self, job, time_step):
        pass
    
    # once we have the two jobs, pick which one is better based on the metric
    def _compute_job_score(self, job):
        if self.metric == "value_to_work":
            return job["importance"] / max(job["remaining_work"], 1)
        elif self.metric == "value":
            return job["importance"]
        elif self.metric == "shortest_job":
            return -job["remaining_work"]
        else:
            return job["importance"]
    
    def select_job(self, available_jobs, current_job, time_step):
        # don't preempt
        if current_job is not None and current_job["remaining_work"] > 0:
            return current_job
        
        if not available_jobs:
            return None
        
        if len(available_jobs) <= 2:
            # stupid edge case
            if len(available_jobs) == 1:
                return available_jobs[0]
            return max(available_jobs, key=self._compute_job_score)
        
        # i like java math.random better python sucks ass
        sample = random.sample(available_jobs, 2)
        
        return max(sample, key=self._compute_job_score)
    
    def during_job_run(self, job, time_step):
        pass
    
    def job_finish(self, job, time_step):
        pass
    
    def job_preempted(self, job, time_step):
        pass
