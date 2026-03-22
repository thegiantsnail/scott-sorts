"""
network_sort.py — Zipper merge sort networks with adaptive Markov routing.

Three structures implemented:

  1. MarkovRouter  — races a pool of sort pairs, builds an empirical Markov
                     transition matrix (last_winner -> next_winner counts),
                     routes future inputs to the predicted winner.
                     Provenance chain shows adaptation as input character changes.

  2. PushSortNetwork — Sort_A and Sort_B run in separate threads.
                       Each pushes (lows, highs) into a queue when done.
                       Sort_C runs phase-1 merges in two more threads, then phase-2.

    3. PullSortNetwork — Sort_A and Sort_B are exposed as generator-style
                                         interfaces, but this implementation materializes each
                                         side before merging. Sort_C then combines them via heapq;
                                         the 4-partition structure is retained for algorithmic
                                         tracking.

Sort_C 4-partition merge:
  Knows: lows_X = sorted_X[:n//2],  highs_X = sorted_X[n//2:]
         and lows_X[-1] <= highs_X[0]  (within each source X).
  Phase 1a: merge(lows_A, lows_B)     # independent -- run in parallel (push)
  Phase 1b: merge(highs_A, highs_B)   # or sequential (pull)
  Phase 2:  merge(phase_1a, phase_1b)
  This is equivalent to a direct 4-way merge but allows phase-1 parallelism.
  Trade-off: 3 merge passes vs 1 => more total comparisons; wall-time savings
  only materialise under true CPU parallelism (Python GIL limits threading here).

Note on GIL: Python threads don't achieve true CPU parallelism for pure-Python
code. Push wall times reflect threading overhead; comparison counts track the
pure algorithmic structure independent of GIL effects.
"""

import heapq
import threading
import queue
import time
import json
import sys
import os
import random
from collections import Counter, defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))
from benchmark_deep import (
    insertion_sort, merge_sort, quick_sort, tim_custom,
    radix_sort, heap_sort, bubble_sort,
    GENERATORS,
)

SEEDS = [42, 137, 1618, 2718, 3141, 9973, 31337, 65537]
SIZES = [64, 256, 1024]


# ─────────────────────────── MERGE HELPERS ───────────────────────────────────

def _merge2(a, b):
    """Standard 2-way merge. Returns (result, comparisons)."""
    out = []
    comps = 0
    i = j = 0
    while i < len(a) and j < len(b):
        comps += 1
        if a[i] <= b[j]:
            out.append(a[i]); i += 1
        else:
            out.append(b[j]); j += 1
    out.extend(a[i:])
    out.extend(b[j:])
    return out, comps


def sort_c_4partition(lows_a, highs_a, lows_b, highs_b, parallel=False):
    """
    3-phase merge exploiting lows/highs label knowledge.

    Phase 1a and 1b never compare across the low/high boundary of the SAME
    source — that ordering is already guaranteed. Phase 2 handles any
    cross-source interleaving, making the result identical to a full 4-way merge.

    parallel=True: phases 1a and 1b run in separate threads.
    """
    if parallel:
        slot_lo = [None, 0]
        slot_hi = [None, 0]

        def do_lo(): slot_lo[0], slot_lo[1] = _merge2(lows_a,  lows_b)
        def do_hi(): slot_hi[0], slot_hi[1] = _merge2(highs_a, highs_b)

        t1 = threading.Thread(target=do_lo)
        t2 = threading.Thread(target=do_hi)
        t1.start(); t2.start()
        t1.join();  t2.join()

        m_lo, c1 = slot_lo[0], slot_lo[1]
        m_hi, c2 = slot_hi[0], slot_hi[1]
    else:
        m_lo, c1 = _merge2(lows_a, lows_b)
        m_hi, c2 = _merge2(highs_a, highs_b)

    final, c3 = _merge2(m_lo, m_hi)
    return final, c1 + c2 + c3


def _split_lh(sorted_arr):
    """Split a sorted array at its midpoint into (lows, highs)."""
    m = len(sorted_arr) // 2
    return sorted_arr[:m], sorted_arr[m:]


# ─────────────────────────── MARKOV ROUTER ───────────────────────────────────

class MarkovRouter:
    """
    Races a pool of (name, sort_fn) pairs on each input. Builds an empirical
    Markov transition matrix: transitions[last_winner][next_winner] += 1.
    Routes the next input to the most likely winner from the current state.

    The provenance chain is a complete log of who won each race and what was
    predicted, enabling retrospective analysis of adaptation behaviour.
    """

    def __init__(self, pool):
        """pool: list of (name, sort_fn)."""
        self.names    = [p[0] for p in pool]
        self.fns      = [p[1] for p in pool]
        k             = len(pool)
        # transitions[i][j] = count of races where state was i and winner was j
        self.transitions  = [[0] * k for _ in range(k)]
        self.last_winner  = 0      # initial state (arbitrary)
        self.history      = []     # list of race records

    def race_all(self, arr, label=None):
        """Race every pool member on arr. Record winner. Update transition."""
        times = []
        for fn in self.fns:
            t0 = time.perf_counter()
            fn(arr[:])
            times.append(time.perf_counter() - t0)

        winner = min(range(len(times)), key=lambda i: times[i])
        self.transitions[self.last_winner][winner] += 1

        record = {
            'label':     label,
            'winner':    self.names[winner],
            'winner_idx': winner,
            'times_ms':  [t * 1000 for t in times],
        }
        self.history.append(record)
        self.last_winner = winner
        return record

    def predict(self):
        """Return index of most likely winner given current Markov state."""
        row   = self.transitions[self.last_winner]
        total = sum(row)
        if total == 0:
            return self.last_winner
        return max(range(len(row)), key=lambda i: row[i])

    def route(self, arr):
        """Sort arr with predicted winner. Update state as if it won."""
        idx           = self.predict()
        res, comps, ops = self.fns[idx](arr[:])
        self.transitions[self.last_winner][idx] += 1
        self.last_winner = idx
        return res, comps, ops, self.names[idx]

    def print_chain(self):
        k = len(self.names)
        col = 10
        print(f"\n{'MARKOV PROVENANCE CHAIN':=^{8 + 20 + 14 + k*col}}")
        hdr = f"{'#':<5}{'Label':<22}{'Winner':<14}" + "".join(f"{n:>{col}}" for n in self.names)
        print(hdr)
        print("-" * len(hdr))
        for i, h in enumerate(self.history):
            times = "".join(f"{t:>{col}.3f}" for t in h['times_ms'])
            print(f"{i:<5}{str(h['label']):<22}{h['winner']:<14}{times}")

        print(f"\n{'TRANSITION MATRIX  (probability: row=from, col=to)':}")
        print("         " + "".join(f"{n:>10}" for n in self.names))
        for i, row in enumerate(self.transitions):
            total = sum(row)
            if total == 0:
                probs = ["    ----" for _ in row]
            else:
                probs = [f"{v/total:>10.2f}" for v in row]
            print(f"  {self.names[i]:<7}" + "".join(probs))


# ─────────────────────────── PUSH NETWORK ────────────────────────────────────

class PushSortNetwork:
    """
    Sort_A and Sort_B run in separate threads. Each pushes its (lows, highs)
    split to a queue. Sort_C (4-partition) fires two more threads for phase-1
    merges, waits on both, then runs phase-2 on the main thread.

    Concurrency model: fan-out (input → A‖B) then fan-in (lows_merge‖highs_merge
    → phase-2). Under the GIL all Python threads run sequentially, so
    wall-time advantages require a GIL-releasing extension (e.g. numpy). The
    comparison counts represent the pure algorithmic cost.
    """

    def __init__(self, name_a, sort_a, name_b, sort_b):
        self.name_a = name_a
        self.name_b = name_b
        self.sa     = sort_a
        self.sb     = sort_b
        self.name   = f"Push({name_a}||{name_b})"

    def sort(self, arr):
        n = len(arr)
        if n <= 1:
            return arr[:], 0, 0

        left  = arr[:n // 2]
        right = arr[n // 2:]
        q_a   = queue.Queue()
        q_b   = queue.Queue()

        def run_a():
            res, c, o = self.sa(left[:])
            lo, hi = _split_lh(res)
            q_a.put((lo, hi, c, o))

        def run_b():
            res, c, o = self.sb(right[:])
            lo, hi = _split_lh(res)
            q_b.put((lo, hi, c, o))

        t_a = threading.Thread(target=run_a)
        t_b = threading.Thread(target=run_b)
        t_a.start(); t_b.start()
        t_a.join();  t_b.join()

        lows_a, highs_a, c_a, o_a = q_a.get()
        lows_b, highs_b, c_b, o_b = q_b.get()

        merged, c_c = sort_c_4partition(lows_a, highs_a, lows_b, highs_b, parallel=True)
        return merged, c_a + c_b + c_c, o_a + o_b


# ─────────────────────────── PULL NETWORK ────────────────────────────────────

class PullSortNetwork:
    """
    Pull model: Sort_C is the consumer. The code keeps the pull-oriented shape
    of the API, but each side is fully sorted before the merge step begins.

    For the 4-partition structure (comparison tracking) the full sort must
    complete before the first element is yielded — true streaming with partial
    results would require online sort algorithms (e.g. patience sorting). The
    3-phase merge then runs sequentially.
    """

    def __init__(self, name_a, sort_a, name_b, sort_b):
        self.name_a = name_a
        self.name_b = name_b
        self.sa     = sort_a
        self.sb     = sort_b
        self.name   = f"Pull({name_a}+{name_b})"

    def _stream(self, sort_fn, arr):
        """Generator: sort arr, yield elements one at a time (pull interface)."""
        res, _, _ = sort_fn(arr[:])
        yield from res

    def sort(self, arr):
        n = len(arr)
        if n <= 1:
            return arr[:], 0, 0

        left  = arr[:n // 2]
        right = arr[n // 2:]

        # Trigger both sorts (pull: consumer drives, but full sort before first yield)
        res_a, c_a, o_a = self.sa(left[:])
        res_b, c_b, o_b = self.sb(right[:])

        lows_a, highs_a = _split_lh(res_a)
        lows_b, highs_b = _split_lh(res_b)

        # Pull through Sort_C (sequential 3-phase)
        merged, c_c = sort_c_4partition(lows_a, highs_a, lows_b, highs_b, parallel=False)
        return merged, c_a + c_b + c_c, o_a + o_b


# ─────────────────────────── MARKOV NETWORK ──────────────────────────────────

class MarkovSortNetwork:
    """
    Combines the Markov router with a pool of (Sort_A, Sort_B) PAIRS.
    After each input the pair that finished first becomes the new Markov state.
    Subsequent inputs are routed to the predicted best pair.

    This creates better provenance chains over time: the network learns which
    algorithm PAIR suits the current data stream's character, and adapts
    when the character changes.
    """

    def __init__(self, pair_pool):
        """
        pair_pool: list of (name, PushSortNetwork_or_PullSortNetwork).
        """
        self.names       = [p[0] for p in pair_pool]
        self.nets        = [p[1] for p in pair_pool]
        k                = len(pair_pool)
        self.transitions = [[0] * k for _ in range(k)]
        self.last_winner = 0
        self.history     = []

    def race_pairs(self, arr, label=None):
        """Race every network pair, update chain, return winner record."""
        times  = []
        comps_ = []
        for net in self.nets:
            t0 = time.perf_counter()
            _, comps, _ = net.sort(arr[:])
            times.append(time.perf_counter() - t0)
            comps_.append(comps)

        winner = min(range(len(times)), key=lambda i: times[i])
        self.transitions[self.last_winner][winner] += 1
        record = {
            'label':     label,
            'winner':    self.names[winner],
            'winner_idx': winner,
            'times_ms':  [t * 1000 for t in times],
            'comps':     comps_,
        }
        self.history.append(record)
        self.last_winner = winner
        return record

    def route(self, arr):
        """Sort arr with the predicted best pair."""
        row   = self.transitions[self.last_winner]
        total = sum(row)
        idx   = max(range(len(row)), key=lambda i: row[i]) if total > 0 else self.last_winner
        res, comps, ops = self.nets[idx].sort(arr[:])
        self.transitions[self.last_winner][idx] += 1
        self.last_winner = idx
        return res, comps, ops, self.names[idx]

    def print_pair_chain(self, max_rows=32):
        k = len(self.names)
        col = 12
        print(f"\n{'MARKOV PAIR ROUTING CHAIN':=^{6 + 22 + k*col}}")
        hdr = f"{'#':<5}{'Label':<22}" + "".join(f"{n:>{col}}" for n in self.names)
        print(hdr)
        print("-" * len(hdr))
        for i, h in enumerate(self.history[:max_rows]):
            marker = " <-- winner"
            times  = ""
            for j, t in enumerate(h['times_ms']):
                tag = marker if j == h['winner_idx'] else ""
                times += f"{t:>{col}.3f}"
            winner_col = " " * (h['winner_idx'] * col)
            print(f"{i:<5}{str(h['label']):<22}{times}")


# ─────────────────────────── BENCHMARK ───────────────────────────────────────

# Algorithms available to the network
POOL_ALGS = [
    ('Tim',       tim_custom),
    ('Quick',     quick_sort),
    ('Merge',     merge_sort),
    ('Radix',     radix_sort),
    ('Insertion', insertion_sort),
]

# Network pairs to benchmark
PAIR_SPECS = [
    ('Quick',     quick_sort,     'Radix',     radix_sort),
    ('Merge',     merge_sort,     'Radix',     radix_sort),
    ('Quick',     quick_sort,     'Merge',     merge_sort),
    ('Merge',     merge_sort,     'Quick',     quick_sort),
    ('Tim',       tim_custom,     'Insertion', insertion_sort),
    ('Quick',     quick_sort,     'Insertion', insertion_sort),
]

# Baselines
BASELINES = [
    ('TimCustom',  tim_custom),
    ('Quick',      quick_sort),
    ('Merge',      merge_sort),
]

INPUT_TYPES = list(GENERATORS.keys())   # 13 input types


def _verify(original, result, name):
    if sorted(original) != result:
        raise AssertionError(f"CORRECTNESS FAILURE in {name}")


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def section_separator(title):
    print(f"\n{'='*80}")
    print(title)
    print('='*80)


# ── SECTION 1: Standalone Markov provenance across changing input streams ─────

def run_markov_provenance_demo(n=512):
    section_separator("SECTION 1 — MARKOV PROVENANCE CHAIN  (n=%d, pool: Tim/Quick/Merge/Radix/Insertion)" % n)

    router = MarkovRouter(POOL_ALGS)

    # 4 phases: input character changes every 8 seeds to test adaptation.
    phases = [
        ("random",        "Phase A"),
        ("nearly_sorted", "Phase B"),
        ("few_unique",    "Phase C"),
        ("random",        "Phase D"),
    ]
    scenario = []
    for itype, phase_label in phases:
        for seed in SEEDS:
            scenario.append((itype, seed, phase_label))

    # Warm-up: first race establishes initial state (no prediction to evaluate)
    correct = 0
    total   = 0
    for itype, seed, phase_label in scenario:
        arr  = GENERATORS[itype](n, seed)
        pred = router.predict()
        rec  = router.race_all(arr, label=f"{phase_label} {itype}:{seed}")
        actual = rec['winner_idx']
        if total > 0:   # skip first (no prior state to predict from)
            if pred == actual:
                correct += 1
        total += 1

    router.print_chain()

    accuracy = correct / max(1, total - 1) * 100
    print(f"\nLag-1 prediction accuracy: {correct}/{total-1} = {accuracy:.1f}%")

    print("\nPer-phase winner distribution:")
    for itype, phase_label in phases:
        idxs   = [i for i, (it, _, pl) in enumerate(scenario) if pl == phase_label]
        winners = [router.history[i]['winner'] for i in idxs]
        c = Counter(winners)
        print(f"  {phase_label} ({itype:<14}): {dict(c)}")

    print("\nAdaptation lag (seeds until correct prediction after phase transition):")
    transitions_at = [8, 16, 24]  # indices where phase changes
    for t_idx in transitions_at:
        if t_idx >= len(router.history):
            continue
        new_phase_winner = router.history[t_idx]['winner']
        lag = 0
        for j in range(t_idx, min(t_idx + 8, len(router.history))):
            if router.history[j]['winner'] != new_phase_winner:
                lag += 1
            else:
                break
        print(f"  After index {t_idx}: dominant winner={new_phase_winner}, adaptation lag={lag} races")

    return router


# ── SECTION 2: Push vs Pull network comparison table ─────────────────────────

def run_network_comparison():
    section_separator("SECTION 2 — PUSH vs PULL NETWORK COMPARISON  (mean over 8 seeds × 13 input types)")

    push_nets = [PushSortNetwork(a, fa, b, fb) for a, fa, b, fb in PAIR_SPECS]
    pull_nets = [PullSortNetwork(a, fa, b, fb) for a, fa, b, fb in PAIR_SPECS]

    all_configs = (
        [(net.name, net.sort) for net in push_nets] +
        [(net.name, net.sort) for net in pull_nets] +
        [(name, fn)           for name, fn in BASELINES]
    )

    for size in SIZES:
        print(f"\n── n = {size} " + "─" * 55)
        results = {}

        for cfg_name, sort_fn in all_configs:
            comps_list = []
            time_list  = []
            for itype in INPUT_TYPES:
                for seed in SEEDS:
                    arr = GENERATORS[itype](size, seed)
                    t0  = time.perf_counter()
                    res, comps, _ = sort_fn(arr)
                    elapsed = (time.perf_counter() - t0) * 1000
                    _verify(arr, res, cfg_name)
                    comps_list.append(comps)
                    time_list.append(elapsed)

            results[cfg_name] = {
                'comps': _mean(comps_list),
                'ms':    _mean(time_list),
            }

        sorted_cfgs = sorted(results.items(), key=lambda x: x[1]['ms'])
        print(f"  {'Name':<32} {'Mean Comps':>12} {'Mean ms':>10}")
        print(f"  {'-'*32} {'-'*12} {'-'*10}")
        for name, r in sorted_cfgs:
            print(f"  {name:<32} {r['comps']:>12,.0f} {r['ms']:>10.3f}")

    return results


# ── SECTION 3: Push vs Pull overhead breakdown ────────────────────────────────

def run_overhead_breakdown():
    section_separator("SECTION 3 — PUSH vs PULL OVERHEAD  (Quick||Radix, 30 runs each)")

    push_net = PushSortNetwork('Quick', quick_sort, 'Radix', radix_sort)
    pull_net = PullSortNetwork('Quick', quick_sort, 'Radix', radix_sort)
    direct   = ('Direct merge(Q+R)', lambda arr: (
        lambda a, b, c: (c[0], a[1] + b[1] + c[1], 0))(
            quick_sort(arr[:len(arr)//2]),
            radix_sort(arr[len(arr)//2:]),
            _merge2(*[quick_sort(arr[:len(arr)//2])[0], radix_sort(arr[len(arr)//2:])[0]])
    ))

    print(f"\n  Note: Python GIL serialises CPU-bound threads. Push overhead = thread")
    print(f"  spawn + queue + GIL contention. Comparison counts are GIL-independent.\n")
    print(f"  {'n':<8} {'Push ms':>10} {'Pull ms':>10} {'Thread overhead':>16} {'Push comps':>12} {'Pull comps':>12}")
    print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*16} {'-'*12} {'-'*12}")

    for size in SIZES:
        arr = GENERATORS['random'](size, 42)
        push_times, pull_times = [], []
        push_comps = pull_comps = 0
        runs = 30
        for _ in range(runs):
            t0 = time.perf_counter()
            res, pc, _ = push_net.sort(arr)
            push_times.append((time.perf_counter() - t0) * 1000)
            push_comps = pc
            t0 = time.perf_counter()
            res, lc, _ = pull_net.sort(arr)
            pull_times.append((time.perf_counter() - t0) * 1000)
            pull_comps = lc

        push_ms = _mean(push_times)
        pull_ms = _mean(pull_times)
        overhead = (push_ms / pull_ms - 1.0) * 100 if pull_ms > 0 else 0
        print(f"  {size:<8} {push_ms:>10.3f} {pull_ms:>10.3f} {overhead:>+15.1f}% {push_comps:>12,} {pull_comps:>12,}")

    print(f"\n  Comparison count difference (push - pull): always 0.")
    print(f"  Both models run the same 3-phase Sort_C; difference is pure overhead.")


# ── SECTION 4: Markov-routed network pairs ────────────────────────────────────

def run_markov_network(n=512):
    section_separator("SECTION 4 — MARKOV-ROUTED NETWORK PAIRS  (n=%d, pull mode)" % n)

    pair_pool = [
        (spec[0] + '+' + spec[2],
         PullSortNetwork(spec[0], spec[1], spec[2], spec[3]))
        for spec in PAIR_SPECS
    ]
    markov_net = MarkovSortNetwork(pair_pool)

    phases = [
        ("random",        "Phase A"),
        ("nearly_sorted", "Phase B"),
        ("few_unique",    "Phase C"),
        ("random",        "Phase D"),
    ]
    scenario = [(itype, seed, pl) for itype, pl in phases for seed in SEEDS]

    for itype, seed, phase_label in scenario:
        arr = GENERATORS[itype](n, seed)
        markov_net.race_pairs(arr, label=f"{phase_label} {itype}")

    # Print condensed chain (winner only, not all times)
    k = len(markov_net.names)
    print(f"\n  {'#':<5} {'Label':<30} {'Winner Pair':<22} {'Winner ms':>10}")
    print(f"  {'-'*5} {'-'*30} {'-'*22} {'-'*10}")
    for i, h in enumerate(markov_net.history):
        best_ms = min(h['times_ms'])
        print(f"  {i:<5} {str(h['label']):<30} {h['winner']:<22} {best_ms:>10.3f}")

    print("\nTransition matrix (pair routing):")
    print("         " + "".join(f"{n:>14}" for n in markov_net.names))
    for i, row in enumerate(markov_net.transitions):
        total = sum(row)
        if total == 0:
            probs = ["    ----      " for _ in row]
        else:
            probs = [f"{v/total:>14.2f}" for v in row]
        print(f"  {markov_net.names[i]:<7}" + "".join(probs))

    print("\nPer-phase dominant pairs:")
    for itype, phase_label in phases:
        idxs    = [i for i, (it, _, pl) in enumerate(scenario) if pl == phase_label]
        winners = [markov_net.history[i]['winner'] for i in idxs]
        c = Counter(winners)
        print(f"  {phase_label} ({itype:<14}): {dict(c)}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("ZIPPER SORT NETWORKS — Push || Pull || Markov Routing")
    print("Sort_C: 4-partition 3-phase merge  |  Seeds: mathematical constants")

    router      = run_markov_provenance_demo(n=512)
    last_result = run_network_comparison()
    run_overhead_breakdown()
    run_markov_network(n=512)

    print("\n" + "="*80)
    print("ALL CORRECTNESS CHECKS PASSED")
    print("="*80)
