import json
from itertools import product as iprod
from collections import Counter, defaultdict

NAMES = ['Bubble','Insertion','Selection','Quick','Merge','Heap','Radix','Tim']
COMPS = {
    'Bubble': frozenset(['Compare','Swap','Iterate']),
    'Insertion': frozenset(['Compare','Shift','Iterate']),
    'Selection': frozenset(['Compare','Swap','Select','Iterate']),
    'Quick': frozenset(['Compare','Split','Recurse']),
    'Merge': frozenset(['Compare','Split','Merge','Recurse']),
    'Heap': frozenset(['Compare','Swap','Select','Iterate','Recurse','Accelerate']),
    'Radix': frozenset(['Bucket','Iterate']),
    'Tim': frozenset(['Compare','Shift','Split','Merge','Iterate','Recurse','Accelerate']),
}

def leq(a, b):
    return COMPS[a].issubset(COMPS[b])

# ============================================================
# 1. ENUMERATE ALL MONOTONE ENDOMORPHISMS
# ============================================================
print("Enumerating all monotone endomorphisms...")
endomorphisms = []
for assignment in iprod(NAMES, repeat=len(NAMES)):
    f = dict(zip(NAMES, assignment))
    is_mono = True
    for a in NAMES:
        for b in NAMES:
            if leq(a, b) and not leq(f[a], f[b]):
                is_mono = False
                break
        if not is_mono:
            break
    if is_mono:
        endomorphisms.append(f)

print(f"Total monotone endomorphisms: {len(endomorphisms)}")

# ============================================================
# 2. DO THEY PRESERVE "SORTS CORRECTLY"?
# ============================================================
# Every algorithm in P sorts correctly. The question is whether
# f(alg) also sorts correctly. Since f maps P -> P and every
# element of P is a correct sorting algorithm, YES — every
# endomorphism maps sorts to sorts.
#
# BUT the deeper question is about SEMANTIC preservation:
# does the *composition of components* still make sense?

print("\n" + "="*60)
print("SEMANTIC PRESERVATION ANALYSIS")
print("="*60)

# Key property: does f preserve the "produces sorted output" invariant?
# Since every element of P is a sorting algorithm, f(x) ∈ P always sorts.
# But does f preserve component-level structure?

# Check: does f preserve the "comparison-based" property?
comparison_based = {nm for nm in NAMES if 'Compare' in COMPS[nm]}
non_comparison = {nm for nm in NAMES if 'Compare' not in COMPS[nm]}  # Just Radix

preserves_comparison = 0
sends_comp_to_noncomp = 0
sends_noncomp_to_comp = 0

for f in endomorphisms:
    comp_ok = all(f[x] in comparison_based for x in comparison_based)
    if comp_ok:
        preserves_comparison += 1
    if any(f[x] in non_comparison for x in comparison_based):
        sends_comp_to_noncomp += 1
    if f['Radix'] in comparison_based:
        sends_noncomp_to_comp += 1

print(f"  Preserve comparison-based: {preserves_comparison}/{len(endomorphisms)}")
print(f"  Send some comparison→non-comparison: {sends_comp_to_noncomp}")
print(f"  Send Radix→comparison-based: {sends_noncomp_to_comp}")

# Check: does f preserve recursion structure?
recursive = {nm for nm in NAMES if 'Recurse' in COMPS[nm]}
iterative_only = {nm for nm in NAMES if 'Recurse' not in COMPS[nm]}

preserves_recursive = sum(1 for f in endomorphisms 
    if all(f[x] in recursive for x in recursive))
preserves_iterative = sum(1 for f in endomorphisms
    if all(f[x] in iterative_only for x in iterative_only))
preserves_both = sum(1 for f in endomorphisms
    if all(f[x] in recursive for x in recursive) and 
       all(f[x] in iterative_only for x in iterative_only))

print(f"  Preserve recursive→recursive: {preserves_recursive}")
print(f"  Preserve iterative→iterative: {preserves_iterative}")
print(f"  Preserve both (respects recursion boundary): {preserves_both}")

# Check: in-place preservation
in_place = {nm for nm in NAMES if 'Swap' in COMPS[nm] or 
            (nm in ['Insertion','Shell'] and 'Shift' in COMPS[nm])}
# Bubble, Selection, Heap, Insertion are in-place
# Actually let's be precise about mutation
mutates = {'Bubble','Insertion','Selection','Heap','Shell','Radix'}
functional = {'Quick','Merge'}  
hybrid = {'Tim'}  # both

print(f"\n  In-place mutators: {mutates & set(NAMES)}")
print(f"  Functional (new allocation): {functional}")
print(f"  Hybrid: {hybrid}")

# ============================================================
# 3. CLASSIFY BY STRUCTURAL PROPERTIES
# ============================================================
print("\n" + "="*60)
print("STRUCTURAL CLASSIFICATION")
print("="*60)

# Image size
image_sizes = Counter()
for f in endomorphisms:
    img = frozenset(f.values())
    image_sizes[len(img)] += 1

print("\nBy image size |im(f)|:")
for sz in sorted(image_sizes):
    print(f"  |im(f)| = {sz}: {image_sizes[sz]} maps")

# Fixed points
fixed_point_counts = Counter()
for f in endomorphisms:
    fp = sum(1 for x in NAMES if f[x] == x)
    fixed_point_counts[fp] += 1

print("\nBy number of fixed points:")
for fp in sorted(fixed_point_counts):
    print(f"  {fp} fixed points: {fixed_point_counts[fp]} maps")

# ============================================================
# 4. AUTOMORPHISM GROUP
# ============================================================
print("\n" + "="*60)
print("AUTOMORPHISM GROUP Aut(P)")
print("="*60)

automorphisms = []
for f in endomorphisms:
    if len(set(f.values())) == len(NAMES):  # bijective
        # Check if inverse is also monotone (automatic for bijective monotone on finite posets 
        # only if it's an order-isomorphism)
        inv = {v: k for k, v in f.items()}
        is_auto = True
        for a in NAMES:
            for b in NAMES:
                if leq(a, b) and not leq(inv[a], inv[b]):
                    is_auto = False
                    break
            if not is_auto:
                break
        if is_auto:
            automorphisms.append(f)

print(f"  |Aut(P)| = {len(automorphisms)}")
for f in automorphisms:
    mapping = {k: v for k, v in f.items() if k != v}
    if not mapping:
        print(f"    Identity")
    else:
        print(f"    {mapping}")

# ============================================================
# 5. IDEMPOTENTS (f∘f = f) — these are "retractions"
# ============================================================
print("\n" + "="*60)
print("IDEMPOTENTS (f² = f) — retractions onto sub-posets")
print("="*60)

idempotents = []
for f in endomorphisms:
    is_idemp = True
    for x in NAMES:
        if f[f[x]] != f[x]:
            is_idemp = False
            break
    if is_idemp:
        idempotents.append(f)

print(f"  Number of idempotents: {len(idempotents)}")

# Classify idempotents by their image (which is a retract of P)
idemp_by_image = defaultdict(list)
for f in idempotents:
    img = frozenset(f.values())
    idemp_by_image[img].append(f)

print(f"  Distinct retract images: {len(idemp_by_image)}")
print(f"\n  Retract images (sub-posets that P retracts onto):")
for img in sorted(idemp_by_image, key=lambda s: (len(s), sorted(s))):
    count = len(idemp_by_image[img])
    print(f"    {sorted(img)} — {count} retraction(s)")

# ============================================================
# 6. NATURAL FAMILIES / SUBMONOIDS
# ============================================================
print("\n" + "="*60)
print("NATURAL FAMILIES")
print("="*60)

# Family 1: Constant maps
constants = [f for f in endomorphisms if len(set(f.values())) == 1]
print(f"\n  Constant maps: {len(constants)}")
# Which elements can be constant images? Only minimal elements work
# Actually for monotone: f constant at c means c must be comparable to everything
# that f(x) = c for all x, need c ≤ c always (trivial) but also
# if x ≤ y then f(x) ≤ f(y), i.e., c ≤ c. Always true.
# Wait - any constant map IS monotone. So |constants| = |P| = 8
const_vals = [list(set(f.values()))[0] for f in constants]
print(f"    Constant images: {sorted(set(const_vals))}")

# Family 2: Closure operators (monotone, extensive: x ≤ f(x), idempotent)
closures = []
for f in idempotents:
    if all(leq(x, f[x]) for x in NAMES):
        closures.append(f)
print(f"\n  Closure operators (monotone + extensive + idempotent): {len(closures)}")
for f in closures:
    img = sorted(set(f.values()))
    mapping = {k:v for k,v in f.items() if k != v}
    print(f"    image={img}, moves: {mapping}")

# Family 3: Interior operators (monotone, contractive: f(x) ≤ x, idempotent)
interiors = []
for f in idempotents:
    if all(leq(f[x], x) for x in NAMES):
        interiors.append(f)
print(f"\n  Interior (kernel) operators (monotone + contractive + idempotent): {len(interiors)}")
for f in interiors[:20]:
    img = sorted(set(f.values()))
    mapping = {k:v for k,v in f.items() if k != v}
    print(f"    image={img}, moves: {mapping}")

# Family 4: Maps that preserve maximal elements
maximal = [x for x in NAMES if not any(leq(x, y) and x != y and not leq(y, x) for y in NAMES)]
print(f"\n  Maximal elements: {maximal}")
preserves_max = sum(1 for f in endomorphisms if all(f[x] in maximal for x in maximal))
print(f"  Maps preserving maximals: {preserves_max}")

# Family 5: Maps that preserve minimal elements
minimal = [x for x in NAMES if not any(leq(y, x) and x != y and not leq(x, y) for y in NAMES)]
print(f"\n  Minimal elements: {minimal}")
preserves_min = sum(1 for f in endomorphisms if all(f[x] in minimal for x in minimal))
print(f"  Maps preserving minimals: {preserves_min}")

# ============================================================
# 7. COMPONENT SEMANTICS OF KEY ENDOMORPHISMS
# ============================================================
print("\n" + "="*60)
print("SEMANTICALLY MEANINGFUL ENDOMORPHISMS")
print("="*60)

# "Forget recursion" — map everything to its iterative counterpart
# This would mean: Quick → ?, Merge → ?, Heap → ?, Tim → ?
# But these don't have natural iterative counterparts in our poset
# We need maps that are interpretable

# "Simplify" — map each algorithm to the simplest one below it
def simplify_map():
    f = {}
    for x in NAMES:
        # Find minimal elements below x
        below = [y for y in NAMES if leq(y, x)]
        # Pick the one with fewest components
        f[x] = min(below, key=lambda y: len(COMPS[y]))
    return f

simp = simplify_map()
print(f"\n  'Simplify' (map to simplest below):")
print(f"    {simp}")
is_mono_simp = all(leq(simp[a], simp[b]) for a in NAMES for b in NAMES if leq(a, b))
print(f"    Monotone: {is_mono_simp}")

# "Maximize" — map each to the most complex above it
def maximize_map():
    f = {}
    for x in NAMES:
        above = [y for y in NAMES if leq(x, y)]
        f[x] = max(above, key=lambda y: len(COMPS[y]))
    return f

maxi = maximize_map()
print(f"\n  'Maximize' (map to most complex above):")
print(f"    {maxi}")
is_mono_maxi = all(leq(maxi[a], maxi[b]) for a in NAMES for b in NAMES if leq(a, b))
print(f"    Monotone: {is_mono_maxi}")

# "Comparison collapse" — map Radix to nearest comparison sort
def comp_collapse():
    f = {x: x for x in NAMES}
    f['Radix'] = 'Bubble'  # minimal comparison sort that's also iterative
    return f

cc = comp_collapse()
print(f"\n  'Comparison collapse' (Radix → Bubble):")
print(f"    {cc}")
is_mono_cc = all(leq(cc[a], cc[b]) for a in NAMES for b in NAMES if leq(a, b))
print(f"    Monotone: {is_mono_cc}")

# "De-accelerate" — remove acceleration, keep rest
def deaccel():
    f = {x: x for x in NAMES}
    f['Heap'] = 'Selection'  # Heap without Accelerate → Selection
    f['Tim'] = 'Merge'  # Tim without Accelerate → closest is Merge (but loses Shift, Iterate)
    return f

da = deaccel()
print(f"\n  'De-accelerate' (Heap→Selection, Tim→Merge):")
print(f"    {da}")
is_mono_da = all(leq(da[a], da[b]) for a in NAMES for b in NAMES if leq(a, b))
print(f"    Monotone: {is_mono_da}")

# ============================================================
# 8. GREEN'S RELATIONS (J-classes, L-classes, R-classes)
# ============================================================
print("\n" + "="*60)
print("MONOID STRUCTURE — GREEN'S RELATIONS (sampled)")
print("="*60)

# For efficiency, work with a hash representation
def compose(f, g):
    return {x: f[g[x]] for x in NAMES}

def to_tuple(f):
    return tuple(f[x] for x in NAMES)

def from_tuple(t):
    return dict(zip(NAMES, t))

identity = {x: x for x in NAMES}

# Convert all endomorphisms to tuples for hashing
endo_tuples = set(to_tuple(f) for f in endomorphisms)

print(f"  Monoid size: {len(endo_tuples)}")

# Find the identity
id_t = to_tuple(identity)
assert id_t in endo_tuples
print(f"  Identity present: ✓")

# Sample: nilpotent elements (f^n = constant for some n)
nilpotent_count = 0
for f in endomorphisms[:2000]:  # sample
    current = f
    for _ in range(10):
        current = compose(current, f)
        if len(set(current.values())) == 1:
            nilpotent_count += 1
            break

print(f"  Nilpotent (in sample of 2000): {nilpotent_count}")

# Find order of each automorphism
print(f"\n  Automorphism group structure:")
for aut in automorphisms:
    current = aut
    order = 1
    while to_tuple(current) != id_t:
        current = compose(current, aut)
        order += 1
        if order > 20:
            break
    mapping = {k: v for k, v in aut.items() if k != v}
    print(f"    order {order}: {mapping}")

# ============================================================
# 9. MONAD STRUCTURE — which idempotents are monads?
# ============================================================
print("\n" + "="*60)
print("CLOSURE OPERATORS AS MONADS")
print("="*60)
print(f"  A closure operator c on P gives a monad on the poset category:")
print(f"  - unit: x → c(x) (extensive)")
print(f"  - multiplication: c(c(x)) = c(x) (idempotent)")
print(f"  - naturality: monotonicity")
print(f"\n  {len(closures)} closure operators = {len(closures)} monads on (P, ≤)")

for i, f in enumerate(closures):
    img = sorted(set(f.values()))
    # The image is the "Eilenberg-Moore category" — the fixed points
    print(f"\n  Monad M_{i}: image (algebra category) = {img}")
    mapping = {k:v for k,v in f.items() if k != v}
    if mapping:
        print(f"    unit maps: {mapping}")
    else:
        print(f"    = identity monad")
    # What does this monad do semantically?
    components_gained = {}
    for x in NAMES:
        if f[x] != x:
            gained = COMPS[f[x]] - COMPS[x]
            components_gained[x] = gained
    if components_gained:
        print(f"    Components added:")
        for x, gained in components_gained.items():
            print(f"      {x} gains {gained} (becomes {f[x]})")

# ============================================================
# 10. SUMMARY STATISTICS
# ============================================================
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

output = {
    "total_endomorphisms": len(endomorphisms),
    "automorphisms": len(automorphisms),
    "idempotents": len(idempotents),
    "closures": len(closures),
    "interiors": len(interiors),
    "constants": len(constants),
    "image_size_distribution": {str(k): v for k,v in sorted(image_sizes.items())},
    "fixed_point_distribution": {str(k): v for k,v in sorted(fixed_point_counts.items())},
    "preserves_comparison": preserves_comparison,
    "preserves_recursive_boundary": preserves_both,
    "retract_images": {str(sorted(img)): len(maps) for img, maps in sorted(idemp_by_image.items(), key=lambda x: len(x[0]))},
    "closure_operators": [
        {"image": sorted(set(f.values())), 
         "mapping": {k:v for k,v in f.items() if k != v},
         "components_added": {x: sorted(COMPS[f[x]] - COMPS[x]) for x in NAMES if f[x] != x}}
        for f in closures
    ],
    "interior_operators": [
        {"image": sorted(set(f.values())),
         "mapping": {k:v for k,v in f.items() if k != v}}
        for f in interiors
    ],
}

with open('/home/claude/endo_data.json', 'w') as fout:
    json.dump(output, fout, indent=2)

print(json.dumps({k:v for k,v in output.items() if k not in ('closure_operators','interior_operators','retract_images')}, indent=2))
print(f"\nRetract images: {len(idemp_by_image)} distinct sub-posets")
print(f"Closure operators: {len(closures)}")
print(f"Interior operators: {len(interiors)}")
