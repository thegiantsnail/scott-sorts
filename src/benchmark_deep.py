"""
benchmark_deep.py - Deep analysis of sorting algorithm performance.
"""
import sys
import time
import random
import json
import math
import copy

sys.setrecursionlimit(100000)

# ---------------------------------------------------------------------------
# Instrumented sorting algorithms
# Each returns (sorted_arr, comparisons, swaps_or_moves)
# ---------------------------------------------------------------------------

def bubble_sort(arr):
    a = arr[:]
    n = len(a)
    comps = 0
    swaps = 0
    for i in range(n):
        for j in range(n - 1 - i):
            comps += 1
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swaps += 1
    return a, comps, swaps


def insertion_sort(arr):
    a = arr[:]
    comps = 0
    moves = 0
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0:
            comps += 1
            if a[j] > key:
                a[j + 1] = a[j]
                moves += 1
                j -= 1
            else:
                break
        a[j + 1] = key
        if j + 1 != i:
            moves += 1
    return a, comps, moves


def selection_sort(arr):
    a = arr[:]
    n = len(a)
    comps = 0
    swaps = 0
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            comps += 1
            if a[j] < a[min_idx]:
                min_idx = j
        if min_idx != i:
            a[i], a[min_idx] = a[min_idx], a[i]
            swaps += 1
    return a, comps, swaps


def merge_sort(arr):
    a = arr[:]
    comps = [0]
    moves = [0]

    def _merge(arr, left, mid, right):
        L = arr[left:mid + 1]
        R = arr[mid + 1:right + 1]
        i = j = 0
        k = left
        while i < len(L) and j < len(R):
            comps[0] += 1
            if L[i] <= R[j]:
                arr[k] = L[i]
                i += 1
            else:
                arr[k] = R[j]
                j += 1
            moves[0] += 1
            k += 1
        while i < len(L):
            arr[k] = L[i]
            i += 1
            k += 1
            moves[0] += 1
        while j < len(R):
            arr[k] = R[j]
            j += 1
            k += 1
            moves[0] += 1

    def _sort(arr, left, right):
        if left < right:
            mid = (left + right) // 2
            _sort(arr, left, mid)
            _sort(arr, mid + 1, right)
            _merge(arr, left, mid, right)

    _sort(a, 0, len(a) - 1)
    return a, comps[0], moves[0]


def _insertion_sort_range(a, left, right, comps, moves):
    for i in range(left + 1, right + 1):
        key = a[i]
        j = i - 1
        while j >= left:
            comps[0] += 1
            if a[j] > key:
                a[j + 1] = a[j]
                moves[0] += 1
                j -= 1
            else:
                break
        a[j + 1] = key
        if j + 1 != i:
            moves[0] += 1


def quick_sort(arr):
    a = arr[:]
    comps = [0]
    swaps = [0]

    def _median3(a, lo, hi):
        mid = (lo + hi) // 2
        comps[0] += 2
        if a[lo] > a[mid]:
            a[lo], a[mid] = a[mid], a[lo]
            swaps[0] += 1
        if a[lo] > a[hi]:
            a[lo], a[hi] = a[hi], a[lo]
            swaps[0] += 1
        if a[mid] > a[hi]:
            a[mid], a[hi] = a[hi], a[mid]
            swaps[0] += 1
        # Put pivot at hi-1
        a[mid], a[hi - 1] = a[hi - 1], a[mid]
        swaps[0] += 1
        return a[hi - 1]

    def _insertion(a, lo, hi):
        for i in range(lo + 1, hi + 1):
            key = a[i]
            j = i - 1
            while j >= lo:
                comps[0] += 1
                if a[j] > key:
                    a[j + 1] = a[j]
                    j -= 1
                else:
                    break
            a[j + 1] = key

    def _sort(a, lo, hi):
        size = hi - lo + 1
        if size <= 1:
            return
        if size <= 3:
            _insertion(a, lo, hi)
            return
        pivot = _median3(a, lo, hi)
        i = lo
        j = hi - 1
        while True:
            i += 1
            while i <= hi - 1:
                comps[0] += 1
                if a[i] < pivot:
                    i += 1
                else:
                    break
            j -= 1
            while j >= lo:
                comps[0] += 1
                if a[j] > pivot:
                    j -= 1
                else:
                    break
            if i >= j:
                break
            a[i], a[j] = a[j], a[i]
            swaps[0] += 1
        # Restore pivot
        a[i], a[hi - 1] = a[hi - 1], a[i]
        swaps[0] += 1
        _sort(a, lo, i - 1)
        _sort(a, i + 1, hi)

    _sort(a, 0, len(a) - 1)
    return a, comps[0], swaps[0]


def heap_sort(arr):
    """Iterative heapsort to avoid stack issues."""
    a = arr[:]
    n = len(a)
    comps = 0
    swaps = 0

    def _sift_down(a, start, end):
        nonlocal comps, swaps
        root = start
        while True:
            child = 2 * root + 1
            if child > end:
                break
            if child + 1 <= end:
                comps += 1
                if a[child] < a[child + 1]:
                    child += 1
            comps += 1
            if a[root] < a[child]:
                a[root], a[child] = a[child], a[root]
                swaps += 1
                root = child
            else:
                break

    # Build max-heap
    for start in range((n - 2) // 2, -1, -1):
        _sift_down(a, start, n - 1)

    # Extract elements
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        swaps += 1
        _sift_down(a, 0, end - 1)

    return a, comps, swaps


def radix_sort(arr):
    a = arr[:]
    n = len(a)
    moves = 0
    comps = 0

    if n == 0:
        return a, comps, moves

    max_val = max(a)
    if max_val == 0:
        return a, comps, moves

    exp = 1
    while max_val // exp > 0:
        output = [0] * n
        count = [0] * 10
        for val in a:
            digit = (val // exp) % 10
            count[digit] += 1
        for i in range(1, 10):
            count[i] += count[i - 1]
        for i in range(n - 1, -1, -1):
            digit = (a[i] // exp) % 10
            count[digit] -= 1
            output[count[digit]] = a[i]
            moves += 1
        a = output
        exp *= 10

    return a, comps, moves


def _tim_merge(a, left, mid, right, comps, moves):
    L = a[left:mid + 1]
    R = a[mid + 1:right + 1]
    i = j = 0
    k = left
    while i < len(L) and j < len(R):
        comps[0] += 1
        if L[i] <= R[j]:
            a[k] = L[i]
            i += 1
        else:
            a[k] = R[j]
            j += 1
        moves[0] += 1
        k += 1
    while i < len(L):
        a[k] = L[i]
        i += 1
        k += 1
        moves[0] += 1
    while j < len(R):
        a[k] = R[j]
        j += 1
        k += 1
        moves[0] += 1


def tim_custom(arr):
    a = arr[:]
    n = len(a)
    comps = [0]
    moves = [0]
    RUN = 32

    # Sort individual runs with insertion sort
    for start in range(0, n, RUN):
        end = min(start + RUN - 1, n - 1)
        _insertion_sort_range(a, start, end, comps, moves)

    # Merge runs
    size = RUN
    while size < n:
        for left in range(0, n, 2 * size):
            mid = min(left + size - 1, n - 1)
            right = min(left + 2 * size - 1, n - 1)
            if mid < right:
                _tim_merge(a, left, mid, right, comps, moves)
        size *= 2

    return a, comps[0], moves[0]


# ---------------------------------------------------------------------------
# Hybrid algorithms
# ---------------------------------------------------------------------------

HYBRID_CUTOFF = 16


def hybrid_qi(arr):
    """Quicksort switching to Insertion for subarrays <= 16."""
    a = arr[:]
    comps = [0]
    swaps = [0]

    def _insertion(a, lo, hi):
        for i in range(lo + 1, hi + 1):
            key = a[i]
            j = i - 1
            while j >= lo:
                comps[0] += 1
                if a[j] > key:
                    a[j + 1] = a[j]
                    j -= 1
                else:
                    break
            a[j + 1] = key

    def _median3(a, lo, hi):
        mid = (lo + hi) // 2
        comps[0] += 2
        if a[lo] > a[mid]:
            a[lo], a[mid] = a[mid], a[lo]
            swaps[0] += 1
        if a[lo] > a[hi]:
            a[lo], a[hi] = a[hi], a[lo]
            swaps[0] += 1
        if a[mid] > a[hi]:
            a[mid], a[hi] = a[hi], a[mid]
            swaps[0] += 1
        a[mid], a[hi - 1] = a[hi - 1], a[mid]
        swaps[0] += 1
        return a[hi - 1]

    def _sort(a, lo, hi):
        size = hi - lo + 1
        if size <= HYBRID_CUTOFF:
            _insertion(a, lo, hi)
            return
        pivot = _median3(a, lo, hi)
        i = lo
        j = hi - 1
        while True:
            i += 1
            while i <= hi - 1:
                comps[0] += 1
                if a[i] < pivot:
                    i += 1
                else:
                    break
            j -= 1
            while j >= lo:
                comps[0] += 1
                if a[j] > pivot:
                    j -= 1
                else:
                    break
            if i >= j:
                break
            a[i], a[j] = a[j], a[i]
            swaps[0] += 1
        a[i], a[hi - 1] = a[hi - 1], a[i]
        swaps[0] += 1
        _sort(a, lo, i - 1)
        _sort(a, i + 1, hi)

    if len(a) > 1:
        _sort(a, 0, len(a) - 1)
    return a, comps[0], swaps[0]


def hybrid_mi(arr):
    """Mergesort switching to Insertion for subarrays <= 16."""
    a = arr[:]
    comps = [0]
    moves = [0]

    def _insertion(a, lo, hi):
        for i in range(lo + 1, hi + 1):
            key = a[i]
            j = i - 1
            while j >= lo:
                comps[0] += 1
                if a[j] > key:
                    a[j + 1] = a[j]
                    j -= 1
                else:
                    break
            a[j + 1] = key
            if j + 1 != i:
                moves[0] += 1

    def _merge(a, lo, mid, hi):
        L = a[lo:mid + 1]
        R = a[mid + 1:hi + 1]
        i = j = 0
        k = lo
        while i < len(L) and j < len(R):
            comps[0] += 1
            if L[i] <= R[j]:
                a[k] = L[i]
                i += 1
            else:
                a[k] = R[j]
                j += 1
            moves[0] += 1
            k += 1
        while i < len(L):
            a[k] = L[i]
            i += 1
            k += 1
            moves[0] += 1
        while j < len(R):
            a[k] = R[j]
            j += 1
            k += 1
            moves[0] += 1

    def _sort(a, lo, hi):
        if hi - lo + 1 <= HYBRID_CUTOFF:
            _insertion(a, lo, hi)
            return
        mid = (lo + hi) // 2
        _sort(a, lo, mid)
        _sort(a, mid + 1, hi)
        _merge(a, lo, mid, hi)

    if len(a) > 1:
        _sort(a, 0, len(a) - 1)
    return a, comps[0], moves[0]


def hybrid_ri(arr):
    """Radix with Insertion fallback for small n (<=16)."""
    a = arr[:]
    n = len(a)
    comps = 0
    moves = 0

    if n <= HYBRID_CUTOFF or min(a) < 0:
        # Fall back to insertion sort
        for i in range(1, n):
            key = a[i]
            j = i - 1
            while j >= 0:
                comps += 1
                if a[j] > key:
                    a[j + 1] = a[j]
                    moves += 1
                    j -= 1
                else:
                    break
            a[j + 1] = key
            if j + 1 != i:
                moves += 1
        return a, comps, moves

    max_val = max(a)
    if max_val == 0:
        return a, comps, moves

    exp = 1
    while max_val // exp > 0:
        output = [0] * n
        count = [0] * 10
        for val in a:
            digit = (val // exp) % 10
            count[digit] += 1
        for i in range(1, 10):
            count[i] += count[i - 1]
        for i in range(n - 1, -1, -1):
            digit = (a[i] // exp) % 10
            count[digit] -= 1
            output[count[digit]] = a[i]
            moves += 1
        a = output
        exp *= 10

    return a, comps, moves


def hybrid_intro(arr):
    """Introsort: Quicksort -> Heapsort when depth exceeded, Insertion for small."""
    a = arr[:]
    n = len(a)
    comps = [0]
    swaps = [0]
    max_depth = 2 * math.floor(math.log2(n)) if n > 1 else 1

    def _insertion(a, lo, hi):
        for i in range(lo + 1, hi + 1):
            key = a[i]
            j = i - 1
            while j >= lo:
                comps[0] += 1
                if a[j] > key:
                    a[j + 1] = a[j]
                    j -= 1
                else:
                    break
            a[j + 1] = key

    def _sift_down(a, start, end):
        root = start
        while True:
            child = 2 * root + 1
            if child > end:
                break
            if child + 1 <= end:
                comps[0] += 1
                if a[child] < a[child + 1]:
                    child += 1
            comps[0] += 1
            if a[root] < a[child]:
                a[root], a[child] = a[child], a[root]
                swaps[0] += 1
                root = child
            else:
                break

    def _heapsort(a, lo, hi):
        n = hi - lo + 1
        # Build heap on subarray
        sub = a[lo:hi + 1]
        for start in range((n - 2) // 2, -1, -1):
            _sift_down(sub, start, n - 1)
        for end in range(n - 1, 0, -1):
            sub[0], sub[end] = sub[end], sub[0]
            swaps[0] += 1
            _sift_down(sub, 0, end - 1)
        a[lo:hi + 1] = sub

    def _median3(a, lo, hi):
        mid = (lo + hi) // 2
        comps[0] += 2
        if a[lo] > a[mid]:
            a[lo], a[mid] = a[mid], a[lo]
            swaps[0] += 1
        if a[lo] > a[hi]:
            a[lo], a[hi] = a[hi], a[lo]
            swaps[0] += 1
        if a[mid] > a[hi]:
            a[mid], a[hi] = a[hi], a[mid]
            swaps[0] += 1
        a[mid], a[hi - 1] = a[hi - 1], a[mid]
        swaps[0] += 1
        return a[hi - 1]

    def _sort(a, lo, hi, depth):
        size = hi - lo + 1
        if size <= HYBRID_CUTOFF:
            _insertion(a, lo, hi)
            return
        if depth == 0:
            _heapsort(a, lo, hi)
            return
        pivot = _median3(a, lo, hi)
        i = lo
        j = hi - 1
        while True:
            i += 1
            while i <= hi - 1:
                comps[0] += 1
                if a[i] < pivot:
                    i += 1
                else:
                    break
            j -= 1
            while j >= lo:
                comps[0] += 1
                if a[j] > pivot:
                    j -= 1
                else:
                    break
            if i >= j:
                break
            a[i], a[j] = a[j], a[i]
            swaps[0] += 1
        a[i], a[hi - 1] = a[hi - 1], a[i]
        swaps[0] += 1
        _sort(a, lo, i - 1, depth - 1)
        _sort(a, i + 1, hi, depth - 1)

    if n > 1:
        _sort(a, 0, n - 1, max_depth)
    return a, comps[0], swaps[0]


# ---------------------------------------------------------------------------
# Input generators
# ---------------------------------------------------------------------------

def gen_random(n, seed=42):
    rng = random.Random(seed)
    return [rng.randint(0, 10 * n) for _ in range(n)]


def gen_sorted(n, seed=42):
    return list(range(n))


def gen_reverse(n, seed=42):
    return list(range(n, 0, -1))


def gen_nearly_sorted(n, seed=42):
    a = list(range(n))
    rng = random.Random(seed)
    swaps = n // 20
    for _ in range(swaps):
        i, j = rng.randint(0, n - 1), rng.randint(0, n - 1)
        a[i], a[j] = a[j], a[i]
    return a


def gen_few_unique(n, seed=42):
    rng = random.Random(seed)
    vals = [0, 1, 2, 3, 4]
    return [rng.choice(vals) for _ in range(n)]


def gen_sawtooth(n, seed=42):
    period = max(n // 10, 1)
    return [i % period for i in range(n)]


def gen_pipe_organ(n, seed=42):
    half = n // 2
    return list(range(half)) + list(range(half, 0, -1))


def gen_all_same(n, seed=42):
    return [42] * n


def gen_two_values(n, seed=42):
    rng = random.Random(seed)
    return [rng.randint(0, 1) for _ in range(n)]


def gen_interleaved(n, seed=42):
    # Two sorted halves interleaved
    half = n // 2
    a = list(range(0, 2 * half, 2))   # 0,2,4,...
    b = list(range(1, 2 * half, 2))   # 1,3,5,...
    result = []
    for i in range(half):
        result.append(a[i])
        result.append(b[i])
    if n % 2 == 1:
        result.append(2 * half)
    return result


def gen_rotated(n, seed=42):
    a = list(range(n))
    k = n // 4
    return a[k:] + a[:k]


def gen_random_blocks(n, seed=42):
    rng = random.Random(seed)
    block_size = max(n // 10, 1)
    blocks = []
    for start in range(0, n, block_size):
        end = min(start + block_size, n)
        blocks.append(list(range(start, end)))
    rng.shuffle(blocks)
    result = []
    for b in blocks:
        result.extend(b)
    return result[:n]


def gen_killer_quick(n, seed=42):
    """Adversarial input for quicksort (alternating lo/hi pattern)."""
    # Classic killer for median-of-3 quicksort
    a = list(range(n))
    # Alternate between picking from front and back
    result = []
    lo, hi = 0, n - 1
    while lo <= hi:
        if lo == hi:
            result.append(a[lo])
            break
        result.append(a[lo])
        result.append(a[hi])
        lo += 1
        hi -= 1
    return result


GENERATORS = {
    "random": gen_random,
    "sorted": gen_sorted,
    "reverse": gen_reverse,
    "nearly_sorted": gen_nearly_sorted,
    "few_unique": gen_few_unique,
    "sawtooth": gen_sawtooth,
    "pipe_organ": gen_pipe_organ,
    "all_same": gen_all_same,
    "two_values": gen_two_values,
    "interleaved": gen_interleaved,
    "rotated": gen_rotated,
    "random_blocks": gen_random_blocks,
    "killer_quick": gen_killer_quick,
}

ALGORITHMS = {
    "Bubble": bubble_sort,
    "Insertion": insertion_sort,
    "Selection": selection_sort,
    "Merge": merge_sort,
    "Quick": quick_sort,
    "Heap": heap_sort,
    "Radix": radix_sort,
    "TimCustom": tim_custom,
    "Hybrid_QI": hybrid_qi,
    "Hybrid_MI": hybrid_mi,
    "Hybrid_RI": hybrid_ri,
    "Hybrid_Intro": hybrid_intro,
}

# Algorithms to skip for large n
SLOW_ALGS = {"Bubble", "Selection"}

SIZES = [50, 200, 1000, 5000]


# ---------------------------------------------------------------------------
# Benchmarking
# ---------------------------------------------------------------------------

def benchmark():
    results = {}  # results[alg][input_type][size] = {...}

    total_combos = 0
    for alg in ALGORITHMS:
        for inp in GENERATORS:
            for n in SIZES:
                if alg in SLOW_ALGS and n > 500:
                    continue
                total_combos += 1

    done = 0
    for alg_name, alg_fn in ALGORITHMS.items():
        results[alg_name] = {}
        for inp_name, gen_fn in GENERATORS.items():
            results[alg_name][inp_name] = {}
            for n in SIZES:
                if alg_name in SLOW_ALGS and n > 500:
                    continue

                reps = max(1, 200 // n)
                arr = gen_fn(n)
                expected = sorted(arr)

                try:
                    # Time it
                    t0 = time.perf_counter()
                    for _ in range(reps):
                        sorted_arr, comps, ops = alg_fn(arr)
                    t1 = time.perf_counter()
                    elapsed = (t1 - t0) / reps

                    # Verify correctness
                    correct = (sorted_arr == expected)
                    if not correct:
                        print(f"  [WARNING] {alg_name} on {inp_name} n={n}: INCORRECT SORT")

                    results[alg_name][inp_name][n] = {
                        "time": elapsed,
                        "comparisons": comps,
                        "ops": ops,
                        "correct": correct,
                    }
                except Exception as e:
                    print(f"  [ERROR] {alg_name} on {inp_name} n={n}: {e}")
                    results[alg_name][inp_name][n] = {
                        "time": None,
                        "comparisons": None,
                        "ops": None,
                        "correct": False,
                        "error": str(e),
                    }

                done += 1
                if done % 50 == 0:
                    print(f"  Progress: {done}/{total_combos} combinations done...")

    return results


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def analysis_1(results, size=1000):
    """Rankings by input type at given size."""
    print(f"\n{'='*70}")
    print(f"ANALYSIS 1: Rankings by Input Type at n={size} (fastest to slowest)")
    print(f"{'='*70}")

    for inp_name in GENERATORS:
        timings = []
        for alg_name in ALGORITHMS:
            if alg_name in SLOW_ALGS and size > 500:
                continue
            rec = results.get(alg_name, {}).get(inp_name, {}).get(size)
            if rec and rec["time"] is not None:
                timings.append((alg_name, rec["time"]))

        timings.sort(key=lambda x: x[1])
        print(f"\n  Input: {inp_name}")
        print(f"  {'Rank':<5} {'Algorithm':<15} {'Time (ms)':>12} {'Relative':>10}")
        print(f"  {'-'*45}")
        if timings:
            base = timings[0][1]
            for rank, (alg, t) in enumerate(timings, 1):
                rel = t / base if base > 0 else 1.0
                print(f"  {rank:<5} {alg:<15} {t*1000:>12.4f} {rel:>10.2f}x")


def analysis_2(results):
    """Every case where any algorithm beats TimCustom."""
    print(f"\n{'='*70}")
    print("ANALYSIS 2: Cases Where Algorithm Beats TimCustom")
    print(f"{'='*70}")

    beats = []
    for alg_name in ALGORITHMS:
        if alg_name == "TimCustom":
            continue
        for inp_name in GENERATORS:
            for n in SIZES:
                if alg_name in SLOW_ALGS and n > 500:
                    continue
                alg_rec = results.get(alg_name, {}).get(inp_name, {}).get(n)
                tim_rec = results.get("TimCustom", {}).get(inp_name, {}).get(n)
                if alg_rec and tim_rec:
                    at = alg_rec.get("time")
                    tt = tim_rec.get("time")
                    if at is not None and tt is not None and at < tt:
                        ratio = tt / at if at > 0 else float("inf")
                        beats.append((alg_name, inp_name, n, at, tt, ratio))

    beats.sort(key=lambda x: -x[5])
    if beats:
        print(f"\n  {'Algorithm':<15} {'Input':<18} {'n':>6} {'AlgTime(ms)':>13} {'TimTime(ms)':>13} {'Speedup':>9}")
        print(f"  {'-'*76}")
        for alg, inp, n, at, tt, ratio in beats:
            print(f"  {alg:<15} {inp:<18} {n:>6} {at*1000:>13.4f} {tt*1000:>13.4f} {ratio:>9.2f}x")
    else:
        print("  No algorithm beat TimCustom in any tested case.")


def analysis_3(results, size=1000):
    """Comparison counts at n=1000 for key input types."""
    print(f"\n{'='*70}")
    print(f"ANALYSIS 3: Comparison Counts at n={size} for Key Input Types")
    print(f"{'='*70}")

    key_inputs = ["random", "sorted", "reverse", "nearly_sorted", "few_unique", "killer_quick"]

    for inp_name in key_inputs:
        print(f"\n  Input: {inp_name}")
        print(f"  {'Algorithm':<15} {'Comparisons':>14} {'Ops':>14}")
        print(f"  {'-'*45}")
        rows = []
        for alg_name in ALGORITHMS:
            if alg_name in SLOW_ALGS and size > 500:
                continue
            rec = results.get(alg_name, {}).get(inp_name, {}).get(size)
            if rec and rec.get("comparisons") is not None:
                rows.append((alg_name, rec["comparisons"], rec["ops"]))
        rows.sort(key=lambda x: x[1])
        for alg, comps, ops in rows:
            comps_str = f"{comps:,}" if comps is not None else "N/A"
            ops_str = f"{ops:,}" if ops is not None else "N/A"
            print(f"  {alg:<15} {comps_str:>14} {ops_str:>14}")


def analysis_4(results):
    """Hybrid algorithm table across input types and sizes."""
    print(f"\n{'='*70}")
    print("ANALYSIS 4: Hybrid Algorithm Performance Table")
    print(f"{'='*70}")

    hybrids = ["Hybrid_QI", "Hybrid_MI", "Hybrid_RI", "Hybrid_Intro"]
    baselines = ["Quick", "Merge", "Radix", "Heap"]

    for n in SIZES:
        print(f"\n  n={n}")
        header = f"  {'Input':<18}"
        for alg in hybrids + baselines:
            header += f" {alg:>11}"
        print(header)
        print("  " + "-" * (18 + 12 * len(hybrids + baselines)))

        for inp_name in GENERATORS:
            row = f"  {inp_name:<18}"
            for alg in hybrids + baselines:
                if alg in SLOW_ALGS and n > 500:
                    row += f" {'N/A':>11}"
                    continue
                rec = results.get(alg, {}).get(inp_name, {}).get(n)
                if rec and rec.get("time") is not None:
                    row += f" {rec['time']*1000:>11.3f}"
                else:
                    row += f" {'N/A':>11}"
            print(row)
        print(f"  (times in ms)")


def analysis_5(results):
    """Adaptivity ratio (random_time / sorted_time) per algorithm."""
    print(f"\n{'='*70}")
    print("ANALYSIS 5: Adaptivity Ratio (random_time / sorted_time) per Algorithm")
    print("  Lower ratio = more adaptive (sorted input is much faster than random)")
    print(f"{'='*70}")

    for n in [200, 1000, 5000]:
        print(f"\n  n={n}")
        print(f"  {'Algorithm':<15} {'Random(ms)':>12} {'Sorted(ms)':>12} {'Ratio':>10} {'Assessment':>15}")
        print(f"  {'-'*60}")
        rows = []
        for alg_name in ALGORITHMS:
            if alg_name in SLOW_ALGS and n > 500:
                continue
            rand_rec = results.get(alg_name, {}).get("random", {}).get(n)
            sort_rec = results.get(alg_name, {}).get("sorted", {}).get(n)
            if rand_rec and sort_rec:
                rt = rand_rec.get("time")
                st = sort_rec.get("time")
                if rt is not None and st is not None and st > 0:
                    ratio = rt / st
                    rows.append((alg_name, rt, st, ratio))

        rows.sort(key=lambda x: x[3])
        for alg, rt, st, ratio in rows:
            if ratio < 1.5:
                assess = "High adapt."
            elif ratio < 3.0:
                assess = "Moderate"
            else:
                assess = "Low adapt."
            print(f"  {alg:<15} {rt*1000:>12.4f} {st*1000:>12.4f} {ratio:>10.2f} {assess:>15}")


def analysis_6(results):
    """Best algorithm per (input_type, size) scenario."""
    print(f"\n{'='*70}")
    print("ANALYSIS 6: Best Algorithm per (Input Type, Size) Scenario")
    print(f"{'='*70}")

    print(f"\n  {'Input Type':<18}", end="")
    for n in SIZES:
        print(f" {'n='+str(n):>20}", end="")
    print()
    print("  " + "-" * (18 + 21 * len(SIZES)))

    for inp_name in GENERATORS:
        print(f"  {inp_name:<18}", end="")
        for n in SIZES:
            best_alg = None
            best_time = float("inf")
            for alg_name in ALGORITHMS:
                if alg_name in SLOW_ALGS and n > 500:
                    continue
                rec = results.get(alg_name, {}).get(inp_name, {}).get(n)
                if rec and rec.get("time") is not None:
                    if rec["time"] < best_time:
                        best_time = rec["time"]
                        best_alg = alg_name
            if best_alg:
                cell = f"{best_alg}({best_time*1000:.3f}ms)"
            else:
                cell = "N/A"
            print(f" {cell:>20}", end="")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("="*70)
    print("DEEP BENCHMARK: Sorting Algorithm Performance Analysis")
    print("="*70)
    print(f"Algorithms: {', '.join(ALGORITHMS.keys())}")
    print(f"Input types: {', '.join(GENERATORS.keys())}")
    print(f"Sizes: {SIZES}")
    print(f"Note: Bubble and Selection skipped for n > 500")
    print()

    print("Running benchmarks...")
    results = benchmark()
    print("Benchmarks complete.\n")

    # Run all analyses
    analysis_1(results, size=1000)
    analysis_2(results)
    analysis_3(results, size=1000)
    analysis_4(results)
    analysis_5(results)
    analysis_6(results)

    # Save to JSON
    import os
    out_path = os.path.join(os.path.dirname(__file__), "benchmark_data.json")
    # Convert int keys to strings for JSON
    def make_serializable(obj):
        if isinstance(obj, dict):
            return {str(k): make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(i) for i in obj]
        elif isinstance(obj, float) and math.isnan(obj):
            return None
        elif isinstance(obj, float) and math.isinf(obj):
            return None
        return obj

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(make_serializable(results), f, indent=2)

    print(f"\n{'='*70}")
    print(f"Results saved to: {out_path}")
    print("="*70)


if __name__ == "__main__":
    main()
