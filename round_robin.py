from collections import deque

class RoundRobin:
    name = "Round Robin"
    def __init__(self, quantum=2):
        self.quantum = quantum
        self.queue = deque()
        self.time_used = {}
    
    def job_arrival(self, job, time_step):
        if job["id"] not in self.time_used:
            self.time_used[job["id"]] = 0
            self.queue.append(job)
    
    def select_job(self, available_jobs, current_job, time_step):
        available_ids = {job["id"] for job in available_jobs}
        
        # Ensure all available jobs are registered with this scheduler
        for job in available_jobs:
            if job["id"] not in self.time_used:
                self.job_arrival(job, time_step)

        # clean finished jobs
        while self.queue and (self.queue[0]["id"] not in available_ids):
            self.queue.popleft()

        if current_job is not None and current_job["remaining_work"] > 0:
            used = self.time_used[current_job["id"]]
            if used < self.quantum:
                return current_job

            # quantum expired time to preempt loser
            self.time_used[current_job["id"]] = 0
            if current_job["id"] in available_ids:
                self.queue.append(current_job)

        # job has remaining work and is available yay
        while self.queue:
            candidate = self.queue.popleft()
            if candidate["id"] in available_ids and candidate["remaining_work"] > 0:
                return candidate
        
        # no jobs in queue, pick first available
        if available_jobs:
            return available_jobs[0]

        return None

    def during_job_run(self, job, time_step):
        self.time_used[job["id"]] += 1

    def job_finish(self, job, time_step):
        self.time_used[job["id"]] = 0
    
    def job_preempted(self, job, time_step):
        pass