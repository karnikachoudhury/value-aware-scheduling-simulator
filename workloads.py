# workload has varying value, work amounts, fragility levels, and preemption costs
# fragility: penalty to value when preempted (context switch overhead)
# preemption_cost: additional cost each time job is preempted
def make_balanced_workload():
    return [
        {"id": "A", "arrival": 0, "work": 8, "importance": 50, "fragility": 10, "preemption_cost": 5},
        {"id": "B", "arrival": 0, "work": 4, "importance": 20, "fragility": 0, "preemption_cost": 0},
        {"id": "C", "arrival": 2, "work": 6, "importance": 40, "fragility": 15, "preemption_cost": 7},
        {"id": "D", "arrival": 3, "work": 2, "importance": 10, "fragility": 0, "preemption_cost": 0},
    ]

def make_database_workload():
    return [
       # background task that is long and fragile, but has high value
        {"id": "compaction", "arrival": 0, "work": 15, "importance": 80, "fragility": 25, "preemption_cost": 15},

        # queries that are short and frequent..
        {"id": "q1", "arrival": 1, "work": 2, "importance": 15, "fragility": 0, "preemption_cost": 0},
        {"id": "q2", "arrival": 2, "work": 2, "importance": 15, "fragility": 0, "preemption_cost": 0},
        {"id": "q3", "arrival": 3, "work": 2, "importance": 15, "fragility": 0, "preemption_cost": 0},
        {"id": "q4", "arrival": 4, "work": 2, "importance": 15, "fragility": 0, "preemption_cost": 0},
    ]

# lots of small requests, low fragility but negligible preemption costs
def make_web_workload():
    return [
        {"id": "r1", "arrival": 0, "work": 1, "importance": 5, "fragility": 0, "preemption_cost": 0},
        {"id": "r2", "arrival": 0, "work": 1, "importance": 5, "fragility": 0, "preemption_cost": 0},
        {"id": "r3", "arrival": 1, "work": 1, "importance": 5, "fragility": 0, "preemption_cost": 0},
        {"id": "r4", "arrival": 1, "work": 1, "importance": 5, "fragility": 0, "preemption_cost": 0},
        {"id": "r5", "arrival": 2, "work": 1, "importance": 5, "fragility": 0, "preemption_cost": 0},
        {"id": "r6", "arrival": 2, "work": 1, "importance": 5, "fragility": 0, "preemption_cost": 0},
    ]

# super fragile, long-running jobs that are very high in value
def make_ml_workload():
    return [
        {"id": "train_model", "arrival": 0, "work": 20, "importance": 100, "fragility": 30, "preemption_cost": 20},
        {"id": "batch_1", "arrival": 0, "work": 10, "importance": 50, "fragility": 20, "preemption_cost": 12},
        {"id": "batch_2", "arrival": 1, "work": 10, "importance": 50, "fragility": 20, "preemption_cost": 12},
    ]