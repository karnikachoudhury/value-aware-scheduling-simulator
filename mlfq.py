from collections import deque

class MLFQ:
    name = "MLFQ"
    def __init__(self, quanta=(1, 2, 4), boost_interval=12):
        self.quanta = list(quanta)
        self.boost_interval = boost_interval
        self.queues = [deque() for _ in self.quanta]
        self.job_level = {}
        self.time_used_at_level = {}
        self.current_epoch = 0

    def job_arrival(self, job, time_step):
        # new job goes into highest priority queue
        if job["id"] not in self.job_level:
            self.job_level[job["id"]] = 0
            self.time_used_at_level[job["id"]] = 0
            self.queues[0].append(job)

    # reset all the priorities when needed
    def boost_all(self, available_jobs):
        # initialize all queues
        self.queues = [deque() for _ in self.quanta]
        # initialize job_level and time used for each of the jobs
        for job in available_jobs:
            if job["remaining_work"] > 0:
                self.job_level[job["id"]] = 0
                self.time_used_at_level[job["id"]] = 0
                self.queues[0].append(job)

    def select_job(self, available_jobs, current_job, time_step):
        # boost if it is time to boost
        if self.boost_interval > 0 and time_step > 0 and time_step % self.boost_interval == 0:
            self.boost_all(available_jobs)
        
        # Ensure all available jobs are registered with this scheduler
        for job in available_jobs:
            if job["id"] not in self.job_level:
                self.job_arrival(job, time_step)

        available_ids = {job["id"] for job in available_jobs}

        # there is work left
        if current_job is not None and current_job["remaining_work"] > 0:
            level = self.job_level[current_job["id"]]
            used = self.time_used_at_level[current_job["id"]]

            # if there is a higher priority job then preempt and demote current job, time slice is secondary
            for higher in range(level):
                while self.queues[higher] and self.queues[higher][0]["id"] not in available_ids:
                    self.queues[higher].popleft()
                # promotion
                if self.queues[higher]:
                    self.queues[level].append(current_job)
                    self.time_used_at_level[current_job["id"]] = 0
                    break
            else:
                if used < self.quanta[level]:
                    return current_job

                # time slice up so demote
                if level < len(self.quanta) - 1:
                    self.job_level[current_job["id"]] += 1
                self.time_used_at_level[current_job["id"]] = 0
                self.queues[self.job_level[current_job["id"]]].append(current_job)
        # go through mlfq queues in order and return the first available job
        for level in range(len(self.queues)):
            while self.queues[level] and self.queues[level][0]["id"] not in available_ids:
                self.queues[level].popleft()
            if self.queues[level]:
                return self.queues[level].popleft()

        return None

    def during_job_run(self, job, time_step):
        self.time_used_at_level[job["id"]] += 1

    def job_finish(self, job, time_step):
        self.time_used_at_level[job["id"]] = 0

    def job_preempted(self, job, time_step):
        if job["remaining_work"] > 0:
            level = self.job_level[job["id"]]
            self.queues[level].append(job)
            self.time_used_at_level[job["id"]] = 0