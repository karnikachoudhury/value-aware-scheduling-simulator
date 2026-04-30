# workload has varying value, work amounts, fragility levels, and migration costs
# fragility: penalty to value when preempted on same worker (context switch overhead)
# migration_cost: penalty to value when moved to different worker (cache/state transfer overhead)
def make_balanced_workload():
    return [
        {"id": "A", "arrival": 0, "work": 8, "importance": 50, "fragility": 10, "migration_cost": 8},
        {"id": "B", "arrival": 0, "work": 4, "importance": 20, "fragility": 0, "migration_cost": 2},
        {"id": "C", "arrival": 2, "work": 6, "importance": 40, "fragility": 15, "migration_cost": 10},
        {"id": "D", "arrival": 3, "work": 2, "importance": 10, "fragility": 0, "migration_cost": 1},
    ]


def make_fork_join_workload():
    """
    MULTIPLE independent substantial tasks all go to Worker 2 (via round-robin on ID length).
    Other workers get tiny filler tasks, then go idle.
    
    This creates a scenario where work stealing provides parallelism benefit:
    - No-stealing: Worker 2 runs 4x40=160 time units sequentially, others idle
    - With stealing: Steal to idle workers, get ~40 time units (4x speedup!)
    - Cost-aware at low c: Worth stealing (benefit > cost)
    - Cost-aware at high c: Not worth stealing (cost > benefit)
    """
    # Round-robin uses len(id) % num_workers
    # len=6 → 6%4=2 (Worker 2 gets the big tasks)
    # len=5 → 5%4=1 (Worker 1 filler)
    # len=4 → 4%4=0 (Worker 0 filler)
    # len=7 → 7%4=3 (Worker 3 filler)
    return [
        # Four substantial tasks all to Worker 2 (len=6, 6%4=2)
        {"id": "big_aa", "arrival": 0, "work": 40, "importance": 80, "fragility": 10, "migration_cost": 50},
        {"id": "big_bb", "arrival": 0, "work": 40, "importance": 80, "fragility": 10, "migration_cost": 50},
        {"id": "big_cc", "arrival": 0, "work": 40, "importance": 80, "fragility": 10, "migration_cost": 50},
        {"id": "big_dd", "arrival": 0, "work": 40, "importance": 80, "fragility": 10, "migration_cost": 50},
        
        # Filler for worker 1 (len=5, 5%4=1) - short, finishes quickly
        {"id": "fill1", "arrival": 0, "work": 2, "importance": 5, "fragility": 0, "migration_cost": 1},
        
        # Filler for worker 0 (len=4, 4%4=0)
        {"id": "fill0", "arrival": 0, "work": 2, "importance": 5, "fragility": 0, "migration_cost": 1},
        
        # Filler for worker 3 (len=7, 7%4=3)
        {"id": "fill3xx", "arrival": 0, "work": 2, "importance": 5, "fragility": 0, "migration_cost": 1},
    ]


def make_bursty_workload():
    """
    Many independent mid-sized parallel tasks.
    With work stealing: Get 4x parallelism
    Without work stealing: Sequential execution
    """
    return [
        # Six independent tasks perfect for parallelism
        {"id": "job_1", "arrival": 0, "work": 60, "importance": 100, "fragility": 15, "migration_cost": 40},
        {"id": "job_2", "arrival": 0, "work": 60, "importance": 100, "fragility": 15, "migration_cost": 40},
        {"id": "job_3", "arrival": 0, "work": 60, "importance": 100, "fragility": 15, "migration_cost": 40},
        {"id": "job_4", "arrival": 0, "work": 60, "importance": 100, "fragility": 15, "migration_cost": 40},
        {"id": "job_5", "arrival": 0, "work": 60, "importance": 100, "fragility": 15, "migration_cost": 40},
        {"id": "job_6", "arrival": 0, "work": 60, "importance": 100, "fragility": 15, "migration_cost": 40},
    ]


def make_skewed_importance_workload():
    """
    Eight high-value independent tasks.
    Massive parallelism opportunity if work stealing works.
    """
    return [
        # Eight equal-value independent tasks
        {"id": "w1", "arrival": 0, "work": 50, "importance": 90, "fragility": 12, "migration_cost": 30},
        {"id": "w2", "arrival": 0, "work": 50, "importance": 90, "fragility": 12, "migration_cost": 30},
        {"id": "w3", "arrival": 0, "work": 50, "importance": 90, "fragility": 12, "migration_cost": 30},
        {"id": "w4", "arrival": 0, "work": 50, "importance": 90, "fragility": 12, "migration_cost": 30},
        {"id": "w5", "arrival": 0, "work": 50, "importance": 90, "fragility": 12, "migration_cost": 30},
        {"id": "w6", "arrival": 0, "work": 50, "importance": 90, "fragility": 12, "migration_cost": 30},
        {"id": "w7", "arrival": 0, "work": 50, "importance": 90, "fragility": 12, "migration_cost": 30},
        {"id": "w8", "arrival": 0, "work": 50, "importance": 90, "fragility": 12, "migration_cost": 30},
    ]

def make_database_workload():
    return [
       # background task that is long and fragile, but has high value
        {"id": "compaction", "arrival": 0, "work": 15, "importance": 80, "fragility": 25, "migration_cost": 20},

        # queries that are short and frequent..
        {"id": "q1", "arrival": 1, "work": 2, "importance": 15, "fragility": 0, "migration_cost": 1},
        {"id": "q2", "arrival": 2, "work": 2, "importance": 15, "fragility": 0, "migration_cost": 1},
        {"id": "q3", "arrival": 3, "work": 2, "importance": 15, "fragility": 0, "migration_cost": 1},
        {"id": "q4", "arrival": 4, "work": 2, "importance": 15, "fragility": 0, "migration_cost": 1},
    ]

# lots of small stateless requests, low migration costs
def make_web_workload():
    return [
        {"id": "r1", "arrival": 0, "work": 1, "importance": 5, "fragility": 0, "migration_cost": 0},
        {"id": "r2", "arrival": 0, "work": 1, "importance": 5, "fragility": 0, "migration_cost": 0},
        {"id": "r3", "arrival": 1, "work": 1, "importance": 5, "fragility": 0, "migration_cost": 0},
        {"id": "r4", "arrival": 1, "work": 1, "importance": 5, "fragility": 0, "migration_cost": 0},
        {"id": "r5", "arrival": 2, "work": 1, "importance": 5, "fragility": 0, "migration_cost": 0},
        {"id": "r6", "arrival": 2, "work": 1, "importance": 5, "fragility": 0, "migration_cost": 0},
    ]

# super fragile, long-running jobs with high state that are very high in value
def make_ml_workload():
    return [
        {"id": "train_model", "arrival": 0, "work": 20, "importance": 100, "fragility": 30, "migration_cost": 25},
        {"id": "batch_1", "arrival": 0, "work": 10, "importance": 50, "fragility": 20, "migration_cost": 15},
        {"id": "batch_2", "arrival": 1, "work": 10, "importance": 50, "fragility": 20, "migration_cost": 15},
    ]

def make_cost_aware_wins_workload():
    """
    Cost-aware should beat Always Stealing dramatically.

    Reason:
    - Large jobs arrive one at a time or in small waves.
    - A steal often moves almost the entire remaining victim load.
    - That makes x-s small, so 2*s*(x-s) is small.
    - Cost-aware rejects many steals.
    - Always-stealing still migrates and pays huge cost.
    """
    jobs = []

    arrivals = [0, 8, 16, 24, 32, 40, 48, 56]

    for i, arrival in enumerate(arrivals):
        jobs.append({
            "id": f"large_single_{i}",
            "arrival": arrival,
            "work": 20,
            "importance": 100,
            "fragility": 0,
            "migration_cost": 0,
        })

    return jobs
    


def make_always_stealing_wins_workload():
    """
    Cost-aware should behave similarly to Always Stealing.

    Reason:
    - Many small jobs start on one worker.
    - Victim load x is large.
    - Stolen amount s is small.
    - Therefore 2*s*(x-s) is large, so cost-aware approves steals.
    """
    jobs = []

    for i in range(40):
        jobs.append({
            "id": f"small_parallel_{i}",
            "arrival": 0,
            "work": 4,
            "importance": 100,
            "fragility": 0,
            "migration_cost": 0,
        })

    return jobs
    