"""
sort_test.py — Deterministic, replayable battery of sorting algorithm tests.

Seeds are chosen from well-known mathematical constants (scaled to integers)
so any result can be reproduced by re-running with the same seed:

    SEEDS = [42, 137, 1618, 2718, 3141, 9973, 31337, 65537]

Every data point in the output carries its seed; to replay any single trial:

    gen_fn(n, seed=<seed>)   →   alg_fn(arr)

Results are written to src/test_results.json with full metadata.

Questions answered:
  Q1. Is Bubble still the least effective algorithm overall?
  Q2. Are there input classes where any algorithm outperforms TimCustom?
  Q3. Which hybrids succeed, and by how much?
"""

import sys
import time
import json
import random
import statistics
from collections import defaultdict

sys.setrecursionlimit(100_000)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─────────────────────────────────────────────────────────────────────────────
# Import shared implementations from benchmark_deep
# ─────────────────────────────────────────────────────────────────────────────
from benchmark_deep import (
    bubble_sort, insertion_sort, selection_sort,
    merge_sort, quick_sort, heap_sort, radix_sort, tim_custom,
    hybrid_qi, hybrid_mi, hybrid_ri, hybrid_intro,
    gen_random, gen_sorted, gen_reverse, gen_nearly_sorted,
    gen_few_unique, gen_sawtooth, gen_pipe_organ, gen_all_same,
    gen_two_values, gen_interleaved, gen_rotated,
    gen_random_blocks, gen_killer_quick,
)

# ─────────────────────────────────────────────────────────────────────────────
# Test configuration
# ─────────────────────────────────────────────────────────────────────────────

# Seeds sourced from scaled mathematical constants — fully documented.
#   42       : canonical default
#   137      : fine-structure constant × 1000 ≈ 137
#   1618     : golden ratio × 1000
#   2718     : Euler's number × 1000
#   3141     : pi × 1000
#   9973     : largest 4-digit prime
#   31337    : 'elite' in hacker lore (deliberately distinct from math seeds)
#   65537    : Fermat prime F4 (used in RSA key generation)
SEEDS = [42, 137, 1618, 2718, 3141, 9973, 31337, 65537]

SIZES = [64, 256, 1024]          # powers of 2; clean for log₂ analysis
SLOW_MAX = 256                   # O(n²) algorithms skip n > SLOW_MAX

ALGORITHMS = {
    "Bubble":       bubble_sort,
    "Insertion":    insertion_sort,
    "Selection":    selection_sort,
    "Merge":        merge_sort,
    "Quick":        quick_sort,
    "Heap":         heap_sort,
    "Radix":        radix_sort,
    "Tim":          tim_custom,
    "Hybrid_QI":    hybrid_qi,
    "Hybrid_MI":    hybrid_mi,
    "Hybrid_RI":    hybrid_ri,
    "Hybrid_Intro": hybrid_intro,
}

SLOW_ALGS = {"Bubble", "Selection"}

GENERATORS = {
    "random":        gen_random,
    "sorted":        gen_sorted,
    "reverse":       gen_reverse,
    "nearly_sorted": gen_nearly_sorted,
    "few_unique":    gen_few_unique,
    "sawtooth":      gen_sawtooth,
    "pipe_organ":    gen_pipe_organ,
    "all_same":      gen_all_same,
    "two_values":    gen_two_values,
    "interleaved":   gen_interleaved,
    "rotated":       gen_rotated,
    "random_blocks": gen_random_blocks,
    "killer_quick":  gen_killer_quick,
}

# ─────────────────────────────────────────────────────────────────────────────
# Core runner
# ─────────────────────────────────────────────────────────────────────────────

def run_battery():
    """
    Run every combination of (algorithm, input_type, size, seed).
    Returns a flat list of result dicts, each fully self-describing.
    """
    # Pre-calculate total trials for progress display
    total = sum(
        1
        for alg  in ALGORITHMS
        for inp  in GENERATORS
        for n    in SIZES
        for _    in SEEDS
        if not (alg in SLOW_ALGS and n > SLOW_MAX)
    )

    print(f"Battery: {len(ALGORITHMS)} algorithms × {len(GENERATORS)} input types "
          f"× {len(SIZES)} sizes × {len(SEEDS)} seeds")
    print(f"Total trials: {total}  (O(n²) algorithms capped at n={SLOW_MAX})")
    print()

    records = []
    done = 0

    for alg_name, alg_fn in ALGORITHMS.items():
        for inp_name, gen_fn in GENERATORS.items():
            for n in SIZES:
                if alg_name in SLOW_ALGS and n > SLOW_MAX:
                    continue
                for seed in SEEDS:
                    arr = gen_fn(n, seed=seed)
                    expected = sorted(arr)

                    try:
                        t0 = time.perf_counter()
                        result_arr, comps, ops = alg_fn(arr)
                        elapsed = time.perf_counter() - t0

                        correct = (result_arr == expected)
                        if not correct:
                            print(f"  [FAIL] {alg_name} / {inp_name} n={n} seed={seed}: "
                                  f"incorrect output")

                        records.append({
                            "alg":        alg_name,
                            "input":      inp_name,
                            "n":          n,
                            "seed":       seed,
                            "time_s":     elapsed,
                            "comparisons":comps,
                            "ops":        ops,
                            "correct":    correct,
                        })

                    except Exception as exc:
                        print(f"  [ERROR] {alg_name} / {inp_name} n={n} seed={seed}: {exc}")
                        records.append({
                            "alg":        alg_name,
                            "input":      inp_name,
                            "n":          n,
                            "seed":       seed,
                            "time_s":     None,
                            "comparisons":None,
                            "ops":        None,
                            "correct":    False,
                            "error":      str(exc),
                        })

                    done += 1
                    if done % 200 == 0:
                        pct = 100 * done / total
                        print(f"  {done}/{total}  ({pct:.0f}%)  last: "
                              f"{alg_name} / {inp_name} n={n}")

    print(f"  {done}/{total}  (100%)  done.\n")
    return records


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _filter(records, **kw):
    """Return records matching all keyword criteria."""
    out = records
    for k, v in kw.items():
        out = [r for r in out if r.get(k) == v]
    return out


def _mean(vals):
    valid = [v for v in vals if v is not None]
    return statistics.mean(valid) if valid else None


def _median(vals):
    valid = [v for v in vals if v is not None]
    return statistics.median(valid) if valid else None


# ─────────────────────────────────────────────────────────────────────────────
# Q1: Overall effectiveness ranking
# ─────────────────────────────────────────────────────────────────────────────

def q1_effectiveness(records):
    """
    Rank algorithms by mean comparison count at n=1024 across all input types
    and all seeds.  Also check if Bubble is consistently worst.
    """
    n = 1024
    print("=" * 70)
    print(f"Q1: OVERALL EFFECTIVENESS RANKING  (n={n}, mean over all inputs & seeds)")
    print("=" * 70)

    rows = []
    for alg in ALGORITHMS:
        recs = _filter(records, alg=alg, n=n)
        comps  = [r["comparisons"] for r in recs if r["comparisons"] is not None]
        times  = [r["time_s"]      for r in recs if r["time_s"] is not None]
        if not comps:
            continue
        rows.append((alg, _mean(comps), _mean(times), min(comps), max(comps)))

    rows.sort(key=lambda x: x[1])   # sort by mean comparisons

    print(f"\n  {'Rank':<5} {'Algorithm':<14} {'Mean Comps':>12} "
          f"{'Min Comps':>11} {'Max Comps':>11} {'Mean ms':>10}")
    print(f"  {'─'*65}")
    for rank, (alg, mc, mt, minc, maxc) in enumerate(rows, 1):
        ms = mt * 1000 if mt else 0
        print(f"  {rank:<5} {alg:<14} {mc:>12,.0f} {minc:>11,} {maxc:>11,} {ms:>10.3f}")

    # Is Bubble always last?
    alg_names = [r[0] for r in rows]
    bubble_rank = alg_names.index("Bubble") + 1 if "Bubble" in alg_names else None
    sel_rank    = alg_names.index("Selection") + 1 if "Selection" in alg_names else None

    print(f"\n  Bubble rank:    {bubble_rank} / {len(rows)}")
    print(f"  Selection rank: {sel_rank} / {len(rows)}")

    # Check per-input-type whether Bubble is ever not last
    print(f"\n  Per-input-type bottom 3 (by mean comparisons at n={n}):")
    for inp in GENERATORS:
        inp_rows = []
        for alg in ALGORITHMS:
            recs = _filter(records, alg=alg, input=inp, n=n)
            comps = [r["comparisons"] for r in recs if r["comparisons"] is not None]
            if comps:
                inp_rows.append((alg, _mean(comps)))
        inp_rows.sort(key=lambda x: x[1])
        bottom = inp_rows[-3:] if len(inp_rows) >= 3 else inp_rows
        bottom_names = [f"{a}({c:,.0f})" for a, c in reversed(bottom)]
        print(f"    {inp:<16}: worst→ {' > '.join(bottom_names)}")


# ─────────────────────────────────────────────────────────────────────────────
# Q2: Cases where any algorithm beats TimCustom
# ─────────────────────────────────────────────────────────────────────────────

def q2_timsort_upsets(records):
    """
    Find (alg, input_type, n, seed) combos where alg is faster than TimCustom.
    Group by (alg, input_type, n) and report fraction-of-seeds and mean speedup.
    """
    print("\n" + "=" * 70)
    print("Q2: INPUT CLASSES WHERE AN ALGORITHM OUTPERFORMS TimCustom")
    print("    (by wall-clock time; grouped by alg × input × n)")
    print("=" * 70)

    # Index Tim records: (input, n, seed) → time
    tim_times = {}
    for r in _filter(records, alg="Tim"):
        if r["time_s"] is not None:
            tim_times[(r["input"], r["n"], r["seed"])] = r["time_s"]

    upsets = defaultdict(list)   # (alg, input, n) → list of (speedup, seed)

    for r in records:
        if r["alg"] in ("Tim", ) or r["time_s"] is None:
            continue
        key = (r["input"], r["n"], r["seed"])
        tt = tim_times.get(key)
        if tt is None or tt == 0:
            continue
        if r["time_s"] < tt:
            speedup = tt / r["time_s"]
            upsets[(r["alg"], r["input"], r["n"])].append((speedup, r["seed"]))

    if not upsets:
        print("\n  No algorithm beat TimCustom in any trial.")
        return

    # Summarise: only show groups where Tim is beaten in ≥2 seeds (robust)
    summary = []
    for (alg, inp, n), entries in upsets.items():
        seeds_beaten = len(entries)
        mean_speedup = statistics.mean(s for s, _ in entries)
        max_speedup  = max(s for s, _ in entries)
        summary.append((alg, inp, n, seeds_beaten, mean_speedup, max_speedup,
                         sorted(sd for _, sd in entries)))

    summary.sort(key=lambda x: (-x[3], -x[4]))   # by seeds_beaten desc, then speedup

    robust = [s for s in summary if s[3] >= 2]
    occasional = [s for s in summary if s[3] == 1]

    if robust:
        print(f"\n  ROBUST UPSETS (beaten in ≥ 2 of {len(SEEDS)} seeds):")
        print(f"  {'Algorithm':<14} {'Input':<16} {'n':>6} "
              f"{'Seeds':>6} {'Mean×':>8} {'Max×':>8}  Seeds where beaten")
        print(f"  {'─'*75}")
        for alg, inp, n, sb, ms, mx, seed_list in robust:
            print(f"  {alg:<14} {inp:<16} {n:>6} {sb:>6} {ms:>8.3f} {mx:>8.3f}  {seed_list}")
    else:
        print("\n  No robust upsets (beaten in ≥2 seeds) found.")

    if occasional:
        print(f"\n  OCCASIONAL UPSETS (beaten in exactly 1 seed):")
        print(f"  {'Algorithm':<14} {'Input':<16} {'n':>6} {'Speedup':>8}  Seed")
        print(f"  {'─'*55}")
        for alg, inp, n, sb, ms, mx, seed_list in occasional[:20]:
            print(f"  {alg:<14} {inp:<16} {n:>6} {ms:>8.3f}  {seed_list[0]}")
        if len(occasional) > 20:
            print(f"  ... and {len(occasional)-20} more")

    # Also rank by comparison count (not wall time — more stable measure)
    print(f"\n  BY COMPARISON COUNT (more stable than wall time):")
    tim_comps = {}
    for r in _filter(records, alg="Tim"):
        if r["comparisons"] is not None:
            tim_comps[(r["input"], r["n"], r["seed"])] = r["comparisons"]

    comp_upsets = defaultdict(list)
    for r in records:
        if r["alg"] == "Tim" or r["comparisons"] is None:
            continue
        key = (r["input"], r["n"], r["seed"])
        tc = tim_comps.get(key)
        if tc is None or tc == 0 or r["comparisons"] == 0:
            continue
        if r["comparisons"] < tc:
            comp_upsets[(r["alg"], r["input"], r["n"])].append(
                (tc / r["comparisons"], r["seed"]))

    comp_summary = []
    for (alg, inp, n), entries in comp_upsets.items():
        if len(entries) >= len(SEEDS) // 2:   # beaten in majority of seeds
            mean_ratio = statistics.mean(s for s, _ in entries)
            comp_summary.append((alg, inp, n, len(entries), mean_ratio))
    comp_summary.sort(key=lambda x: (-x[3], -x[4]))

    if comp_summary:
        print(f"  {'Algorithm':<14} {'Input':<16} {'n':>6} "
              f"{'Seeds':>6} {'Mean ratio':>12}")
        print(f"  {'─'*58}")
        for alg, inp, n, sb, mr in comp_summary:
            print(f"  {alg:<14} {inp:<16} {n:>6} {sb:>6} {mr:>12.3f}")
        print(f"  (Radix has 0 comparisons by design — excluded from ratio.)")
    else:
        print(f"  No algorithm consistently beats Tim on comparison count.")


# ─────────────────────────────────────────────────────────────────────────────
# Q3: Hybrid algorithm analysis
# ─────────────────────────────────────────────────────────────────────────────

def q3_hybrids(records):
    """
    Compare hybrid algorithms against their pure parents and TimCustom.
    """
    print("\n" + "=" * 70)
    print("Q3: HYBRID ALGORITHM EFFECTIVENESS")
    print("    (mean comparisons at n=1024, all inputs & seeds)")
    print("=" * 70)

    hybrids = {
        "Hybrid_QI":    ("Quick",     "Insertion"),
        "Hybrid_MI":    ("Merge",     "Insertion"),
        "Hybrid_RI":    ("Radix",     "Insertion"),
        "Hybrid_Intro": ("Quick",     "Heap"),
    }

    n = 1024

    # Build mean comparison table for n=1024 per input type
    def _mean_comps(alg, inp):
        recs = _filter(records, alg=alg, input=inp, n=n)
        vals = [r["comparisons"] for r in recs if r["comparisons"] is not None]
        return _mean(vals)

    def _mean_time(alg, inp):
        recs = _filter(records, alg=alg, input=inp, n=n)
        vals = [r["time_s"] for r in recs if r["time_s"] is not None]
        return _mean(vals)

    print(f"\n  For each hybrid: comparison count vs. both parents and Tim (n={n})")
    print(f"  Values are mean comparisons over all {len(SEEDS)} seeds × all input types.")
    print()

    for hybrid, (parent1, parent2) in hybrids.items():
        print(f"  {'─'*65}")
        print(f"  {hybrid}  (combines {parent1} + {parent2})")
        print(f"  {'Input':<16} {hybrid:>12} {parent1:>12} {parent2:>12} {'Tim':>12}  {'Winner':>10}")
        print(f"  {'─'*65}")

        wins_vs_p1 = wins_vs_p2 = wins_vs_tim = 0
        total_inp = 0

        for inp in GENERATORS:
            hc = _mean_comps(hybrid, inp)
            p1c = _mean_comps(parent1, inp)
            p2c = _mean_comps(parent2, inp)
            timc = _mean_comps("Tim", inp)

            if hc is None:
                continue
            total_inp += 1

            candidates = [(hybrid, hc), (parent1, p1c), (parent2, p2c), ("Tim", timc)]
            candidates = [(a, v) for a, v in candidates if v is not None]
            if not candidates:
                continue
            winner = min(candidates, key=lambda x: x[1])[0]

            if p1c is not None and hc < p1c:  wins_vs_p1 += 1
            if p2c is not None and hc < p2c:  wins_vs_p2 += 1
            if timc is not None and hc < timc: wins_vs_tim += 1

            def _fmt(v): return f"{v:>12,.0f}" if v is not None else f"{'N/A':>12}"
            print(f"  {inp:<16} {_fmt(hc)} {_fmt(p1c)} {_fmt(p2c)} {_fmt(timc)}  {winner:>10}")

        print(f"\n  {hybrid} beats {parent1}: {wins_vs_p1}/{total_inp} input types")
        print(f"  {hybrid} beats {parent2}: {wins_vs_p2}/{total_inp} input types")
        print(f"  {hybrid} beats Tim:    {wins_vs_tim}/{total_inp} input types")
        print()


# ─────────────────────────────────────────────────────────────────────────────
# Bonus: per-input-type profile for small n vs large n
# ─────────────────────────────────────────────────────────────────────────────

def profile_by_input(records):
    """
    For each input type, show which algorithm wins at each size.
    Uses mean comparison count as the primary metric.
    """
    print("=" * 70)
    print("BONUS: BEST ALGORITHM PER INPUT TYPE × SIZE  (by mean comparisons)")
    print("=" * 70)
    print(f"\n  {'Input':<16}", end="")
    for n in SIZES:
        print(f"  {'n='+str(n):>10}", end="")
    print()
    print("  " + "─" * (16 + 13 * len(SIZES)))

    for inp in GENERATORS:
        print(f"  {inp:<16}", end="")
        for n in SIZES:
            best_alg = None
            best_mean = None
            for alg in ALGORITHMS:
                if alg in SLOW_ALGS and n > SLOW_MAX:
                    continue
                recs = _filter(records, alg=alg, input=inp, n=n)
                vals = [r["comparisons"] for r in recs if r["comparisons"] is not None]
                if not vals:
                    continue
                m = statistics.mean(vals)
                if best_mean is None or m < best_mean:
                    best_mean = m
                    best_alg = alg
            label = best_alg or "—"
            print(f"  {label:>10}", end="")
        print()


# ─────────────────────────────────────────────────────────────────────────────
# Correctness summary
# ─────────────────────────────────────────────────────────────────────────────

def correctness_summary(records):
    print("\n" + "=" * 70)
    print("CORRECTNESS SUMMARY")
    print("=" * 70)
    total   = len(records)
    correct = sum(1 for r in records if r.get("correct"))
    errors  = sum(1 for r in records if "error" in r)
    wrong   = total - correct - errors

    print(f"\n  Total trials : {total}")
    print(f"  Correct      : {correct}  ({100*correct/total:.1f}%)")
    print(f"  Wrong output : {wrong}")
    print(f"  Exceptions   : {errors}")

    if wrong or errors:
        print("\n  Failures:")
        for r in records:
            if not r.get("correct") or "error" in r:
                print(f"    {r['alg']} / {r['input']} n={r['n']} seed={r['seed']}: "
                      f"{r.get('error', 'wrong output')}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("SORT TEST BATTERY")
    print(f"Seeds: {SEEDS}")
    print(f"Sizes: {SIZES}  (O(n²) capped at n={SLOW_MAX})")
    print("=" * 70 + "\n")

    records = run_battery()

    # Persist results
    manifest = {
        "seeds":      SEEDS,
        "sizes":      SIZES,
        "slow_max":   SLOW_MAX,
        "algorithms": list(ALGORITHMS.keys()),
        "generators": list(GENERATORS.keys()),
        "records":    records,
    }
    out_path = "src/test_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Full results written to {out_path}\n")

    correctness_summary(records)
    print()
    q1_effectiveness(records)
    print()
    q2_timsort_upsets(records)
    print()
    q3_hybrids(records)
    print()
    profile_by_input(records)


if __name__ == "__main__":
    main()
