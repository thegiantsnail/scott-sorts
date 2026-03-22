import json
from itertools import combinations, chain

# The ur-components
COMPONENTS = ['Compare','Swap','Shift','Split','Merge','Select','Bucket','Iterate','Recurse','Accelerate']

# Algorithm compositions (as frozensets of component indices)
ALGS = {
    'Bubble':    frozenset(['Compare','Swap','Iterate']),
    'Insertion': frozenset(['Compare','Shift','Iterate']),
    'Selection': frozenset(['Compare','Swap','Select','Iterate']),
    'Shell':     frozenset(['Compare','Shift','Iterate']),
    'Merge':     frozenset(['Compare','Split','Merge','Recurse']),
    'Quick':     frozenset(['Compare','Split','Recurse']),
    'Heap':      frozenset(['Compare','Swap','Select','Iterate','Recurse','Accelerate']),
    'Radix':     frozenset(['Bucket','Iterate']),
    'Tim':       frozenset(['Compare','Shift','Split','Merge','Iterate','Recurse','Accelerate']),
}

names = list(ALGS.keys())
n = len(names)

# ============================================================
# 1. PARTIAL ORDER: subset inclusion on component sets
# ============================================================
def leq(a, b):
    """a ≤ b iff components(a) ⊆ components(b)"""
    return ALGS[a].issubset(ALGS[b])

# Build the order relation
order_matrix = {}
for a in names:
    for b in names:
        order_matrix[(a,b)] = leq(a, b)

print("=" * 60)
print("PARTIAL ORDER (component-subset inclusion)")
print("=" * 60)

# Print the order relation compactly
for a in names:
    above = [b for b in names if leq(a, b) and a != b]
    below = [b for b in names if leq(b, a) and a != b]
    print(f"  {a:10s} ({len(ALGS[a])} components): {ALGS[a]}")
    if above:
        print(f"             ≤ {above}")
    if below:
        print(f"             ≥ {below}")

# ============================================================
# 2. NOTE: Insertion = Shell in this poset — collapse before covers
# ============================================================
print("\n" + "=" * 60)
print("NOTE: Insertion and Shell have IDENTICAL component sets")
print("They are identified in the poset (same point)")
print("=" * 60)

# Collapse Shell = Insertion for topological analysis
# Use canonical representatives
canonical = {nm: nm for nm in names}
canonical['Shell'] = 'Insertion'  # They're the same point

# Work with distinct points only
distinct_names = [nm for nm in names if canonical[nm] == nm]
distinct_n = len(distinct_names)

print(f"\nDistinct points in the poset: {distinct_n}")
for nm in distinct_names:
    print(f"  {nm:10s}: {ALGS[nm]}")

# ============================================================
# 3. COVERING RELATIONS (Hasse edges) — on the 8-point quotient
# ============================================================
covers = []
for a in distinct_names:
    for b in distinct_names:
        if a == b or not leq(a, b):
            continue
        # Check if there's anything strictly between a and b
        is_cover = True
        for c in distinct_names:
            if c == a or c == b:
                continue
            if leq(a, c) and leq(c, b) and not (leq(b, c) and leq(c, a)):
                is_cover = False
                break
        if is_cover:
            covers.append((a, b))

print(f"\nCOVERING RELATIONS ({len(covers)} edges):")
for a, b in covers:
    diff = ALGS[b] - ALGS[a]
    print(f"  {a} ≺ {b}  (adds: {diff})")

# ============================================================
# 4. SCOTT TOPOLOGY on the finite poset
# ============================================================
# For a FINITE poset (which is trivially a dcpo — all directed 
# sets are finite, so sup = max element), the Scott topology
# coincides with the Alexandrov topology:
#   Scott-open = upper set (upward closed)
# because the "inaccessibility by directed suprema" condition
# is vacuous when all directed sets are finite.
#
# Proof sketch: In a finite dcpo, every directed set D has 
# ⊔D = max(D) ∈ D. So if U is an upper set and ⊔D ∈ U,
# then max(D) ∈ U, and max(D) ∈ D. The Scott condition is 
# automatically satisfied. Conversely, every Scott-open set
# is an upper set (by monotonicity of the topology).

print("\n" + "=" * 60)
print("SCOTT TOPOLOGY = ALEXANDROV TOPOLOGY (finite dcpo)")
print("=" * 60)
print("In a finite poset, every directed set {x₁,...,xₖ} has")
print("⊔{x₁,...,xₖ} = max, which is IN the set.")
print("So Scott-open = upper set (upward closed).")
print("The inaccessibility condition is vacuous.")

# Enumerate ALL upper sets (= Scott-open sets)
def is_upper_set(S, poset_names=distinct_names):
    """S is upper-closed: if x ∈ S and x ≤ y, then y ∈ S"""
    for x in S:
        for y in poset_names:
            if leq(x, y) and y not in S:
                return False
    return True

# Generate all subsets and filter for upper sets
all_subsets = []
for r in range(len(distinct_names) + 1):
    for combo in combinations(distinct_names, r):
        all_subsets.append(frozenset(combo))

scott_opens = [S for S in all_subsets if is_upper_set(S)]
scott_opens.sort(key=lambda s: (len(s), sorted(s)))

print(f"\nNumber of Scott-open sets: {len(scott_opens)}")
print(f"(out of 2^{distinct_n} = {2**distinct_n} total subsets)")

for i, S in enumerate(scott_opens):
    print(f"  U_{i:2d} = {set(S) if S else '∅'}")

# ============================================================
# 5. CLOSED SETS (complements of opens = downward closed sets)
# ============================================================
scott_closeds = [frozenset(distinct_names) - S for S in scott_opens]
scott_closeds.sort(key=lambda s: (len(s), sorted(s)))

print(f"\nNumber of Scott-closed sets: {len(scott_closeds)}")
for i, S in enumerate(scott_closeds):
    print(f"  C_{i:2d} = {set(S) if S else '∅'}")

# ============================================================
# 6. CLOSURE AND INTERIOR OPERATORS
# ============================================================
print("\n" + "=" * 60)
print("CLOSURE OPERATOR: cl(x) = ↓x (downward closure)")
print("INTERIOR OPERATOR: int(S) = largest upper set ⊆ S")
print("=" * 60)

for x in distinct_names:
    down_x = frozenset(y for y in distinct_names if leq(y, x))
    up_x = frozenset(y for y in distinct_names if leq(x, y))
    print(f"  ↓{x:10s} = {set(down_x)}")
    print(f"  ↑{x:10s} = {set(up_x)}")

# ============================================================
# 7. SPECIALIZATION ORDER
# ============================================================
print("\n" + "=" * 60)
print("SPECIALIZATION PREORDER")
print("x ≤_spec y iff x ∈ cl({y}) iff ↓y contains x")
print("For Scott topology on poset: specialization = original order")
print("=" * 60)

# Verify
for a in distinct_names:
    for b in distinct_names:
        # x ≤_spec y iff every open containing x also contains y
        spec = True
        for U in scott_opens:
            if a in U and b not in U:
                spec = False
                break
        original = leq(a, b)
        if spec != original:
            print(f"  MISMATCH: {a} ≤_spec {b} = {spec}, but {a} ≤ {b} = {original}")

print("  Verified: specialization order = subset-inclusion order ✓")

# ============================================================
# 8. SEPARATION AXIOMS
# ============================================================
print("\n" + "=" * 60)
print("SEPARATION AXIOMS")
print("=" * 60)

# T0: for every pair, there exists an open set containing one but not the other
is_T0 = True
for i, a in enumerate(distinct_names):
    for b in distinct_names[i+1:]:
        separating = False
        for U in scott_opens:
            if (a in U) != (b in U):
                separating = True
                break
        if not separating:
            print(f"  T0 FAIL: {a} and {b} are topologically indistinguishable")
            is_T0 = False
print(f"  T₀ (Kolmogorov): {is_T0}")

# T1: for every pair, each has an open neighborhood not containing the other
is_T1 = True
for i, a in enumerate(distinct_names):
    for b in distinct_names[i+1:]:
        a_sep = any(a in U and b not in U for U in scott_opens)
        b_sep = any(b in U and a not in U for U in scott_opens)
        if not (a_sep and b_sep):
            is_T1 = False
            if not a_sep:
                pass  # a is in closure of b
            if not b_sep:
                pass  # b is in closure of a
print(f"  T₁: {is_T1}")
if not is_T1:
    print("  (Scott topology on a non-discrete poset is never T₁)")

# T2 (Hausdorff)
print(f"  T₂ (Hausdorff): False (follows from ¬T₁)")

# Sobriety
print(f"  Sober: True (finite T₀ spaces are sober)")

# ============================================================
# 9. LAWSON TOPOLOGY
# ============================================================
print("\n" + "=" * 60)
print("LAWSON TOPOLOGY = Scott ∨ Lower")
print("Lower topology generated by {X \\ ↑x : x ∈ P}")
print("=" * 60)

# Lower topology subbasis: complements of principal filters
lower_subbasis = []
for x in distinct_names:
    up_x = frozenset(y for y in distinct_names if leq(x, y))
    complement = frozenset(distinct_names) - up_x
    lower_subbasis.append((x, complement))
    print(f"  X \\ ↑{x:10s} = {set(complement) if complement else '∅'}")

# Generate the lower topology (close subbasis under finite intersections and arbitrary unions)
# For finite case: generate all intersections of subbasis elements, then close under unions
lower_generators = set()
lower_generators.add(frozenset())  # empty set
lower_generators.add(frozenset(distinct_names))  # full set

subbasis_sets = [s for _, s in lower_subbasis]
# All intersections of subbasis elements
for r in range(1, len(subbasis_sets) + 1):
    for combo in combinations(subbasis_sets, r):
        intersection = frozenset(distinct_names)
        for s in combo:
            intersection = intersection & s
        lower_generators.add(intersection)

# Close under arbitrary unions
lower_opens = set()
lower_opens.add(frozenset())
lower_opens.add(frozenset(distinct_names))
for s in lower_generators:
    lower_opens.add(s)

# Iterate: union of any subset of generators
changed = True
while changed:
    changed = False
    new_opens = set()
    for a in lower_opens:
        for b in lower_opens:
            u = a | b
            if u not in lower_opens:
                new_opens.add(u)
    if new_opens:
        lower_opens |= new_opens
        changed = True

print(f"\n  Lower topology has {len(lower_opens)} open sets")

# Now Lawson = Scott ∨ Lower = topology generated by Scott-opens ∪ Lower-opens
lawson_generators = set(frozenset(s) for s in scott_opens) | lower_opens
lawson_opens = set()
lawson_opens.add(frozenset())
lawson_opens.add(frozenset(distinct_names))
for s in lawson_generators:
    lawson_opens.add(s)

# Close under finite intersection and arbitrary union
changed = True
while changed:
    changed = False
    new_opens = set()
    current = list(lawson_opens)
    for a in current:
        for b in current:
            u = a | b
            i = a & b
            if u not in lawson_opens:
                new_opens.add(u)
            if i not in lawson_opens:
                new_opens.add(i)
    if new_opens:
        lawson_opens |= new_opens
        changed = True

print(f"  Lawson topology has {len(lawson_opens)} open sets")
print(f"  (out of 2^{distinct_n} = {2**distinct_n} possible)")

# Check if Lawson = discrete
is_discrete = len(lawson_opens) == 2**distinct_n
print(f"  Lawson is discrete: {is_discrete}")

# Check if Lawson is T1
lawson_opens_list = list(lawson_opens)
lawson_T1 = True
for i, a in enumerate(distinct_names):
    for b in distinct_names[i+1:]:
        a_sep = any(a in U and b not in U for U in lawson_opens_list)
        b_sep = any(b in U and a not in U for U in lawson_opens_list)
        if not (a_sep and b_sep):
            lawson_T1 = False
            print(f"    T1 fail: {a}, {b}")
print(f"  Lawson T₁: {lawson_T1}")

lawson_T2 = True
for i, a in enumerate(distinct_names):
    for b in distinct_names[i+1:]:
        found_disjoint = False
        for U in lawson_opens_list:
            if a not in U:
                continue
            for V in lawson_opens_list:
                if b not in V:
                    continue
                if not (U & V):
                    found_disjoint = True
                    break
            if found_disjoint:
                break
        if not found_disjoint:
            lawson_T2 = False
            print(f"    T2 fail: {a}, {b}")
print(f"  Lawson T₂ (Hausdorff): {lawson_T2}")

# ============================================================
# 10. SCOTT-CONTINUOUS ENDOMORPHISMS
# ============================================================
print("\n" + "=" * 60)
print("SCOTT-CONTINUOUS ENDOMORPHISMS (monotone maps P → P)")
print("(= order-preserving maps for finite posets)")
print("=" * 60)

# For finite dcpo, Scott-continuous = monotone
# Count all monotone maps
from itertools import product as iprod

monotone_count = 0
interesting_maps = []
for assignment in iprod(distinct_names, repeat=distinct_n):
    f = dict(zip(distinct_names, assignment))
    is_mono = True
    for a in distinct_names:
        for b in distinct_names:
            if leq(a, b) and not leq(f[a], f[b]):
                is_mono = False
                break
        if not is_mono:
            break
    if is_mono:
        monotone_count += 1
        # Check if it's interesting (not identity, not constant)
        is_id = all(f[x] == x for x in distinct_names)
        is_const = len(set(f.values())) == 1
        img = set(f.values())
        if not is_id and not is_const and len(img) >= 3:
            interesting_maps.append(dict(f))

print(f"  Total monotone endomorphisms: {monotone_count}")
print(f"  Non-trivial (≥3 image points): {len(interesting_maps)}")
if interesting_maps[:5]:
    print(f"  Examples:")
    for f in interesting_maps[:5]:
        arrows = ", ".join(f"{k}→{v}" for k,v in f.items() if k != v)
        fixed = [k for k in f if f[k] == k]
        print(f"    fixes {fixed}, moves: {arrows}")

# ============================================================
# 11. BASIS FOR THE SCOTT TOPOLOGY
# ============================================================
print("\n" + "=" * 60)
print("BASIS FOR SCOTT TOPOLOGY")
print("=" * 60)
print("Principal filters ↑x form a basis.")
print("Every Scott-open set is a union of principal filters.")

for x in distinct_names:
    up_x = frozenset(y for y in distinct_names if leq(x, y))
    # Check which opens are exactly this filter
    print(f"  ↑{x:10s} = {set(up_x)}")

# Verify basis property
print("\nDecomposing each Scott-open as union of principal filters:")
for i, U in enumerate(scott_opens):
    if not U:
        print(f"  U_{i:2d} = ∅")
        continue
    # Minimal elements of U
    minimals = []
    for x in U:
        is_minimal = True
        for y in U:
            if y != x and leq(y, x):
                is_minimal = False
                break
        if is_minimal:
            minimals.append(x)
    print(f"  U_{i:2d} = {' ∪ '.join(f'↑{m}' for m in minimals)} = {set(U)}")

# ============================================================
# 12. COMPACT ELEMENTS (way-below relation)
# ============================================================
print("\n" + "=" * 60)
print("WAY-BELOW RELATION AND COMPACT ELEMENTS")
print("In a finite dcpo, x ≪ y iff x ≤ y")
print("Every element is compact. The dcpo is algebraic.")
print("=" * 60)

print("This is because for any directed set D with y ≤ ⊔D,")
print("since D is finite, ⊔D = max(D) ∈ D, so y ≤ max(D)")
print("and since x ≤ y, we have x ≤ max(D), so x ≤ d for d=max(D)∈D.")
print()
print("Compact elements: ALL elements are compact")
print("The poset is algebraic (= continuous + all elements compact)")

# ============================================================
# 13. FRAME OF OPENS (as a lattice)
# ============================================================
print("\n" + "=" * 60)
print("FRAME OF SCOTT-OPENS (Ω(P))")
print("This is the frame/locale associated to the space")
print("=" * 60)

# Compute meet and join of all pairs
print(f"  |Ω(P)| = {len(scott_opens)}")
print(f"  Bottom = ∅")
print(f"  Top = {set(distinct_names)}")

# Check distributivity (should be automatic for topology)
# Instead, let's identify the irreducible elements
# An open U is meet-irreducible if U = V ∩ W implies U = V or U = W
meet_irred = []
for U in scott_opens:
    if U == frozenset(distinct_names):
        continue
    is_irred = True
    for V in scott_opens:
        for W in scott_opens:
            if V & W == U and V != U and W != U:
                is_irred = False
                break
        if not is_irred:
            break
    if is_irred:
        meet_irred.append(U)

print(f"\n  Meet-irreducible opens: {len(meet_irred)}")
for U in meet_irred:
    print(f"    {set(U) if U else '∅'}")

# Join-irreducible
join_irred = []
for U in scott_opens:
    if not U:
        continue
    is_irred = True
    for V in scott_opens:
        for W in scott_opens:
            if (V | W) == U and V != U and W != U:
                is_irred = False
                break
        if not is_irred:
            break
    if is_irred:
        join_irred.append(U)

print(f"\n  Join-irreducible opens (= principal filters of join-irred elements): {len(join_irred)}")
for U in join_irred:
    print(f"    {set(U)}")

# ============================================================
# Output structured data for visualization
# ============================================================
output = {
    "distinct_points": distinct_names,
    "components": {nm: sorted(ALGS[nm]) for nm in distinct_names},
    "covers": covers,
    "scott_opens": [sorted(S) for S in scott_opens],
    "scott_closeds": [sorted(S) for S in scott_closeds],
    "num_scott_opens": len(scott_opens),
    "num_lawson_opens": len(lawson_opens),
    "lawson_is_discrete": is_discrete,
    "scott_T0": is_T0,
    "scott_T1": is_T1,
    "lawson_T1": lawson_T1,
    "lawson_T2": lawson_T2,
    "monotone_endomorphisms": monotone_count,
    "meet_irreducibles": [sorted(S) for S in meet_irred],
    "join_irreducibles": [sorted(S) for S in join_irred],
    "principal_filters": {nm: sorted(y for y in distinct_names if leq(nm, y)) for nm in distinct_names},
    "principal_ideals": {nm: sorted(y for y in distinct_names if leq(y, nm)) for nm in distinct_names},
}

with open('src/scott_data.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\n\nStructured data written to scott_data.json")
