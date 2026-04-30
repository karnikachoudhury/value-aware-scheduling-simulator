# interface for different work stealing strategies to be used in the simulator
class WorkStealingStrategy:
    
    def should_steal(self, idle_worker, victim_worker, stolen_job, migration_cost, time_step, lambda_param=1.0):
        raise NotImplementedError


class NoStealing(WorkStealingStrategy):    
    def should_steal(self, idle_worker, victim_worker, stolen_job, migration_cost, time_step, lambda_param=1.0):
        return False


class AlwaysStealing(WorkStealingStrategy):    
    def should_steal(self, idle_worker, victim_worker, stolen_job, migration_cost, time_step, lambda_param=1.0):
        return True


class CostAwareStealing(WorkStealingStrategy):

    def should_steal(self, idle_worker, victim_worker, stolen_job,
                     migration_cost, time_step, lambda_param=1.0):

        # x = total work currently on victim worker
        victim_info = victim_worker.get_queue_info()
        x = victim_info["total_work"]

        # s = amount of work moved (remaining work of the job)
        s = stolen_job["remaining_work"]

        benefit = 2 * s * (x - s)
        cost = lambda_param * migration_cost

        return benefit > cost