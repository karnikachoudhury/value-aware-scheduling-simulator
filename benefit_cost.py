from dataclasses import dataclass
from typing import List, Dict
import csv


@dataclass
class Trial:
    victim_load_x: int
    steal_amount_s: int
    migration_cost_c: int
    lambda_param: float = 1.0

# quadratic potential function to measure load imbalance
def potential(loads: List[int]) -> float:
    avg = sum(loads) / len(loads)
    return sum((load - avg) ** 2 for load in loads)


# run a trial of the experiment/execution
def run_trial(trial: Trial, num_workers: int = 4) -> Dict[str, float]:
    x = trial.victim_load_x
    s = trial.steal_amount_s
    c = trial.migration_cost_c
    lam = trial.lambda_param

    # one overloaded worker, rest are idle
    before_loads = [x] + [0] * (num_workers - 1)

    # move s work from worker 0 to worker 1
    after_loads = [x - s, s] + [0] * (num_workers - 2)

    phi_before = potential(before_loads)
    phi_after = potential(after_loads)
    phi_change = phi_after - phi_before
    phi_reduction = phi_before - phi_after

    benefit = 2 * s * (x - s)
    weighted_cost = lam * c
    margin = benefit - weighted_cost

    psi_before = phi_before
    psi_after = phi_after + weighted_cost
    psi_change = psi_after - psi_before

    predicted_steal_helps = benefit > weighted_cost
    actual_steal_helps = psi_after < psi_before

    return {
        "x_victim_load": x,
        "s_stolen_work": s,
        "c_migration_cost": c,
        "lambda": lam,
        "benefit_2s_x_minus_s": benefit,
        "weighted_cost_lambda_c": weighted_cost,
        "margin_benefit_minus_cost": margin,
        "phi_before": phi_before,
        "phi_after": phi_after,
        "phi_reduction": phi_reduction,
        "psi_before": psi_before,
        "psi_after": psi_after,
        "psi_change_after_minus_before": psi_change,
        "formula_says_steal_helps": predicted_steal_helps,
        "actual_steal_helps": actual_steal_helps,
        "matches_lemma": predicted_steal_helps == actual_steal_helps,
    }

def format_bool(value: bool) -> str:
    return "YES" if value else "NO"


# print function
def print_table(rows: List[Dict[str, float]]) -> None:
    headers = [
        "x", "s", "c", "benefit", "cost", "margin",
        "Phi before", "Phi after", "Psi before", "Psi after",
        "formula says helps", "actually helps", "matches"
    ]

    print("\n" + "=" * 130)
    print("BENEFIT VS COST WORK-STEALING LEMMA EXPERIMENT")
    print("=" * 130)
    print(
        f"{headers[0]:>5} {headers[1]:>5} {headers[2]:>6} "
        f"{headers[3]:>10} {headers[4]:>10} {headers[5]:>10} "
        f"{headers[6]:>12} {headers[7]:>12} {headers[8]:>12} {headers[9]:>12} "
        f"{headers[10]:>18} {headers[11]:>15} {headers[12]:>10}"
    )
    print("-" * 130)

    for r in rows:
        print(
            f"{r['x_victim_load']:5.0f} "
            f"{r['s_stolen_work']:5.0f} "
            f"{r['c_migration_cost']:6.0f} "
            f"{r['benefit_2s_x_minus_s']:10.2f} "
            f"{r['weighted_cost_lambda_c']:10.2f} "
            f"{r['margin_benefit_minus_cost']:10.2f} "
            f"{r['phi_before']:12.2f} "
            f"{r['phi_after']:12.2f} "
            f"{r['psi_before']:12.2f} "
            f"{r['psi_after']:12.2f} "
            f"{format_bool(r['formula_says_steal_helps']):>18} "
            f"{format_bool(r['actual_steal_helps']):>15} "
            f"{format_bool(r['matches_lemma']):>10}"
        )

    print("=" * 130)
    print("Interpretation:")
    print("  margin = benefit - cost = 2*s*(x-s) - lambda*c")
    print("  Positive margin means the lemma predicts stealing helps.")
    print("  Negative margin means the lemma predicts stealing hurts.")
    print("  'matches' should be YES for every row.")

# save results to csv for plotting
def save_csv(rows: List[Dict[str, float]], filename: str = "benefit_vs_cost_results.csv") -> None:
    if not rows:
        return
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved CSV to: {filename}")


def main() -> None:
    x = 40
    s = 10
    lambda_param = 1.0

    migration_costs = [0, 100, 300, 599, 600, 700, 1000]

    trials = [Trial(x, s, c, lambda_param) for c in migration_costs]
    rows = [run_trial(trial) for trial in trials]

    print_table(rows)
    save_csv(rows)

    print("\nThreshold explanation:")
    threshold = 2 * s * (x - s) / lambda_param
    print(f"  With x={x}, s={s}, lambda={lambda_param}, the threshold is c < {threshold:.2f}.")
    print("  Rows with c below this threshold should improve Psi.")
    print("  Rows with c at or above this threshold should not improve Psi.")


if __name__ == "__main__":
    main()
