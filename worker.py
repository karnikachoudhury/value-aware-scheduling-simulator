from collections import deque

# a processor representation that can run job and has local queue
class Worker:
    
    def __init__(self, worker_id, scheduler):
        self.worker_id = worker_id
        self.scheduler = scheduler
        self.local_queue = deque() 
        self.current_job = None
        

        self.interruptions = 0
        self.value_lost = 0
        self.preemption_cost = 0
        self.completed_jobs = []
    
    def assign_job(self, job):
        self.local_queue.append(job)
        self.scheduler.job_arrival(job, -1)
    
    def select_job(self, time_step):
        available_jobs = list(self.local_queue)
        selected = self.scheduler.select_job(available_jobs, self.current_job, time_step)
        return selected
    
    # not doing anything; idle but useless is funnier
    def being_useless(self):
        return self.current_job is None and len(self.local_queue) == 0
    
    # is stealing
    def steal_job(self, job):
        self.local_queue.append(job)
    
    # got stolen from
    def remove_job_from_queue(self, job):
        if job in self.local_queue:
            self.local_queue.remove(job)
            return True
        return False
    
    def get_queue_info(self):
        total_work = sum(job["remaining_work"] for job in self.local_queue)
        max_value_job = max(self.local_queue, key=lambda j: j["importance"]) if self.local_queue else None
        return {
            "total_work": total_work,
            "queue_length": len(self.local_queue),
            "max_value_job": max_value_job,
        }
