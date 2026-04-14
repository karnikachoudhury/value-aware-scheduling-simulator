# workload has  varying value, work amounts, and fragility levels.. should be a baseline?
def make_balanced_workload():
    return [
        {"id": "A", "arrival": 0, "work": 8, "value": 50, "fragility": 10},
        {"id": "B", "arrival": 0, "work": 4, "value": 20, "fragility": 0},
        {"id": "C", "arrival": 2, "work": 6, "value": 40, "fragility": 15},
        {"id": "D", "arrival": 3, "work": 2, "value": 10, "fragility": 0},
    ]

