# workload has  varying value, work amounts, and fragility levels.. should be a baseline?
def make_balanced_workload():
    return [
        {"id": "A", "arrival": 0, "work": 8, "value": 50, "fragility": 10},
        {"id": "B", "arrival": 0, "work": 4, "value": 20, "fragility": 0},
        {"id": "C", "arrival": 2, "work": 6, "value": 40, "fragility": 15},
        {"id": "D", "arrival": 3, "work": 2, "value": 10, "fragility": 0},
    ]

def make_database_workload():
    return [
       # background task that is long and fragile, but has high value
        {"id": "compaction", "arrival": 0, "work": 15, "value": 80, "fragility": 25},

        # queries that are short and frequent..
        {"id": "q1", "arrival": 1, "work": 2, "value": 15, "fragility": 0},
        {"id": "q2", "arrival": 2, "work": 2, "value": 15, "fragility": 0},
        {"id": "q3", "arrival": 3, "work": 2, "value": 15, "fragility": 0},
        {"id": "q4", "arrival": 4, "work": 2, "value": 15, "fragility": 0},
    ]

# lots of small requests, very fragile but also low in value and not weighted that differently
def make_web_workload():
    return [
        {"id": "r1", "arrival": 0, "work": 1, "value": 5, "fragility": 0},
        {"id": "r2", "arrival": 0, "work": 1, "value": 5, "fragility": 0},
        {"id": "r3", "arrival": 1, "work": 1, "value": 5, "fragility": 0},
        {"id": "r4", "arrival": 1, "work": 1, "value": 5, "fragility": 0},
        {"id": "r5", "arrival": 2, "work": 1, "value": 5, "fragility": 0},
        {"id": "r6", "arrival": 2, "work": 1, "value": 5, "fragility": 0},
    ]

# super fragile, long-running jobs that are very high in value
def make_ml_workload():
    return [
        {"id": "train_model", "arrival": 0, "work": 20, "value": 100, "fragility": 30},
        {"id": "batch_1", "arrival": 0, "work": 10, "value": 50, "fragility": 20},
        {"id": "batch_2", "arrival": 1, "work": 10, "value": 50, "fragility": 20},
    ]