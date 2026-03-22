"""
Sort Compiler: Source-to-source transformation via Scott-topology operators.

Applies the named endomorphisms of the sorting-algorithm poset as
source-to-source transformations.  For each (source_algorithm, operator)
pair the compiler outputs:

  * the target algorithm (the image of the endomorphism)
  * which ur-components were added or stripped
  * an AST-level structural diff (function count, recursion, loop depth, …)
  * the canonical Python implementation of the target algorithm
  * a verification that every named operator is genuinely Scott-continuous
    (monotone), and a proof that the "de-accelerate" counter-example is not

The 8 interior operators are contractive+idempotent+monotone: they are the
de-optimization paths that stay within the Scott topology.
The 32 closure operators are extensive+idempotent+monotone: the optimization
paths.  "de_accelerate" (Heap→Selection, Tim→Merge) is shown to violate
monotonicity — establishing the topological asymmetry proved in Section 7.3.
"""

import ast
import sys

# Ensure Unicode output works on Windows consoles (same fix as run_all.sh)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─────────────────────────────────────────────────────────────────────────────
# 1.  Poset  (identical to endomorphism_analysis.py)
# ─────────────────────────────────────────────────────────────────────────────

NAMES = ['Bubble', 'Insertion', 'Selection', 'Quick', 'Merge', 'Heap', 'Radix', 'Tim']

COMPS = {
    'Bubble':    frozenset(['Compare', 'Swap', 'Iterate']),
    'Insertion': frozenset(['Compare', 'Shift', 'Iterate']),
    'Selection': frozenset(['Compare', 'Swap', 'Select', 'Iterate']),
    'Quick':     frozenset(['Compare', 'Split', 'Recurse']),
    'Merge':     frozenset(['Compare', 'Split', 'Merge', 'Recurse']),
    'Heap':      frozenset(['Compare', 'Swap', 'Select', 'Iterate', 'Recurse', 'Accelerate']),
    'Radix':     frozenset(['Bucket', 'Iterate']),
    'Tim':       frozenset(['Compare', 'Shift', 'Split', 'Merge', 'Iterate', 'Recurse', 'Accelerate']),
}


def leq(a, b):
    return COMPS[a].issubset(COMPS[b])


def is_monotone(op):
    """Return (True, None) if op is monotone, else (False, counterexample)."""
    for a in NAMES:
        for b in NAMES:
            if leq(a, b) and not leq(op[a], op[b]):
                return False, (a, b, op[a], op[b])
    return True, None


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Canonical implementations
# ─────────────────────────────────────────────────────────────────────────────

IMPL = {

'Bubble': '''\
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break
    return arr''',

'Insertion': '''\
def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr''',

'Selection': '''\
def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr''',

'Quick': '''\
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left   = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right  = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)''',

'Merge': '''\
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid   = len(arr) // 2
    left  = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return _merge(left, right)

def _merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result''',

'Heap': '''\
def heap_sort(arr):
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        _heapify(arr, n, i)
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        _heapify(arr, i, 0)
    return arr

def _heapify(arr, n, i):
    largest = i
    left  = 2 * i + 1
    right = 2 * i + 2
    if left  < n and arr[left]  > arr[largest]: largest = left
    if right < n and arr[right] > arr[largest]: largest = right
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        _heapify(arr, n, largest)''',

'Radix': '''\
def radix_sort(arr):
    if not arr:
        return arr
    max_val = max(arr)
    exp = 1
    while max_val // exp > 0:
        _counting_sort_by_digit(arr, exp)
        exp *= 10
    return arr

def _counting_sort_by_digit(arr, exp):
    n      = len(arr)
    output = [0] * n
    count  = [0] * 10
    for i in range(n):
        count[arr[i] // exp % 10] += 1
    for i in range(1, 10):
        count[i] += count[i - 1]
    for i in range(n - 1, -1, -1):
        idx = arr[i] // exp % 10
        output[count[idx] - 1] = arr[i]
        count[idx] -= 1
    for i in range(n):
        arr[i] = output[i]''',

'Tim': '''\
def tim_sort(arr):
    MIN_RUN = 32
    n = len(arr)
    for start in range(0, n, MIN_RUN):
        _insertion_run(arr, start, min(start + MIN_RUN - 1, n - 1))
    size = MIN_RUN
    while size < n:
        for left in range(0, n, 2 * size):
            mid   = min(left + size - 1, n - 1)
            right = min(left + 2 * size - 1, n - 1)
            if mid < right:
                _merge_inplace(arr, left, mid, right)
        size *= 2
    return arr

def _insertion_run(arr, left, right):
    for i in range(left + 1, right + 1):
        key = arr[i]
        j   = i - 1
        while j >= left and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key

def _merge_inplace(arr, left, mid, right):
    lpart = arr[left:mid + 1]
    rpart = arr[mid + 1:right + 1]
    i = j = 0
    k = left
    while i < len(lpart) and j < len(rpart):
        if lpart[i] <= rpart[j]:
            arr[k] = lpart[i]; i += 1
        else:
            arr[k] = rpart[j]; j += 1
        k += 1
    while i < len(lpart):
        arr[k] = lpart[i]; i += 1; k += 1
    while j < len(rpart):
        arr[k] = rpart[j]; j += 1; k += 1''',
}


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Operator catalogue
#
# All 8 interior operators are derived analytically (Section 3 of the proof):
#
#   Forced fixed points (minimal / isolated): Bubble, Insertion, Quick, Radix, Tim
#   Free choices with monotonicity + idempotency constraints:
#     f(Selection) ∈ {Bubble, Selection}
#     f(Heap)      ∈ {Bubble, Selection, Heap}   (Selection→Heap forces Selection fixed)
#     f(Merge)     ∈ {Quick, Merge}
#
#   Constraint: f(Bubble)≤f(Selection) forces:
#     f(Heap)=Bubble  →  f(Selection)=Bubble
#     f(Heap)=Selection → f(Selection)=Selection
#
#   The 8 combinations (labelled by the "free" bits) are enumerated below.
# ─────────────────────────────────────────────────────────────────────────────

_F = {'Bubble': 'Bubble', 'Insertion': 'Insertion', 'Quick': 'Quick',
      'Radix': 'Radix', 'Tim': 'Tim'}   # forced fixed points

INTERIOR_OPS = {
    # name : short description
    # (Selection→?,  Heap→?,       Merge→?)
    'simplify_all':             ('Bubble',    'Bubble',    'Quick'),
    'strip_select':             ('Bubble',    'Bubble',    'Merge'),
    'degrade_heap_strip_merge': ('Selection', 'Selection', 'Quick'),
    'degrade_heap':             ('Selection', 'Selection', 'Merge'),
    'strip_both':               ('Bubble',    'Heap',      'Quick'),
    'strip_select_only':        ('Bubble',    'Heap',      'Merge'),
    'strip_merge_only':         ('Selection', 'Heap',      'Quick'),
    'identity':                 ('Selection', 'Heap',      'Merge'),
}

def _make_interior(sel, heap, merge):
    return {**_F, 'Selection': sel, 'Heap': heap, 'Merge': merge}

INTERIOR = {name: _make_interior(*vals) for name, vals in INTERIOR_OPS.items()}

# ─────────────────────────────────────────────────────────────────────────────
# Representative closure operators (extensive + idempotent + monotone).
# All 32 exist, but the semantically interesting ones are listed here.
# Each is characterised by the covering-relation "upgrade bits" it activates.
# ─────────────────────────────────────────────────────────────────────────────

_U = {'Heap': 'Heap', 'Tim': 'Tim', 'Radix': 'Radix'}   # always maximal / fixed

CLOSURE = {
    # name : {alg: target, …}

    'identity': {
        **_U,
        'Bubble': 'Bubble', 'Insertion': 'Insertion', 'Selection': 'Selection',
        'Quick':  'Quick',  'Merge':     'Merge',
    },

    # ── Single upgrade decisions ──────────────────────────────────────────

    # Bubble ≺ Selection  (add Select)
    'add_select': {
        **_U,
        'Bubble': 'Selection', 'Insertion': 'Insertion', 'Selection': 'Selection',
        'Quick':  'Quick',     'Merge':     'Merge',
    },

    # Selection ≺ Heap  (add Recurse + Accelerate)
    'add_heap_from_selection': {
        **_U,
        'Bubble': 'Bubble',    'Insertion': 'Insertion', 'Selection': 'Heap',
        'Quick':  'Quick',     'Merge':     'Merge',
    },

    # Quick ≺ Merge  (add Merge combinator)
    'add_merge': {
        **_U,
        'Bubble': 'Bubble', 'Insertion': 'Insertion', 'Selection': 'Selection',
        'Quick':  'Merge',  'Merge':     'Merge',
    },

    # Merge ≺ Tim  (add Shift + Iterate + Accelerate)
    'add_run_merge': {
        **_U,
        'Bubble': 'Bubble', 'Insertion': 'Insertion', 'Selection': 'Selection',
        'Quick':  'Quick',  'Merge':     'Tim',
    },

    # Insertion ≺ Tim  (add Split + Merge + Recurse + Accelerate)
    'recursify_insertion': {
        **_U,
        'Bubble': 'Bubble', 'Insertion': 'Tim',       'Selection': 'Selection',
        'Quick':  'Quick',  'Merge':     'Merge',
    },

    # ── Combined upgrades ────────────────────────────────────────────────

    # Quick → Tim  (add Merge combinator then Shift + Iterate + Accelerate)
    'fully_recursify': {
        **_U,
        'Bubble': 'Bubble', 'Insertion': 'Tim',       'Selection': 'Selection',
        'Quick':  'Tim',    'Merge':     'Tim',
    },

    # Maximize: map every algorithm to the most complex point above it
    'maximize': {
        **_U,
        'Bubble':    'Heap',  # max above Bubble in ↑Bubble = Heap
        'Insertion': 'Tim',   # max above Insertion in ↑Insertion = Tim
        'Selection': 'Heap',  # max above Selection = Heap
        'Quick':     'Tim',   # max above Quick = Tim
        'Merge':     'Tim',   # max above Merge = Tim
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Non-continuous counter-example (Section 7.3)
# Heap → Selection, Tim → Merge.
# Violates monotonicity: Insertion ≤ Tim but f(Insertion)=Insertion ⊄ Merge=f(Tim)
# ─────────────────────────────────────────────────────────────────────────────

DEACCEL = {x: x for x in NAMES}
DEACCEL['Heap'] = 'Selection'
DEACCEL['Tim']  = 'Merge'


# ─────────────────────────────────────────────────────────────────────────────
# 4.  AST structural analysis
# ─────────────────────────────────────────────────────────────────────────────

def ast_signature(source):
    """
    Extract structural features from Python source using the ast module.
    Returns a dict of counts comparable across algorithms.
    """
    tree = ast.parse(source)

    sig = {
        'func_defs':          0,
        'recursive_calls':    0,
        'loops':              0,
        'max_loop_depth':     0,
        'list_comprehensions':0,
        'slices':             0,
        'swaps':              0,
        'comparisons':        0,
    }

    func_names: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_names.add(node.name)
            sig['func_defs'] += 1

    def _walk(node, depth):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While)):
                sig['loops'] += 1
                sig['max_loop_depth'] = max(sig['max_loop_depth'], depth + 1)
                _walk(child, depth + 1)
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and child.func.id in func_names:
                    sig['recursive_calls'] += 1
                _walk(child, depth)
            elif isinstance(child, ast.ListComp):
                sig['list_comprehensions'] += 1
                _walk(child, depth)
            elif isinstance(child, ast.Subscript):
                if isinstance(child.slice, ast.Slice):
                    sig['slices'] += 1
                _walk(child, depth)
            elif isinstance(child, ast.Assign):
                # Detect tuple-swap:  a, b = b, a
                if (isinstance(child.value, ast.Tuple) and
                        len(child.targets) == 1 and
                        isinstance(child.targets[0], ast.Tuple)):
                    sig['swaps'] += 1
                _walk(child, depth)
            elif isinstance(child, ast.Compare):
                sig['comparisons'] += 1
                _walk(child, depth)
            else:
                _walk(child, depth)

    _walk(tree, 0)
    return sig


def structural_diff(src_alg, tgt_alg):
    """
    Return a dict of {feature: (src_val, tgt_val, delta)} for features that
    differ between the two canonical implementations.
    """
    src_sig = ast_signature(IMPL[src_alg])
    tgt_sig = ast_signature(IMPL[tgt_alg])
    diff = {}
    for k in src_sig:
        d = tgt_sig[k] - src_sig[k]
        if d != 0:
            diff[k] = (src_sig[k], tgt_sig[k], d)
    return diff


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Compiler entry point
# ─────────────────────────────────────────────────────────────────────────────

def compile_transform(source_alg, op_map, op_name=''):
    """
    Apply an endomorphism to a sorting algorithm.

    Returns a dict:
      source          – input algorithm name
      target          – output algorithm name (image under the endomorphism)
      op              – operator name
      continuous      – True iff the operator is monotone (Scott-continuous)
      violation       – counterexample tuple if not continuous, else None
      components_removed – sorted list of stripped ur-components
      components_added   – sorted list of gained ur-components
      ast_diff           – structural AST delta (only changed features)
      output_code        – canonical Python source of the target algorithm
    """
    mono, violation = is_monotone(op_map)
    target_alg = op_map[source_alg]
    removed = sorted(COMPS[source_alg] - COMPS[target_alg])
    added   = sorted(COMPS[target_alg] - COMPS[source_alg])
    diff    = structural_diff(source_alg, target_alg)

    return {
        'source':             source_alg,
        'target':             target_alg,
        'op':                 op_name,
        'continuous':         mono,
        'violation':          violation,
        'components_removed': removed,
        'components_added':   added,
        'ast_diff':           diff,
        'output_code':        IMPL[target_alg],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Pretty-print
# ─────────────────────────────────────────────────────────────────────────────

def _hr(char='─', width=70):
    print(char * width)

def _print_result(r, show_code=True):
    src, tgt, op = r['source'], r['target'], r['op']
    tag = 'Scott-continuous' if r['continuous'] else '*** NOT CONTINUOUS ***'

    if src == tgt:
        print(f"    {src}  [fixed point — no change]")
        return

    print(f"    {src}  ──[{op}]──►  {tgt}    ({tag})")
    print(f"      components({src:9s}) = {sorted(COMPS[src])}")
    print(f"      components({tgt:9s}) = {sorted(COMPS[tgt])}")
    if r['components_removed']:
        print(f"      stripped  : {r['components_removed']}")
    if r['components_added']:
        print(f"      added     : {r['components_added']}")

    if not r['continuous'] and r['violation']:
        a, b, fa, fb = r['violation']
        print(f"      VIOLATION : {a} ≤ {b} in P  but  "
              f"f({a})={fa} ⊄ {fb}=f({b})")
        print(f"        ({sorted(COMPS[fa] - COMPS[fb])} present in "
              f"f({a}) but not in f({b}))")

    if r['ast_diff']:
        print(f"      AST delta :")
        for feat, (sv, tv, d) in r['ast_diff'].items():
            sign = f"+{d}" if d > 0 else str(d)
            label = {
                'func_defs':           'helper functions',
                'recursive_calls':     'recursive calls',
                'loops':               'loops',
                'max_loop_depth':      'max loop depth',
                'list_comprehensions': 'list comprehensions',
                'slices':              'slices',
                'swaps':               'tuple swaps',
                'comparisons':         'comparison nodes',
            }.get(feat, feat)
            print(f"        {label:25s}: {sv} → {tv}  ({sign})")

    if show_code:
        print(f"\n      ── output code ({tgt}) " + "─" * 40)
        for line in r['output_code'].split('\n'):
            print(f"      {line}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# 7.  Operator self-verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_all_operators():
    print("=" * 70)
    print("OPERATOR VERIFICATION")
    print("=" * 70)

    all_ok = True

    print("\nInterior operators (contractive + idempotent + monotone):")
    for name, op in INTERIOR.items():
        mono, viol = is_monotone(op)
        # Verify contractive
        contractive = all(leq(op[x], x) for x in NAMES)
        # Verify idempotent (every image element is a fixed point)
        idempotent  = all(op[op[x]] == op[x] for x in NAMES)
        ok = mono and contractive and idempotent
        if not ok:
            all_ok = False
        status = "OK" if ok else f"FAIL mono={mono} contr={contractive} idemp={idempotent}"
        print(f"  {name:30s}  {status}")

    print("\nClosure operators (extensive + idempotent + monotone):")
    for name, op in CLOSURE.items():
        mono, viol = is_monotone(op)
        extensive  = all(leq(x, op[x]) for x in NAMES)
        idempotent = all(op[op[x]] == op[x] for x in NAMES)
        ok = mono and extensive and idempotent
        if not ok:
            all_ok = False
        status = "OK" if ok else f"FAIL mono={mono} ext={extensive} idemp={idempotent}"
        print(f"  {name:30s}  {status}")

    print("\nDiscontinuous counter-example (de_accelerate):")
    mono, viol = is_monotone(DEACCEL)
    print(f"  de_accelerate  monotone={mono}")
    if viol:
        a, b, fa, fb = viol
        print(f"    Witness: {a} ≤ {b}  but  f({a})={fa} ⊄ {fb}=f({b})")
        diff_comps = sorted(COMPS[fa] - COMPS[fb])
        print(f"    Components in f({a}) missing from f({b}): {diff_comps}")

    result = "All operators verified OK." if all_ok else "ERRORS found — see above."
    print(f"\n{result}")
    return all_ok


# ─────────────────────────────────────────────────────────────────────────────
# 8.  Demo
# ─────────────────────────────────────────────────────────────────────────────

def run_demo():
    print("=" * 70)
    print("SORT COMPILER — Scott-Topology Source-to-Source Transformations")
    print("=" * 70)

    # ── Interior operators: de-optimization paths ─────────────────────────
    print("\n" + "─" * 70)
    print("INTERIOR OPERATORS  (de-optimization, always Scott-continuous)")
    print("─" * 70)

    # The two semantically richest interior transforms
    demos_interior = [
        ('degrade_heap',     'Heap',      True),
        ('degrade_heap',     'Tim',       True),
        ('strip_merge_only', 'Merge',     True),
        ('simplify_all',     'Heap',      True),
        ('simplify_all',     'Tim',       True),
    ]
    for op_name, src, show_code in demos_interior:
        r = compile_transform(src, INTERIOR[op_name], op_name)
        _print_result(r, show_code=show_code)

    # ── Closure operators: optimization paths ────────────────────────────
    print("\n" + "─" * 70)
    print("CLOSURE OPERATORS  (optimization, always Scott-continuous)")
    print("─" * 70)

    demos_closure = [
        ('add_merge',            'Quick',     True),
        ('recursify_insertion',  'Insertion', True),
        ('add_run_merge',        'Merge',     True),
        ('maximize',             'Bubble',    True),
        ('maximize',             'Quick',     True),
    ]
    for op_name, src, show_code in demos_closure:
        r = compile_transform(src, CLOSURE[op_name], op_name)
        _print_result(r, show_code=show_code)

    # ── Discontinuous counter-example ────────────────────────────────────
    print("\n" + "─" * 70)
    print("DISCONTINUOUS COUNTER-EXAMPLE  (Section 7.3)")
    print("de_accelerate: Heap→Selection, Tim→Merge")
    print("─" * 70)
    print()

    for src in ['Heap', 'Tim', 'Insertion']:
        r = compile_transform(src, DEACCEL, 'de_accelerate')
        _print_result(r, show_code=False)

    print("  Conclusion: de_accelerate tears the partial order.")
    print("  It cannot be Scott-continuous (Insertion ≤ Tim, but")
    print("  Insertion ⊄ Merge — the 'Shift' component is lost).")

    # ── Full operator × algorithm table ─────────────────────────────────
    print("\n" + "─" * 70)
    print("FULL COMPILATION TABLE  (operator × source → target)")
    print("─" * 70)
    all_ops = (
        [(n, op, 'interior') for n, op in INTERIOR.items()] +
        [(n, op, 'closure')  for n, op in CLOSURE.items()]
    )
    col = max(len(n) for n, _, _ in all_ops)
    header = f"  {'operator':{col}}  " + "  ".join(f"{nm[:4]:4s}" for nm in NAMES)
    print(header)
    print("  " + "─" * (len(header) - 2))
    for op_name, op, kind in all_ops:
        row = f"  {op_name:{col}}  "
        for nm in NAMES:
            tgt = op[nm]
            cell = tgt[:4] if tgt != nm else '·   '
            row += f"{cell:4s}  "
        row += f"  [{kind[0]}]"
        print(row)


if __name__ == '__main__':
    ok = verify_all_operators()
    print()
    run_demo()
    sys.exit(0 if ok else 1)
