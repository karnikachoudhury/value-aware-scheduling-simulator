class LinuxCFS:
    name = "Linux CFS"
    def __init__(self):
        pass

    def select_job(self, available_jobs, current_job, time_step):
        if not available_jobs:
            return None
        return min(available_jobs, key=lambda j: (j["vruntime"], j["arrival"]))

    def job_arrival(self, job, time_step):
        pass
    
    def during_job_run(self, job, time_step):
        # jobs with more weight means they should get more CPU time so increase vruntime less
        weight = job["weight"]
        job["vruntime"] += 1024.0 / weight
    
    def job_finish(self, job, time_step):
        pass
    
    def job_preempted(self, job, time_step):
        pass