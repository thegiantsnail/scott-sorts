"""
batch_export.py — Command-line batch runner for all 48 sort algorithms.

Runs every requested algorithm across every (input_class, size, seed)
combination, records comparison counts and wall-clock time, then exports
results as CSV and/or JSON.

Usage examples
--------------
  # Quick sanity check: all base algorithms, two sizes, one seed
  python batch_export.py --algos base --sizes 64,256 --seeds 42

  # Full 12k-operation suite (all 48 algos x 13 inputs x 3 sizes x 8 seeds)
  python batch_export.py --algos all --out results/full_12k

  # Triplets only, random + reverse inputs, export JSON
  python batch_export.py --algos triplets --inputs random,reverse --format json

  # Single algorithm family comparison
  python batch_export.py --algos hybrids,base --sizes 1024 --seeds 42,137,1618

Flags
-----
  --algos   Comma-separated subset of: base, hybrids, triplets, all
            (default: all)
  --sizes   Comma-separated list of array sizes     (default: 64,256,1024)
  --seeds   Comma-separated list of RNG seeds       (default: 42,137,1618,2718,3141,9973,31337,65537)
  --inputs  Comma-separated input-class names or "all"  (default: all)
  --out     Output path prefix (no extension)        (default: src/batch_results)
  --format  csv, json, or both                       (default: both)
  --trials  Repetitions per (algo, input, size, seed) for timing  (default: 3)
  --no-slow Skip O(n²) algorithms (Bubble, Selection) for n > 512 (default: on)

Output schema
-------------
  Each record:
    algo        algorithm name  e.g. "Quick", "T_QMI", "Hybrid_QI"
    group       "base" | "hybrid" | "triplet"
    input       input-class name  e.g. "random"
    n           array size
    seed        RNG seed
    comps       comparison count
    moves       move/swap count
    wall_ms     median wall time in milliseconds (best of --trials)
    correct     bool — sorted == expected
"""

import sys
import os
import json
import csv
import time
import argparse
import statistics
import itertools

sys.setrecursionlimit(500_000)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ---------------------------------------------------------------------------
# Import shared sort implementations and generators
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from benchmark_deep import (
    bubble_sort, insertion_sort, selection_sort,
    merge_sort, quick_sort, heap_sort, radix_sort, tim_custom,
    hybrid_qi, hybrid_mi, hybrid_ri, hybrid_intro,
    gen_random, gen_sorted, gen_reverse, gen_nearly_sorted,
    gen_few_unique, gen_sawtooth, gen_pipe_organ, gen_all_same,
    gen_two_values, gen_interleaved, gen_rotated,
    gen_random_blocks, gen_killer_quick,
)
from triplet_test import make_triplet

# ---------------------------------------------------------------------------
# Algorithm registry
# ---------------------------------------------------------------------------

BASE_ALGORITHMS = {
    "Bubble":     ("base", bubble_sort),
    "Insertion":  ("base", insertion_sort),
    "Selection":  ("base", selection_sort),
    "Merge":      ("base", merge_sort),
    "Quick":      ("base", quick_sort),
    "Heap":       ("base", heap_sort),
    "Radix":      ("base", radix_sort),
    "TimCustom":  ("base", tim_custom),
}

HYBRID_ALGORITHMS = {
    "Hybrid_QI":    ("hybrid", hybrid_qi),
    "Hybrid_MI":    ("hybrid", hybrid_mi),
    "Hybrid_RI":    ("hybrid", hybrid_ri),
    "Hybrid_Intro": ("hybrid", hybrid_intro),
}

# Build the full 36-triplet registry: T_{outer}{mid}{inner}
_SHORT = {"Quick": "Q", "Merge": "M", "Heap": "H",
          "Insertion": "I", "Selection": "S", "Bubble": "B", "Radix": "R"}
_OUTER = ["Quick", "Merge"]
_MID   = ["Quick", "Merge", "Heap", "Insertion", "Selection", "Radix"]
_INNER = ["Insertion", "Selection", "Bubble"]

TRIPLET_ALGORITHMS = {}
for _o, _m, _i in itertools.product(_OUTER, _MID, _INNER):
    _name = f"T_{_SHORT[_o]}{_SHORT[_m]}{_SHORT[_i]}"
    _fn, _ = make_triplet(_o, _m, _i)
    TRIPLET_ALGORITHMS[_name] = ("triplet", _fn)

# Total: 8 + 4 + 36 = 48
ALL_ALGORITHMS = {**BASE_ALGORITHMS, **HYBRID_ALGORITHMS, **TRIPLET_ALGORITHMS}

# ---------------------------------------------------------------------------
# Input-class registry
# ---------------------------------------------------------------------------

ALL_GENERATORS = {
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

# O(n²) algorithms to skip for large n when --no-slow
SLOW_ALGS = {"Bubble", "Selection"}

# ---------------------------------------------------------------------------
# Benchmarking helpers
# ---------------------------------------------------------------------------

def _run_sort(fn, arr):
    """
    Run fn on a copy of arr.  Returns (comps, moves, wall_ms, correct).

    All sort functions in this project return a 3-tuple:
        (sorted_list, comparisons: int, moves: int)
    Falls back gracefully to dict-style or plain list returns.
    """
    data = list(arr)
    expected = sorted(arr)
    t0 = time.perf_counter()
    result = fn(data)
    wall_ms = (time.perf_counter() - t0) * 1000.0

    if isinstance(result, tuple) and len(result) == 3:
        sorted_arr, comps, moves = result
    elif isinstance(result, dict):
        comps      = result.get('comparisons', 0)
        moves      = result.get('moves', 0)
        sorted_arr = result.get('sorted', data)
    elif isinstance(result, list):
        sorted_arr = result
        comps = moves = 0
    else:
        # fn mutated data in-place
        sorted_arr = data
        comps = moves = 0

    correct = (sorted_arr == expected)
    return comps, moves, wall_ms, correct


def run_trial(fn, arr, trials=3):
    """
    Run fn `trials` times, return median timing + comps from first run.
    """
    comps, moves, _, correct = _run_sort(fn, arr)
    times = []
    for _ in range(trials):
        _, _, wms, _ = _run_sort(fn, arr)
        times.append(wms)
    return comps, moves, statistics.median(times), correct


# ---------------------------------------------------------------------------
# Main batch runner
# ---------------------------------------------------------------------------

def build_algo_set(algos_arg):
    """Resolve --algos argument to a dict of {name: (group, fn)}."""
    chosen = {}
    for token in algos_arg.split(','):
        token = token.strip().lower()
        if token == 'all':
            chosen.update(ALL_ALGORITHMS)
        elif token == 'base':
            chosen.update(BASE_ALGORITHMS)
        elif token in ('hybrid', 'hybrids'):
            chosen.update(HYBRID_ALGORITHMS)
        elif token in ('triplet', 'triplets'):
            chosen.update(TRIPLET_ALGORITHMS)
        else:
            # Maybe a direct algorithm name
            for name, val in ALL_ALGORITHMS.items():
                if name.lower() == token:
                    chosen[name] = val
                    break
            else:
                print(f"  Warning: unknown algo token '{token}', skipping.", file=sys.stderr)
    return chosen


def build_input_set(inputs_arg):
    """Resolve --inputs argument to a dict of {name: gen_fn}."""
    if inputs_arg.strip().lower() == 'all':
        return dict(ALL_GENERATORS)
    chosen = {}
    for token in inputs_arg.split(','):
        token = token.strip()
        if token in ALL_GENERATORS:
            chosen[token] = ALL_GENERATORS[token]
        else:
            print(f"  Warning: unknown input class '{token}', skipping.", file=sys.stderr)
    return chosen


def batch_run(algos, inputs, sizes, seeds, trials=3, skip_slow_large=True):
    """
    Run the full combinatorial suite.

    Returns list of record dicts (schema matches module docstring).
    """
    records = []
    total = len(algos) * len(inputs) * len(sizes) * len(seeds)
    done  = 0

    print(f"\nBatch run: {len(algos)} algos × {len(inputs)} inputs × "
          f"{len(sizes)} sizes × {len(seeds)} seeds = {total} cells "
          f"({trials} trial(s) each)\n")

    for size in sorted(sizes):
        for input_name, gen_fn in sorted(inputs.items()):
            # Pre-generate arrays for each seed so all algos see identical input
            arrays = {seed: gen_fn(size, seed=seed) for seed in seeds}

            for algo_name, (group, fn) in sorted(algos.items()):
                # Skip O(n²) for large n
                if skip_slow_large and algo_name in SLOW_ALGS and size > 512:
                    for seed in seeds:
                        records.append({
                            "algo":    algo_name,
                            "group":   group,
                            "input":   input_name,
                            "n":       size,
                            "seed":    seed,
                            "comps":   None,
                            "moves":   None,
                            "wall_ms": None,
                            "correct": None,
                            "skipped": True,
                        })
                        done += 1
                    continue

                for seed in seeds:
                    arr = arrays[seed]
                    try:
                        comps, moves, wall_ms, correct = run_trial(fn, arr, trials)
                        records.append({
                            "algo":    algo_name,
                            "group":   group,
                            "input":   input_name,
                            "n":       size,
                            "seed":    seed,
                            "comps":   comps,
                            "moves":   moves,
                            "wall_ms": round(wall_ms, 4),
                            "correct": correct,
                            "skipped": False,
                        })
                    except Exception as exc:
                        records.append({
                            "algo":    algo_name,
                            "group":   group,
                            "input":   input_name,
                            "n":       size,
                            "seed":    seed,
                            "comps":   None,
                            "moves":   None,
                            "wall_ms": None,
                            "correct": False,
                            "skipped": False,
                            "error":   str(exc),
                        })

                    done += 1
                    if done % 200 == 0 or done == total:
                        pct = 100 * done / total
                        print(f"  {done}/{total} ({pct:.1f}%)  "
                              f"[{algo_name}, {input_name}, n={size}, seed={seed}]",
                              flush=True)

    return records


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

_CSV_FIELDS = ["algo", "group", "input", "n", "seed",
               "comps", "moves", "wall_ms", "correct", "skipped"]


def export_csv(records, path):
    """Write records to a CSV file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
    print(f"  CSV  → {os.path.abspath(path)}")


def export_json(records, path):
    """Write records to a JSON file (pretty-printed)."""
    os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    print(f"  JSON → {os.path.abspath(path)}")


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def print_summary(records, top_n=10):
    """Print a brief leaderboard (median wall_ms across all seeds/inputs) per algo."""
    from collections import defaultdict
    times_by_algo = defaultdict(list)
    correct_by_algo = defaultdict(list)

    for r in records:
        if r.get('skipped') or r.get('wall_ms') is None:
            continue
        times_by_algo[r['algo']].append(r['wall_ms'])
        if r.get('correct') is not None:
            correct_by_algo[r['algo']].append(r['correct'])

    if not times_by_algo:
        print("  (no timing data)")
        return

    rows = []
    for algo, times in times_by_algo.items():
        med = statistics.median(times)
        ok  = all(correct_by_algo.get(algo, [True]))
        rows.append((med, algo, len(times), ok))
    rows.sort()

    print(f"\n{'Rank':<5} {'Algorithm':<18} {'Median ms':>10} {'Trials':>7} {'Correct':>8}")
    print("-" * 55)
    for rank, (med, algo, n, ok) in enumerate(rows[:top_n], 1):
        flag = "" if ok else " ✗"
        print(f"{rank:<5} {algo:<18} {med:>10.4f} {n:>7} {'yes' if ok else 'NO':>8}{flag}")

    if len(rows) > top_n:
        print(f"  ... and {len(rows) - top_n} more (use --format to see full export)")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Batch-benchmark all 48 sort algorithms and export results.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument('--algos',    default='all',
                   help='Comma-separated: base, hybrids, triplets, all (default: all)')
    p.add_argument('--sizes',    default='64,256,1024',
                   help='Comma-separated array sizes (default: 64,256,1024)')
    p.add_argument('--seeds',    default='42,137,1618,2718,3141,9973,31337,65537',
                   help='Comma-separated RNG seeds (default: 8 standard seeds)')
    p.add_argument('--inputs',   default='all',
                   help='Comma-separated input classes or "all" (default: all)')
    p.add_argument('--out',      default='src/batch_results',
                   help='Output file prefix, no extension (default: src/batch_results)')
    p.add_argument('--format',   default='both',
                   choices=['csv', 'json', 'both'],
                   help='Export format: csv | json | both (default: both)')
    p.add_argument('--trials',   type=int, default=3,
                   help='Timing repetitions per cell (default: 3)')
    p.add_argument('--no-slow',  action='store_true', default=True,
                   dest='no_slow',
                   help='Skip O(n²) algorithms for n>512 (default: on)')
    p.add_argument('--allow-slow', action='store_false', dest='no_slow',
                   help='Include O(n²) algorithms at all sizes')
    p.add_argument('--top',      type=int, default=10,
                   help='Rows to show in summary table (default: 10)')
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    algos  = build_algo_set(args.algos)
    inputs = build_input_set(args.inputs)
    sizes  = [int(s.strip()) for s in args.sizes.split(',')]
    seeds  = [int(s.strip()) for s in args.seeds.split(',')]

    if not algos:
        print("Error: no algorithms selected.", file=sys.stderr)
        sys.exit(1)
    if not inputs:
        print("Error: no input classes selected.", file=sys.stderr)
        sys.exit(1)

    print(f"Algorithms ({len(algos)}): {', '.join(sorted(algos))}")
    print(f"Input classes ({len(inputs)}): {', '.join(sorted(inputs))}")
    print(f"Sizes: {sizes}")
    print(f"Seeds: {seeds}")
    print(f"Trials per cell: {args.trials}")
    print(f"Skip slow for n>512: {args.no_slow}")

    records = batch_run(
        algos, inputs, sizes, seeds,
        trials=args.trials,
        skip_slow_large=args.no_slow,
    )

    # Export
    print(f"\nExporting {len(records)} records …")
    if args.format in ('csv', 'both'):
        export_csv(records, args.out + '.csv')
    if args.format in ('json', 'both'):
        export_json(records, args.out + '.json')

    # Print summary
    print_summary(records, top_n=args.top)

    # Correctness check
    failures = [r for r in records if r.get('correct') is False and not r.get('skipped')]
    if failures:
        print(f"\n  WARNING: {len(failures)} incorrect result(s):")
        for r in failures[:5]:
            print(f"    {r['algo']} / {r['input']} / n={r['n']} / seed={r['seed']}")
    else:
        ok_count = sum(1 for r in records if r.get('correct') is True)
        print(f"\n  All {ok_count} executed cells sorted correctly.")

    return records


if __name__ == '__main__':
    main()
