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

# Runtime efficiency scores (lower = better, based on worst-case + practical considerations)
# Scale: 1=excellent, 5=poor
EFFICIENCY = {
    'Bubble': 5.0,      # O(n²), terrible
    'Insertion': 4.0,    # O(n²) worst but good on small/nearly-sorted
    'Selection': 4.5,    # O(n²), no adaptivity
    'Quick': 2.5,        # O(n²) worst but O(n log n) avg, excellent cache
    'Merge': 2.0,        # O(n log n) guaranteed, stable
    'Heap': 2.5,         # O(n log n) guaranteed, in-place but poor cache
    'Radix': 1.5,        # O(nk) linear for fixed-width, but limited applicability
    'Tim': 1.0,          # O(n log n) worst, O(n) best, stable, adaptive, practical champion
}

# Component count (structural complexity)
COMPLEXITY = {nm: len(COMPS[nm]) for nm in NAMES}

def leq(a, b):
    return COMPS[a].issubset(COMPS[b])

# Enumerate all monotone endomorphisms
print("Enumerating monotone endomorphisms...")
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

print(f"Total: {len(endomorphisms)}")

# ============================================================
# EFFICIENCY METRICS FOR EACH ENDOMORPHISM
# ============================================================

def compute_metrics(f):
    """Compute multiple efficiency/quality metrics for an endomorphism."""
    
    # 1. Average runtime efficiency of image
    # If you APPLIED this endomorphism as "algorithm selection advice",
    # how fast would the resulting algorithms be?
    avg_eff = sum(EFFICIENCY[f[x]] for x in NAMES) / len(NAMES)
    
    # 2. Worst efficiency in image (max = worst)
    worst_eff = max(EFFICIENCY[f[x]] for x in NAMES)
    
    # 3. Best efficiency in image (min = best)
    best_eff = min(EFFICIENCY[f[x]] for x in NAMES)
    
    # 4. Information preservation = |image| / |domain|
    img_size = len(set(f.values()))
    info_preserve = img_size / len(NAMES)
    
    # 5. Component displacement: how much does f move things?
    # Sum of |components(f(x)) △ components(x)| (symmetric difference)
    displacement = sum(len(COMPS[f[x]].symmetric_difference(COMPS[x])) for x in NAMES)
    
    # 6. Upgrade score: net components gained (positive = upgrading)
    upgrade = sum(len(COMPS[f[x]]) - len(COMPS[x]) for x in NAMES)
    
    # 7. Fixed points
    fixed = sum(1 for x in NAMES if f[x] == x)
    
    # 8. Is idempotent?
    is_idemp = all(f[f[x]] == f[x] for x in NAMES)
    
    # 9. Efficiency improvement: negative means f makes things faster
    eff_delta = sum(EFFICIENCY[f[x]] - EFFICIENCY[x] for x in NAMES)
    
    # 10. Preserves comparison-based?
    preserves_comp = all(f[x] != 'Radix' for x in NAMES if 'Compare' in COMPS[x])
    
    return {
        'avg_efficiency': round(avg_eff, 3),
        'worst_efficiency': worst_eff,
        'best_efficiency': best_eff,
        'image_size': img_size,
        'info_preservation': round(info_preserve, 3),
        'displacement': displacement,
        'upgrade_score': upgrade,
        'fixed_points': fixed,
        'is_idempotent': is_idemp,
        'efficiency_delta': round(eff_delta, 2),
        'preserves_comparison': preserves_comp,
    }

print("\nComputing metrics for all endomorphisms...")
all_metrics = []
for i, f in enumerate(endomorphisms):
    m = compute_metrics(f)
    m['index'] = i
    m['mapping'] = dict(f)
    all_metrics.append(m)

# ============================================================
# RANK BY MULTIPLE CRITERIA
# ============================================================

# MOST EFFICIENT: lowest avg_efficiency (maps everything to fast sorts)
by_avg_eff = sorted(all_metrics, key=lambda m: m['avg_efficiency'])

print("\n" + "="*60)
print("TOP 20 MOST EFFICIENT ENDOMORPHISMS")
print("(lowest average runtime cost of image)")
print("="*60)
for m in by_avg_eff[:20]:
    f = m['mapping']
    moves = {k:v for k,v in f.items() if k!=v}
    print(f"  avg={m['avg_efficiency']:.2f} worst={m['worst_efficiency']:.1f} "
          f"|im|={m['image_size']} fixed={m['fixed_points']} "
          f"Δeff={m['efficiency_delta']:+.1f} moves={moves}")

# LEAST EFFICIENT
print("\n" + "="*60)
print("TOP 20 LEAST EFFICIENT ENDOMORPHISMS")
print("="*60)
by_avg_eff_rev = sorted(all_metrics, key=lambda m: -m['avg_efficiency'])
for m in by_avg_eff_rev[:20]:
    f = m['mapping']
    moves = {k:v for k,v in f.items() if k!=v}
    print(f"  avg={m['avg_efficiency']:.2f} worst={m['worst_efficiency']:.1f} "
          f"|im|={m['image_size']} fixed={m['fixed_points']} "
          f"Δeff={m['efficiency_delta']:+.1f} moves={moves}")

# MOST INFORMATION PRESERVING (largest image that also improves efficiency)
print("\n" + "="*60)
print("PARETO FRONT: max info preservation + min avg efficiency")
print("="*60)
# Pareto: no other map has BOTH better efficiency AND larger image
pareto = []
for m in all_metrics:
    dominated = False
    for other in all_metrics:
        if (other['avg_efficiency'] <= m['avg_efficiency'] and 
            other['image_size'] >= m['image_size'] and
            (other['avg_efficiency'] < m['avg_efficiency'] or other['image_size'] > m['image_size'])):
            dominated = True
            break
    if not dominated:
        pareto.append(m)

pareto.sort(key=lambda m: m['image_size'])
print(f"  Pareto front size: {len(pareto)}")
for m in pareto:
    f = m['mapping']
    moves = {k:v for k,v in f.items() if k!=v}
    print(f"  avg={m['avg_efficiency']:.2f} |im|={m['image_size']} "
          f"fixed={m['fixed_points']} idemp={m['is_idempotent']} "
          f"moves={moves}")

# ============================================================
# SYMMETRY ANALYSIS
# ============================================================
print("\n" + "="*60)
print("SYMMETRY CLASSES")
print("="*60)

# Two endomorphisms are "symmetric" if they have the same structural profile:
# same image size, same displacement, same efficiency profile up to permutation
# More precisely: f ~ g iff there exists an automorphism σ such that g = σ∘f∘σ⁻¹
# Since Aut(P) = {id}, conjugacy classes are singletons!
# 
# So we need a WEAKER notion of symmetry.
# Use: same "effect profile" — same multiset of {stays, goes up, goes down, crosses chain}

def effect_profile(f):
    """Classify each mapping as stay/up/down/cross and compute profile."""
    effects = []
    for x in NAMES:
        y = f[x]
        if x == y:
            effects.append('fixed')
        elif leq(x, y):
            effects.append('up')  # upgraded
        elif leq(y, x):
            effects.append('down')  # downgraded  
        else:
            effects.append('cross')  # incomparable — crossed chains
    return tuple(sorted(effects))

def efficiency_signature(f):
    """Multiset of (efficiency_change, component_change) pairs."""
    sig = []
    for x in NAMES:
        y = f[x]
        eff_change = round(EFFICIENCY[y] - EFFICIENCY[x], 1)
        comp_change = len(COMPS[y]) - len(COMPS[x])
        sig.append((eff_change, comp_change))
    return tuple(sorted(sig))

# Group by effect profile
profile_groups = defaultdict(list)
for i, f in enumerate(endomorphisms):
    prof = effect_profile(f)
    profile_groups[prof].append(i)

print(f"\nEffect profile classes: {len(profile_groups)}")
print("\nLargest profile classes:")
sorted_profiles = sorted(profile_groups.items(), key=lambda x: -len(x[1]))
for prof, indices in sorted_profiles[:25]:
    counts = Counter(prof)
    desc = ', '.join(f"{v}×{k}" for k,v in sorted(counts.items()))
    # Show one representative
    rep = endomorphisms[indices[0]]
    moves = {k:v for k,v in rep.items() if k!=v}
    print(f"  [{desc}]: {len(indices)} maps. e.g. {moves}")

# Group by efficiency signature (finer)
effsig_groups = defaultdict(list)
for i, f in enumerate(endomorphisms):
    sig = efficiency_signature(f)
    effsig_groups[sig].append(i)

print(f"\nEfficiency signature classes: {len(effsig_groups)}")

# ============================================================
# STRUCTURAL SYMMETRY: conjugacy by graph automorphisms
# ============================================================
# Since Aut(P) is trivial, let's look for a weaker structural
# symmetry: maps that have isomorphic "action diagrams"
# (the directed graph x → f(x))

def action_graph_type(f):
    """Classify the action graph (functional digraph) up to isomorphism."""
    # Find cycles and tails
    visited = set()
    cycles = []
    tails = []
    
    for start in NAMES:
        if start in visited:
            continue
        path = []
        x = start
        while x not in visited and x not in path:
            path.append(x)
            x = f[x]
        
        if x in path:
            # Found a cycle
            cycle_start = path.index(x)
            cycle = path[cycle_start:]
            tail = path[:cycle_start]
            cycles.append(len(cycle))
            if tail:
                tails.append(len(tail))
            for node in path:
                visited.add(node)
        else:
            # x was already visited (connects to existing component)
            for node in path:
                visited.add(node)
                tails.append(1)  # approximate
    
    return (tuple(sorted(cycles)), tuple(sorted(tails)))

def functional_digraph_iso_class(f):
    """More precise: encode the tree structure of the functional digraph."""
    # For each node, trace its eventual cycle and depth to cycle
    def trace(x, f):
        seen = {}
        step = 0
        while x not in seen:
            seen[x] = step
            x = f[x]
            step += 1
        cycle_len = step - seen[x]
        rho = seen[x]  # tail length
        return (rho, cycle_len)
    
    profile = tuple(sorted(trace(x, f) for x in NAMES))
    return profile

digraph_groups = defaultdict(list)
for i, f in enumerate(endomorphisms):
    iso = functional_digraph_iso_class(f)
    digraph_groups[iso].append(i)

print(f"\nFunctional digraph isomorphism classes: {len(digraph_groups)}")
print("\nLargest digraph iso classes:")
sorted_dg = sorted(digraph_groups.items(), key=lambda x: -len(x[1]))
for iso, indices in sorted_dg[:20]:
    rep = endomorphisms[indices[0]]
    moves = {k:v for k,v in rep.items() if k!=v}
    # Decode the iso class
    desc_parts = []
    for rho, cyc in iso:
        if rho == 0 and cyc == 1:
            desc_parts.append("fix")
        elif rho > 0 and cyc == 1:
            desc_parts.append(f"tail{rho}→fix")
        elif rho == 0 and cyc > 1:
            desc_parts.append(f"cyc{cyc}")
        else:
            desc_parts.append(f"tail{rho}→cyc{cyc}")
    desc = ', '.join(sorted(desc_parts))
    print(f"  [{desc}]: {len(indices)} maps")

# ============================================================
# COMBINED: efficiency × symmetry
# ============================================================
print("\n" + "="*60)
print("EFFICIENCY × DIGRAPH SYMMETRY CROSS-TABULATION")
print("="*60)

# Bin efficiency into categories
def eff_bin(m):
    avg = m['avg_efficiency']
    if avg <= 1.5: return 'excellent'
    if avg <= 2.0: return 'good'
    if avg <= 3.0: return 'moderate'
    if avg <= 4.0: return 'poor'
    return 'terrible'

cross = defaultdict(lambda: defaultdict(int))
for i, f in enumerate(endomorphisms):
    m = all_metrics[i]
    eb = eff_bin(m)
    iso = functional_digraph_iso_class(f)
    # Simplify iso to just count of fixed vs non-fixed
    n_fixed = sum(1 for rho, cyc in iso if rho == 0 and cyc == 1)
    cross[eb][n_fixed] += 1

print(f"\n  {'Category':<12} " + " ".join(f"{i}fix" for i in range(9)))
for cat in ['excellent','good','moderate','poor','terrible']:
    row = cross[cat]
    vals = " ".join(f"{row.get(i,0):>4}" for i in range(9))
    total = sum(row.values())
    print(f"  {cat:<12} {vals}  = {total}")

# ============================================================
# OUTPUT for visualization
# ============================================================
output = {
    'pareto_front': [{
        'avg_efficiency': m['avg_efficiency'],
        'image_size': m['image_size'],
        'fixed_points': m['fixed_points'],
        'is_idempotent': m['is_idempotent'],
        'displacement': m['displacement'],
        'efficiency_delta': m['efficiency_delta'],
        'mapping': m['mapping'],
    } for m in pareto],
    'top_efficient': [{
        'avg_efficiency': m['avg_efficiency'],
        'image_size': m['image_size'],
        'mapping': m['mapping'],
    } for m in by_avg_eff[:30]],
    'top_inefficient': [{
        'avg_efficiency': m['avg_efficiency'],
        'image_size': m['image_size'],
        'mapping': m['mapping'],
    } for m in by_avg_eff_rev[:30]],
    'profile_class_sizes': [(dict(Counter(prof)), len(indices)) 
                            for prof, indices in sorted_profiles[:30]],
    'digraph_class_sizes': [(list(iso), len(indices)) 
                            for iso, indices in sorted_dg[:30]],
    'efficiency_distribution': {
        'excellent': sum(1 for m in all_metrics if m['avg_efficiency'] <= 1.5),
        'good': sum(1 for m in all_metrics if 1.5 < m['avg_efficiency'] <= 2.0),
        'moderate': sum(1 for m in all_metrics if 2.0 < m['avg_efficiency'] <= 3.0),
        'poor': sum(1 for m in all_metrics if 3.0 < m['avg_efficiency'] <= 4.0),
        'terrible': sum(1 for m in all_metrics if m['avg_efficiency'] > 4.0),
    },
}

with open('/home/claude/eff_sym_data.json', 'w') as fout:
    json.dump(output, fout, indent=2)

print("\n" + json.dumps(output['efficiency_distribution']))
print(f"\nProfile classes: {len(profile_groups)}")
print(f"Digraph iso classes: {len(digraph_groups)}")
print(f"Efficiency sig classes: {len(effsig_groups)}")
print(f"Pareto front: {len(pareto)}")
