"""
triplet_test.py — Systematic triplet hybrid sort battery.

Generates every (outer, mid, inner) combination from the algorithm sets:
  outer ∈ {Quick, Merge}
  mid   ∈ {Quick, Merge, Heap, Insertion, Selection, Radix}
  inner ∈ {Insertion, Selection, Bubble}

Each triplet dispatches by subarray size:
  n > HIGH_CUT  → outer algorithm (recurses via do_outer)
  LOW_CUT < n ≤ HIGH_CUT → mid algorithm (recurses via do_mid for recursive mids)
  n ≤ LOW_CUT   → inner algorithm (direct, in-place)

Thresholds: HIGH_CUT=128, LOW_CUT=16

Results are written to src/triplet_results.json and printed as raw tables.
No algorithm is highlighted or analysed here — output only.
"""

import sys
import time
import json
import statistics
from collections import defaultdict

sys.setrecursionlimit(200_000)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from benchmark_deep import (
    gen_random, gen_sorted, gen_reverse, gen_nearly_sorted,
    gen_few_unique, gen_sawtooth, gen_pipe_organ, gen_all_same,
    gen_two_values, gen_interleaved, gen_rotated,
    gen_random_blocks, gen_killer_quick,
)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration — identical seeds / sizes as sort_test.py
# ─────────────────────────────────────────────────────────────────────────────

SEEDS     = [42, 137, 1618, 2718, 3141, 9973, 31337, 65537]
SIZES     = [64, 256, 1024]

HIGH_CUT  = 128   # outer → mid threshold
LOW_CUT   = 16    # mid   → inner threshold

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

OUTER_NAMES = ["Quick", "Merge"]
MID_NAMES   = ["Quick", "Merge", "Heap", "Insertion", "Selection", "Radix"]
INNER_NAMES = ["Insertion", "Selection", "Bubble"]

# ─────────────────────────────────────────────────────────────────────────────
# Triplet hybrid factory
# ─────────────────────────────────────────────────────────────────────────────

def make_triplet(outer, mid, inner, high_cut=HIGH_CUT, low_cut=LOW_CUT):
    """
    Return an instrumented sort function for the (outer, mid, inner) triplet.
    Returns (sort_fn, display_name).
    """
    short = {"Quick": "Q", "Merge": "M", "Heap": "H",
             "Insertion": "I", "Selection": "S", "Bubble": "B", "Radix": "R"}
    name = f"T_{short[outer]}{short[mid]}{short[inner]}"

    def sort_fn(arr):
        a   = arr[:]
        n   = len(a)
        c   = [0]   # comparisons
        o   = [0]   # ops (swaps / moves)

        # ── helpers ──────────────────────────────────────────────────────

        def ins_range(lo, hi):
            for i in range(lo + 1, hi + 1):
                key = a[i]; j = i - 1
                while j >= lo:
                    c[0] += 1
                    if a[j] > key: a[j + 1] = a[j]; o[0] += 1; j -= 1
                    else: break
                a[j + 1] = key

        def sel_range(lo, hi):
            for i in range(lo, hi + 1):
                mi = i
                for j in range(i + 1, hi + 1):
                    c[0] += 1
                    if a[j] < a[mi]: mi = j
                if mi != i: a[i], a[mi] = a[mi], a[i]; o[0] += 1

        def bub_range(lo, hi):
            for i in range(lo, hi + 1):
                swapped = False
                for j in range(lo, hi - (i - lo)):
                    c[0] += 1
                    if a[j] > a[j + 1]:
                        a[j], a[j + 1] = a[j + 1], a[j]; o[0] += 1; swapped = True
                if not swapped: break

        def do_merge(lo, m, hi):
            L = a[lo:m + 1]; R = a[m + 1:hi + 1]
            i = j = 0; k = lo
            while i < len(L) and j < len(R):
                c[0] += 1
                if L[i] <= R[j]: a[k] = L[i]; i += 1
                else:             a[k] = R[j]; j += 1
                o[0] += 1; k += 1
            while i < len(L): a[k] = L[i]; i += 1; o[0] += 1; k += 1
            while j < len(R): a[k] = R[j]; j += 1; o[0] += 1; k += 1

        def partition(lo, hi):
            # median-of-3 pivot placed at hi-1
            m = (lo + hi) // 2
            c[0] += 2
            if a[lo] > a[m]:      a[lo], a[m]      = a[m], a[lo];      o[0] += 1
            if a[lo] > a[hi]:     a[lo], a[hi]     = a[hi], a[lo];     o[0] += 1
            if a[m]  > a[hi]:     a[m],  a[hi]     = a[hi], a[m];      o[0] += 1
            a[m], a[hi - 1] = a[hi - 1], a[m]; o[0] += 1
            pivot = a[hi - 1]
            i = lo; j = hi - 1
            while True:
                i += 1
                while i <= hi - 1:
                    c[0] += 1
                    if a[i] < pivot: i += 1
                    else: break
                j -= 1
                while j >= lo:
                    c[0] += 1
                    if a[j] > pivot: j -= 1
                    else: break
                if i >= j: break
                a[i], a[j] = a[j], a[i]; o[0] += 1
            a[i], a[hi - 1] = a[hi - 1], a[i]; o[0] += 1
            return i

        def heapsort_range(lo, hi):
            sub = a[lo:hi + 1]
            ns = len(sub)
            def sift(s, root, end):
                while True:
                    child = 2 * root + 1
                    if child > end: break
                    if child + 1 <= end:
                        c[0] += 1
                        if s[child] < s[child + 1]: child += 1
                    c[0] += 1
                    if s[root] < s[child]:
                        s[root], s[child] = s[child], s[root]; o[0] += 1; root = child
                    else: break
            for start in range((ns - 2) // 2, -1, -1):
                sift(sub, start, ns - 1)
            for end in range(ns - 1, 0, -1):
                sub[0], sub[end] = sub[end], sub[0]; o[0] += 1
                sift(sub, 0, end - 1)
            a[lo:hi + 1] = sub

        def radix_range(lo, hi):
            sub = a[lo:hi + 1]
            if not sub: return
            mx = max(sub)
            if mx <= 0: return
            exp = 1
            while mx // exp > 0:
                out = [0] * len(sub)
                cnt = [0] * 10
                for v in sub: cnt[(v // exp) % 10] += 1
                for k in range(1, 10): cnt[k] += cnt[k - 1]
                for k in range(len(sub) - 1, -1, -1):
                    d = (sub[k] // exp) % 10
                    cnt[d] -= 1; out[cnt[d]] = sub[k]; o[0] += 1
                sub = out; exp *= 10
            a[lo:hi + 1] = sub

        # ── inner (always direct) ─────────────────────────────────────────

        def do_inner(lo, hi):
            if inner == "Insertion": ins_range(lo, hi)
            elif inner == "Selection": sel_range(lo, hi)
            else:                      bub_range(lo, hi)

        # ── mid (uses do_inner as its own base case) ──────────────────────

        def do_mid(lo, hi):
            size = hi - lo + 1
            if size <= 1: return
            if size <= low_cut: do_inner(lo, hi); return
            if mid == "Insertion": ins_range(lo, hi)
            elif mid == "Selection": sel_range(lo, hi)
            elif mid == "Heap":   heapsort_range(lo, hi)
            elif mid == "Radix":  radix_range(lo, hi)
            elif mid == "Merge":
                m = (lo + hi) // 2
                do_mid(lo, m); do_mid(m + 1, hi); do_merge(lo, m, hi)
            elif mid == "Quick":
                if size == 2:
                    c[0] += 1
                    if a[lo] > a[hi]: a[lo], a[hi] = a[hi], a[lo]; o[0] += 1
                    return
                p = partition(lo, hi)
                do_mid(lo, p - 1); do_mid(p + 1, hi)

        # ── outer (recurses; switches to do_mid at HIGH_CUT) ──────────────

        def do_outer(lo, hi):
            size = hi - lo + 1
            if size <= 1: return
            if size <= low_cut:  do_inner(lo, hi); return
            if size <= high_cut: do_mid(lo, hi);   return
            if outer == "Quick":
                if size == 2:
                    c[0] += 1
                    if a[lo] > a[hi]: a[lo], a[hi] = a[hi], a[lo]; o[0] += 1
                    return
                p = partition(lo, hi)
                do_outer(lo, p - 1); do_outer(p + 1, hi)
            elif outer == "Merge":
                m = (lo + hi) // 2
                do_outer(lo, m); do_outer(m + 1, hi); do_merge(lo, m, hi)

        if n > 1:
            do_outer(0, n - 1)
        return a, c[0], o[0]

    sort_fn.__name__ = name
    return sort_fn, name


# ─────────────────────────────────────────────────────────────────────────────
# Build the full triplet catalogue
# ─────────────────────────────────────────────────────────────────────────────

TRIPLETS = {}   # name → sort_fn
for _o in OUTER_NAMES:
    for _m in MID_NAMES:
        for _i in INNER_NAMES:
            _fn, _nm = make_triplet(_o, _m, _i)
            TRIPLETS[_nm] = _fn

# ─────────────────────────────────────────────────────────────────────────────
# Battery runner
# ─────────────────────────────────────────────────────────────────────────────

def run_battery():
    total = len(TRIPLETS) * len(GENERATORS) * len(SIZES) * len(SEEDS)
    print(f"Triplet battery: {len(TRIPLETS)} algorithms × {len(GENERATORS)} input types "
          f"× {len(SIZES)} sizes × {len(SEEDS)} seeds")
    print(f"Total trials: {total}")
    print()

    records = []
    done = 0

    for alg_name, alg_fn in TRIPLETS.items():
        for inp_name, gen_fn in GENERATORS.items():
            for n in SIZES:
                for seed in SEEDS:
                    arr = gen_fn(n, seed=seed)
                    expected = sorted(arr)
                    try:
                        t0 = time.perf_counter()
                        result_arr, comps, ops = alg_fn(arr)
                        elapsed = time.perf_counter() - t0
                        correct = (result_arr == expected)
                        if not correct:
                            print(f"  [FAIL] {alg_name} / {inp_name} n={n} seed={seed}")
                        records.append({
                            "alg": alg_name, "input": inp_name, "n": n, "seed": seed,
                            "time_s": elapsed, "comparisons": comps, "ops": ops,
                            "correct": correct,
                        })
                    except Exception as exc:
                        print(f"  [ERROR] {alg_name} / {inp_name} n={n} seed={seed}: {exc}")
                        records.append({
                            "alg": alg_name, "input": inp_name, "n": n, "seed": seed,
                            "time_s": None, "comparisons": None, "ops": None,
                            "correct": False, "error": str(exc),
                        })
                    done += 1
                    if done % 2000 == 0:
                        print(f"  {done}/{total}  ({100*done//total}%)")

    print(f"  {done}/{total}  (100%)  done.\n")
    return records

# ─────────────────────────────────────────────────────────────────────────────
# Raw output — no analysis, no winners called out
# ─────────────────────────────────────────────────────────────────────────────

def _filter(records, **kw):
    out = records
    for k, v in kw.items():
        out = [r for r in out if r.get(k) == v]
    return out

def _mean(vals):
    v = [x for x in vals if x is not None]
    return statistics.mean(v) if v else None

def print_raw_tables(records):
    """
    Print raw mean-comparison and mean-time tables.
    Rows = algorithms, columns = input types.  One table per size.
    No analysis, no rankings called out.
    """
    alg_names = list(TRIPLETS.keys())
    inp_names  = list(GENERATORS.keys())

    for n in SIZES:
        print("=" * 140)
        print(f"RAW MEAN COMPARISONS  n={n}  (mean over {len(SEEDS)} seeds)")
        print("=" * 140)

        # header
        col = 12
        hdr = f"  {'Algorithm':<10}"
        for inp in inp_names:
            hdr += f"  {inp[:10]:>10}"
        hdr += f"  {'MEAN':>10}"
        print(hdr)
        print("  " + "─" * (len(hdr) - 2))

        for alg in alg_names:
            row_vals = []
            row = f"  {alg:<10}"
            for inp in inp_names:
                recs = _filter(records, alg=alg, input=inp, n=n)
                vals = [r["comparisons"] for r in recs if r["comparisons"] is not None]
                m = _mean(vals)
                row_vals.append(m)
                if m is None:
                    row += f"  {'—':>10}"
                else:
                    row += f"  {m:>10,.0f}"
            overall = _mean(row_vals)
            row += f"  {overall:>10,.0f}" if overall is not None else f"  {'—':>10}"
            print(row)
        print()

    for n in SIZES:
        print("=" * 140)
        print(f"RAW MEAN WALL TIME (ms)  n={n}  (mean over {len(SEEDS)} seeds)")
        print("=" * 140)

        hdr = f"  {'Algorithm':<10}"
        for inp in inp_names:
            hdr += f"  {inp[:10]:>10}"
        hdr += f"  {'MEAN':>10}"
        print(hdr)
        print("  " + "─" * (len(hdr) - 2))

        for alg in alg_names:
            row_vals = []
            row = f"  {alg:<10}"
            for inp in inp_names:
                recs = _filter(records, alg=alg, input=inp, n=n)
                vals = [r["time_s"] for r in recs if r["time_s"] is not None]
                m = _mean(vals)
                row_vals.append(m)
                if m is None:
                    row += f"  {'—':>10}"
                else:
                    row += f"  {m*1000:>10.3f}"
            overall = _mean(row_vals)
            row += f"  {overall*1000:>10.3f}" if overall is not None else f"  {'—':>10}"
            print(row)
        print()

def print_correctness(records):
    total   = len(records)
    correct = sum(1 for r in records if r.get("correct"))
    errors  = [r for r in records if "error" in r]
    wrong   = [r for r in records if not r.get("correct") and "error" not in r]

    print("=" * 60)
    print("CORRECTNESS")
    print("=" * 60)
    print(f"  Total  : {total}")
    print(f"  Correct: {correct}  ({100*correct/total:.1f}%)")
    if wrong:
        print(f"  Wrong  : {len(wrong)}")
        for r in wrong:
            print(f"    {r['alg']} / {r['input']} n={r['n']} seed={r['seed']}")
    if errors:
        print(f"  Errors : {len(errors)}")
        for r in errors:
            print(f"    {r['alg']} / {r['input']} n={r['n']} seed={r['seed']}: {r['error']}")
    print()

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("TRIPLET HYBRID SORT BATTERY")
    print(f"HIGH_CUT={HIGH_CUT}  LOW_CUT={LOW_CUT}")
    print(f"Seeds: {SEEDS}")
    print(f"Sizes: {SIZES}")
    print(f"Triplets: {len(TRIPLETS)}")
    print("=" * 60)
    print()
    print("Key:")
    for _o in OUTER_NAMES:
        for _m in MID_NAMES:
            for _i in INNER_NAMES:
                short = {"Quick": "Q", "Merge": "M", "Heap": "H",
                         "Insertion": "I", "Selection": "S",
                         "Bubble": "B", "Radix": "R"}
                nm = f"T_{short[_o]}{short[_m]}{short[_i]}"
                print(f"  {nm}  =  outer:{_o}  mid:{_m}  inner:{_i}")
    print()

    records = run_battery()

    manifest = {
        "high_cut": HIGH_CUT, "low_cut": LOW_CUT,
        "seeds": SEEDS, "sizes": SIZES,
        "triplets": {nm: {"outer": nm[2], "mid": nm[3], "inner": nm[4]}
                     for nm in TRIPLETS},
        "records": records,
    }
    out_path = "src/triplet_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Full results written to {out_path}\n")

    print_correctness(records)
    print_raw_tables(records)


if __name__ == "__main__":
    main()
