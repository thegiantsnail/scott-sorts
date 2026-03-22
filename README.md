# The Scott Topology of Sorting Algorithms

**A domain-theoretic analysis of the space of sorting algorithms, ordered by compositional structure.**

---

## Abstract

We construct a poset of sorting algorithms ordered by component-subset inclusion and study its Scott and Lawson topologies. The algorithms are decomposed into ur-components (Compare, Swap, Shift, Split, Merge, Select, Bucket, Iterate, Recurse, Accelerate), and the inclusion ordering on these component sets yields a partial order with genuine incomparabilities. The Scott topology on this 8-point poset has 56 open sets and coincides with the Alexandrov topology. The Lawson topology is discrete. We enumerate all 12,672 monotone endomorphisms (= Scott-continuous self-maps), identify 32 closure operators forming a Boolean lattice 2⁵, 8 interior operators, and a trivial automorphism group. We classify endomorphisms by efficiency, digraph symmetry, and semantic preservation, finding that only 128 of 12,672 maps (1%) respect the recursion boundary between iterative and recursive algorithms. We prove that de-optimization (removing acceleration structures) is not Scott-continuous, establishing a topological asymmetry between program improvement and degradation.

## Presentation Snapshot

- Distinct algorithms in the poset: 8
- Scott-open sets: 56
- Lawson-open sets: 256
- Monotone endomorphisms: 12,672
- Closure operators: 32
- Interior operators: 8
- Recursion-boundary-preserving maps: 128

Suggested data sources for demos and slides:

- [src/scott_data.json](src/scott_data.json) for the poset and topology tables.
- [src/endo_data.json](src/endo_data.json) for endomorphism counts and operator summaries.
- [src/benchmark_data.json](src/benchmark_data.json) and [src/test_results.json](src/test_results.json) for performance tables.
- [demo.html](demo.html) — interactive browser demo: animated sorting with Markov chain routing and live transition matrix.

## 1. Introduction: Sorting Algorithms as Points in a Space

Sorting algorithms are traditionally compared along a single axis — asymptotic time complexity — yielding a total preorder with many ties. Merge sort and heap sort both achieve O(n log n) worst case, yet they are fundamentally different computational objects: one builds new structures via divide-and-merge, the other mutates in place via an implicit tree.

We propose a richer view. Instead of ranking algorithms by performance, we decompose them into *compositional primitives* and order them by subset inclusion on these components. This yields a partial order where merge sort and heap sort are genuinely incomparable — neither contains the other's component set. The resulting poset is a concrete finite dcpo on which we can define and study the Scott topology.

This approach has three precedents, none of which take the topological step:

- **Darlington (1978)** synthesized six sorting algorithms from a common specification via program transformation, producing a family tree. But trees are not lattices, and Darlington put no topology on his tree.
- **Merritt (1985)** proposed an "inverted taxonomy" dividing all comparison sorts into hardsplit/easyjoin and easysplit/hardjoin families. This binary classification captures a real structural divide but has only two categories — no partial order, no topology, no continuous maps.
- **Lau & Prestwich (1988–1994)** extended Merritt's taxonomy using logic programming to derive both comparison and non-comparison sorts from specifications.

Our contribution is to treat sorting algorithms not as objects to be *derived* from a common specification, but as *points in a topological space* whose structure we can study with the tools of domain theory.

## 2. The Poset of Sorts

### 2.1 Ur-Components

We identify 10 primitive components from which all sorting algorithms in our study are composed:

| Component | Type | Description |
|-----------|------|-------------|
| Compare | Primitive | Binary comparison a < b |
| Swap | Primitive | Exchange two elements in place |
| Shift | Primitive | Slide elements to create a gap |
| Split | Combinator | Divide input into subproblems |
| Merge | Combinator | Combine sorted subsequences |
| Select | Combinator | Find extremal element |
| Bucket | Combinator | Distribute by key/digit (non-comparison) |
| Iterate | Control | Repeat over shrinking unsorted region |
| Recurse | Control | Self-similar subproblem decomposition |
| Accelerate | Meta | Replace linear scan with data structure |

### 2.2 Algorithm Decompositions

| Algorithm | Components | |C| |
|-----------|------------|-----|
| Bubble sort | {Compare, Swap, Iterate} | 3 |
| Insertion sort | {Compare, Shift, Iterate} | 3 |
| Selection sort | {Compare, Swap, Select, Iterate} | 4 |
| Quicksort | {Compare, Split, Recurse} | 3 |
| Merge sort | {Compare, Split, Merge, Recurse} | 4 |
| Heap sort | {Compare, Swap, Select, Iterate, Recurse, Accelerate} | 6 |
| Radix sort | {Bucket, Iterate} | 2 |
| Timsort | {Compare, Shift, Split, Merge, Iterate, Recurse, Accelerate} | 7 |

Shell sort has identical components to Insertion sort ({Compare, Shift, Iterate}) and is identified with it in the poset.

### 2.3 The Partial Order

We define **a ≤ b** iff components(a) ⊆ components(b). This yields a poset P on 8 distinct points with covering relations:

```
Bubble ≺ Selection   (adds Select)
Selection ≺ Heap     (adds Recurse, Accelerate)
Quick ≺ Merge        (adds Merge combinator)
Merge ≺ Tim          (adds Shift, Iterate, Accelerate)
Insertion ≺ Tim      (adds Split, Merge, Recurse, Accelerate)
```

Radix sort is isolated — comparable only to itself, since {Bucket, Iterate} shares no subset relation with any other algorithm's component set (Bucket appears nowhere else).

## 3. The Scott Topology

### 3.1 Scott = Alexandrov on Finite Posets

**Theorem.** On the finite poset P, the Scott topology coincides with the Alexandrov topology. A set U ⊆ P is Scott-open iff it is upward-closed.

*Proof.* Every directed set in a finite poset has a maximum element that belongs to the set. If U is upper-closed and ⊔D ∈ U, then max(D) ∈ U and max(D) ∈ D. The Scott inaccessibility condition is automatically satisfied. ∎

### 3.2 Enumeration

The Scott topology on P has exactly **56 open sets** out of 2⁸ = 256 possible subsets. These 56 are precisely the antichains of P under the Birkhoff representation.

**Basis.** The 8 principal filters ↑x = {y ∈ P : x ≤ y} form a basis:

| ↑x | Elements |
|----|----------|
| ↑Bubble | {Bubble, Selection, Heap} |
| ↑Insertion | {Insertion, Tim} |
| ↑Selection | {Selection, Heap} |
| ↑Quick | {Quick, Merge, Tim} |
| ↑Merge | {Merge, Tim} |
| ↑Heap | {Heap} |
| ↑Radix | {Radix} |
| ↑Tim | {Tim} |

Every Scott-open set is a union of principal filters.

### 3.3 Separation Properties

- **T₀ (Kolmogorov):** Yes. Every pair of distinct points is separated by some open set.
- **T₁:** No. The Scott topology on a non-discrete poset is never T₁.
- **Sober:** Yes. Finite T₀ spaces are sober.
- **Specialization order** = original partial order (verified computationally).

### 3.4 Way-Below and Algebraicity

In this finite dcpo, x ≪ y iff x ≤ y. Every element is compact. The dcpo is algebraic.

## 4. The Lawson Topology

### 4.1 Definition and Computation

The Lawson topology is the common refinement of the Scott topology and the lower topology (generated by complements of principal filters {X \ ↑x}).

**Theorem.** The Lawson topology on P is the discrete topology. All 256 subsets are Lawson-open.

*Proof.* For every x ∈ P, the singleton {x} = ↑x ∩ ⋂_{y>x} (X \\ ↑y) is Lawson-open (the first factor is Scott-open, the remaining factors are lower-open). For maximal elements (Heap, Tim, Radix) the index set {y : y > x} is empty; the empty intersection equals X by convention, so {x} = ↑x ∩ X = ↑x, which is a singleton since x is maximal. Since every singleton is open, the topology is discrete. ∎

### 4.2 Interpretation

The Scott topology observes only *presence* of components — "this algorithm uses Recurse" defines the Scott-open set {Quick, Merge, Heap, Tim}. But *absence* of a component is not Scott-observable. The Lawson topology adds this power: "this algorithm does NOT use Swap" is a lower-open observation. Together, presence and absence fully distinguish every algorithm, yielding the discrete topology.

The gap between Scott (56 opens) and Lawson (256 opens) is precisely the 200 sets that require observing absences.

## 5. The Frame of Scott-Opens

The 56 Scott-open sets form a frame Ω(P) — a complete distributive lattice (Heyting algebra) under intersection and union.

- **Join-irreducible elements:** 8 (the principal filters, generating all opens by union)
- **Meet-irreducible elements:** 8
- **Spatial:** Yes (every point is a completely prime filter)
- **Sobrification:** Identity (P is already sober)

By Birkhoff's representation theorem, Ω(P) is isomorphic to the lattice of antichains of P.

## 6. Monotone Endomorphisms

### 6.1 Enumeration

Since Scott-continuous = monotone on finite posets, we enumerate all order-preserving self-maps of P.

**Result: 12,672 monotone endomorphisms.**

### 6.2 The Automorphism Group

**Aut(P) = {id}.** The poset has no non-trivial symmetry — every algorithm occupies a structurally unique position. This maximal rigidity comes from the asymmetric branching of the Hasse diagram.

### 6.3 Idempotents and Retracts

- **1,498 idempotent endomorphisms** (f² = f)
- **207 distinct retract images** (sub-posets that P retracts onto)
- Most popular retracts: {Quick, Merge, Tim} (90 retractions — the divide-and-conquer suite), {Bubble, Selection, Heap} (75 — the swap-based iterative suite)

### 6.4 Closure Operators = Monads

**32 closure operators** (monotone, extensive, idempotent) form a Boolean lattice isomorphic to 2⁵. Each is a monad on the poset category.

The five independent binary "upgrade decisions":

1. Bubble → Selection or Heap (add Select)
2. Selection → Heap (add Recurse + Accelerate)
3. Quick → Merge (add Merge combinator)
4. Merge → Tim (add Shift + Iterate + Accelerate)
5. Insertion → Tim (add Split + Merge + Recurse + Accelerate)

The **maximum closure** sends everything to {Heap, Radix, Tim}: "use only the best version of each paradigm."

### 6.5 Interior Operators

**8 interior (kernel) operators** (monotone, contractive, idempotent). These strip components: Selection → Bubble (remove Select), Merge → Quick (remove Merge combinator), Heap → Selection (de-accelerate).

### 6.6 Semantic Preservation

Not all 12,672 maps are created equal. We classify by computational invariant preservation:

| Invariant | Maps Preserving | Fraction |
|-----------|-----------------|----------|
| Output is sorted | 12,672 | 100% (trivial) |
| Comparison-based preserved | 11,960 | 94.4% |
| Recursion boundary respected | 128 | 1.0% |
| Maximal elements preserved | 2,295 | 18.1% |

The **128 recursion-preserving maps** form the tightest meaningful submonoid — they map recursive algorithms to recursive ones and iterative to iterative, preserving the control flow paradigm.

## 7. Continuous Deformation Paths

### 7.1 Connected Families

Some algorithms are connected by continuous parameter paths:

- **Gap-parameterized insertion:** Shell sort with gap=[1] IS insertion sort. Continuous retraction.
- **Stride-parameterized bubble:** Comb sort with shrink=1.0 IS bubble sort.
- **Divide-and-merge interpolation:** Timsort interpolates between insertion sort (min_run=n) and merge sort (min_run=1).
- **Extract-min acceleration:** Selection sort → Heap sort by replacing linear scan with a heap. Data structure refinement.

### 7.2 Disconnected Components

Radix sort is order-theoretically isolated — comparable only to itself in the poset. Quicksort, while connected upward to Merge and Tim, is topologically separated from the swap-based and shift-based families: no continuous deformation path connects it to Bubble, Insertion, or Selection. The CFG skeletons are fundamentally different: Quicksort's divide-by-pivot structure shares no component-subset relation with iterative linear scans.

### 7.3 De-Optimization is Not Scott-Continuous

**Theorem.** The map f: Heap → Selection, Tim → Merge (remove Accelerate) is not monotone.

*Proof.* Tim ≥ Insertion in P (components(Insertion) ⊆ components(Tim)), but f(Tim) = Merge and Merge ≱ Insertion (components(Insertion) ⊄ components(Merge)). Monotonicity fails. ∎

This establishes a **topological asymmetry**: optimization (adding acceleration) is a closure operator (continuous), but de-optimization is not its inverse — it tears the partial order. You cannot continuously degrade algorithms in this space.

## 8. Efficiency and Symmetry of Endomorphisms

### 8.1 Efficiency Ranking

Scoring each algorithm by practical runtime quality (Tim=1.0 best, Bubble=5.0 worst), the most efficient endomorphism is const(Tim) (average 1.0, all information destroyed). The identity has average 2.88 with perfect information preservation.

**Pareto front** (21 maps): efficiency vs. information preservation traces a steep convex frontier — information is lost quickly as you push toward efficiency.

### 8.2 Symmetry Classes

Since Aut(P) is trivial, conjugacy gives only singletons. We use three weaker equivalences:

- **Effect profile** (78 classes): classify each point's movement as fixed/up/down/cross.
- **Functional digraph isomorphism** (236 classes): the shape of x ↦ f(x) — fixed points, tails, cycles.
- **Efficiency signature** (12,240 classes): nearly unique — the monoid has minimal redundancy at fine resolution.

The largest class (2,548 maps, 20%) sends every algorithm to an incomparable one — maximum disruption while remaining monotone.

## 9. Connection to Prior Work

| Approach | What It Does | What's Missing |
|----------|-------------|----------------|
| Darlington (1978) | Family tree via program transformation | Not a lattice, no topology |
| Merritt (1985) | Binary taxonomy: hardsplit/easyjoin vs easysplit/hardjoin | Only two categories, no partial order |
| Lau (1988–1994) | Logic-based synthesis from specifications | Classification, not topology |
| Knuth (1973) | Bottom-up operational classification | No compositional structure |
| **This work** | **Poset with Scott/Lawson topology, endomorphism monoid** | — |

The key novelty is treating algorithms as *points in a topological space* rather than objects to be derived from specifications or classified by operational features.

## 10. Sort Compiler: Program Synthesis via Continuous Maps

The endomorphisms of P are not merely combinatorial curiosities — each one specifies a *source-to-source rewrite rule* that maps any sorting algorithm to another point in the poset. `src/sort_compiler.py` implements this compiler.

### 10.1 Operator Taxonomy

| Class | Count | Properties | Semantic role |
|-------|-------|------------|---------------|
| Interior operators | 8 | contractive + idempotent + monotone | de-optimization: strip components |
| Closure operators | 32 | extensive + idempotent + monotone | optimization: add components |
| `de_accelerate` | — | **not** monotone | topological counter-example (§7.3) |

### 10.2 Interior (De-optimization) Paths

Every interior operator strips ur-components while remaining Scott-continuous. Two semantically meaningful ones:

**`degrade_heap`:** Heap → Selection (strip `{Accelerate, Recurse}`).
The `_heapify` helper is removed, recursive calls drop from 3 to 0, and the implicit binary tree is replaced by a nested linear scan. The compiled output is canonical `selection_sort`.

**`strip_merge_only`:** Merge → Quick (strip `{Merge}`).
The `_merge` helper and its while-loop are removed; the combining step becomes list-comprehension partitioning and concatenation. The compiled output is `quicksort`.

Both transforms are **Scott-continuous** because they move downward in the poset.

### 10.3 Closure (Optimization) Paths

**`add_merge`:** Quick → Merge (add `{Merge}`).
Inserts the `_merge` combinator: list comprehensions → slices + while-loop merge. AST delta: +1 function definition, +4 slices, −3 list comprehensions, +1 loop.

**`recursify_insertion`:** Insertion → Tim (add `{Accelerate, Merge, Recurse, Split}`).
The most dramatic transform: a simple 2-loop insertion sort gains +2 helper functions, +6 loops, and +2 recursive call sites — yielding Timsort's divide-and-conquer scaffold with adaptive run detection.

**`maximize`:** maps every algorithm to the most complex point above it in the poset (Bubble/Selection → Heap; Quick/Merge/Insertion → Tim; Radix stays).

### 10.4 The Discontinuous Counter-Example (Verified Computationally)

The `de_accelerate` map (Heap → Selection, Tim → Merge) is **not** Scott-continuous. The compiler verifies this mechanically:

```
Witness: Insertion ≤ Tim  but  f(Insertion) = Insertion ⊄ Merge = f(Tim)
Missing components: ['Iterate', 'Shift']
```

`Shift` and `Iterate` are present in `f(Insertion) = Insertion` but absent from `f(Tim) = Merge`. Monotonicity is violated. You can strip acceleration from a single algorithm, but you cannot do so *continuously* across the whole poset.

### 10.5 Full Compilation Table

Running `python src/sort_compiler.py` prints a full `operator × algorithm → target` matrix and the AST structural diff for each non-trivial transform. Every named operator is verified against the three axioms (monotone + contractive/extensive + idempotent) before the demo runs.

## 11. Triplet Hybrid Experiments

The pairwise hybrid results (Section 8) showed that combining disjoint ur-component sets beats any single-paradigm algorithm. Section 11 pushes this further: **three-tier dispatch** `Outer → Mid → Inner`, where the outer layer handles large sub-arrays (`n > 128`), the mid layer handles medium sub-arrays (`16 < n ≤ 128`), and the inner layer handles the base case (`n ≤ 16`). `src/triplet_test.py` exhausts the combination space: Outer ∈ {Quick, Merge} × Mid ∈ {Quick, Merge, Heap, Insertion, Selection, Radix} × Inner ∈ {Insertion, Selection, Bubble} = **36 triplets**, tested across 13 input classes × 3 sizes × 8 seeds = **11,232 trials**, all correct.

### 11.1 Correctness and Stability

Composition boundaries at `n=128` and `n=16` are perfectly stable across all 36 combinations and all 13 input classes. Every recursive mid algorithm (Quick, Merge) correctly falls back to the inner algorithm at the base case; every non-recursive mid algorithm (Heap, Insertion, Selection, Radix) is applied directly on its slice.

### 11.2 The Radix Mid-Layer Dominance

The most striking empirical finding is that interposing Radix as the mid-layer produces the fastest wall times at `n=1024` regardless of which outer or inner algorithm surrounds it:

| Triplet | Mean wall time (ms, n=1024) | Mean comparisons |
|---------|----------------------------|-----------------|
| T_QRB (Quick/Radix/Bubble) | **0.773** | 4,716 |
| T_QRI (Quick/Radix/Insertion) | 0.776 | 4,703 |
| T_QRS (Quick/Radix/Selection) | 0.780 | 4,535 |
| T_MRI (Merge/Radix/Insertion) | 0.787 | 2,233 |
| T_MRB (Merge/Radix/Bubble) | 0.787 | 2,233 |
| T_MQI (Merge/Quick/Insertion) | 0.865 | 7,565 |

The Radix mid-layer achieves this because it operates in zero comparisons on the medium sub-arrays (its counting-based dispatch never touches `<`), leaving only the outer divide-and-conquer overhead and the insertion/selection base case. This is a direct empirical manifestation of the ur-component independence theorem: `{Bucket}` (Radix) and `{Split}` (Quick) or `{Merge}` (Merge) occupy disjoint parts of the component lattice, so combining them produces a strictly richer algorithm than either alone.

### 11.3 O(n²) Mid-Layers Are Catastrophic

Placing Selection as the mid-layer eliminates all performance gains from the outer divide-and-conquer:

| Triplet | Mean wall time (ms, n=1024) | Mean comparisons |
|---------|----------------------------|-----------------|
| T_MSI (Merge/Selection/Insertion) | 4.150 | 67,257 |
| T_QSI (Quick/Selection/Insertion) | 3.559 | 58,336 |

The O(n²) growth of Selection on sub-arrays in the range `(16, 128]` dominates entirely. For comparison, T_MRI runs in 0.787ms (5.3× faster) with 2,233 comparisons vs. 67,257 (30× fewer). This confirms the topological picture: Selection and Radix are in the same connected component of the poset as Bubble, and routing medium sub-arrays through them defeats the purpose of the outer O(n log n) structure.

### 11.4 The T_QMI / T_MQI Symmetry

The two configurations that cross-nest Quick and Merge perform nearly identically at `n=1024`:

| Triplet | Mean wall time (ms) | Mean comparisons |
|---------|---------------------|-----------------|
| T_MQI (Merge outer / Quick mid / Insertion inner) | 0.865 | 7,565 |
| T_QMI (Quick outer / Merge mid / Insertion inner) | 1.019 | 8,638 |

`T_MQI` edges out `T_QMI` by ~15% in wall time. Merge's guaranteed O(n log n) split is a marginally more uniform router at the top level before Quick handles the intermediate tier, consistent with Merge's lower variance across input classes (Merge lacks Quick's adversarial `killer_quick` case). Both are competitive with Tim's 8,595 mean comparisons.

### 11.5 Topological Interpretation

The triplet results confirm that the ur-component structure of the poset predicts hybrid performance:

- **Radix mid dominates** because `{Bucket}` is disjoint from every component used by Quick/Merge (Split, Merge, Recurse); their union is maximally rich.
- **Selection mid collapses** because `{Compare, Swap, Select}` is a subset of components already exercised by Quick; the hybrid adds no new capability while extending O(n²) behavior to the mid range.
- **Insertion inner universally wins** over Selection and Bubble inner because `{Shift, Iterate}` is strictly more efficient than `{Swap, Iterate}` or `{Compare, Swap}` on small arrays with nearly-sorted structure at the leaves.

These patterns are not coincidental — they are consequences of the poset's topology. Algorithms high in the ordering (Tim, Radix) dominate as mid-layers because their ur-component sets are larger; algorithms low in the ordering (Bubble, Selection) are best confined to the inner base case or excluded entirely.

## 12. Future Directions

- **Infinite enrichment.** Extend the poset to include all sorting algorithms (counting sort, bucket sort, library sort, smoothsort, etc.) and study the Scott topology on the resulting infinite dcpo, where the inaccessibility condition becomes non-trivial.
- **Crown topology connection.** The Lawson topology's "observe absence" power mirrors the Independent Veto topology (K* = max) in Open Crown Type Theory, where the gap between Scott and Lawson corresponds to the gap between Series and Veto evaluation.
- **Program transformation as continuous maps.** The interior and closure operators are now implemented as a source-to-source compiler in `src/sort_compiler.py` (Section 10). Extending to finer-grained transforms (loop unrolling, memoization, arbitrary data-structure replacement) remains open.
- **Triplet and beyond.** Section 11 establishes that three-tier dispatch with a Radix mid-layer achieves sub-millisecond sorting at n=1024. Extending to four tiers (Radix outer → Merge mid → Quick mid-inner → Insertion inner) and studying the convergence of hybrid performance to theoretical lower bounds is an open direction.
- **Galois connection.** The closure/interior operator pairing suggests a Galois connection between "upgrade" and "simplify" that could be formalized.
- **Extended poset P\*.** `src/topology_navigator.py` identifies two new poset points, Net_QR = join(Quick, Radix) and Net_TR = join(Tim, Radix), expanding the Scott-open set count from 56 to 72. Characterising the full family of join-constructible algorithms and their continuous maps is an open direction.
- **Adaptive topology navigation.** The Markov chain in `src/network_sort.py` empirically discovers phase boundaries without knowledge of P\*. Combining a topological prior (ur-component advantage weights per input feature) with the empirical transition matrix would give a fully principled Bayesian navigator.

---

## Appendix A: Empirical Data Tables

Data from `src/test_results.json` (3,536 trials) and `src/triplet_results.json` (11,232 trials).
All results are means over 8 deterministic seeds × 13 input classes unless noted.

### A.1 Algorithm Performance at n = 1024

| Algorithm | Mean comparisons | Mean wall time (ms) | vs. Tim |
|-----------|----------------:|--------------------:|:-------:|
| Radix | 0 | 0.463 | 2.5× faster |
| Hybrid_QI | 10,025 | 0.840 | 1.4× faster |
| Hybrid_RI | 0 | 1.006 | 1.1× faster |
| Quick | 10,906 | 1.046 | 1.1× faster |
| **Tim** | **8,595** | **1.144** | **—** |
| Hybrid_MI | 7,013 | 1.230 | 1.1× slower |
| Heap | 15,523 | 1.361 | 1.2× slower |
| Merge | 6,547 | 1.573 | 1.4× slower |
| Hybrid_Intro | 10,119 | 1.877 | 1.6× slower |
| Insertion | 183,201 | 14.256 | 12.5× slower |

*Bubble and Selection excluded at n=1024 (O(n²) timing budget exceeded).*

### A.2 Input-Class Upsets (n = 1024)

#### Radix vs. Tim — wall time ratio Tim÷Radix (Radix wins all 13 classes)

| Input class | Tim÷Radix |
|-------------|----------:|
| few_unique | 9.9× |
| two_values | 7.1× |
| reverse | 4.3× |
| pipe_organ | 3.5× |
| killer_quick | 2.9× |
| sawtooth | 2.4× |
| random | 2.3× |
| all_same | 2.2× |
| nearly_sorted | 1.6× |
| interleaved | 1.3× |
| rotated | 1.2× |
| random_blocks | 1.5× |
| sorted | 1.1× |

#### Insertion vs. Tim — wall time ratio Tim÷Insertion (Insertion wins 3 of 13)

| Input class | Tim÷Insertion | Winner |
|-------------|-------------:|:------:|
| interleaved | 6.8× | Insertion |
| all_same | 6.1× | Insertion |
| sorted | 5.7× | Insertion |
| nearly_sorted | 0.33× | Tim |
| all others | < 0.15× | Tim |

### A.3 Triplet Hybrid Rankings at n = 1024

`T_XYZ` = outer X / mid Y / inner Z. HIGH_CUT = 128, LOW_CUT = 16.
Tim baseline: 1.144 ms / 8,595 mean comparisons. **14 of 36 triplets beat Tim.**

| Triplet | Mean ms | Mean comps | vs. Tim |
|---------|--------:|-----------:|:-------:|
| T_QRB (Quick/Radix/Bubble) | 0.773 | 4,712 | **1.48×** |
| T_QRI (Quick/Radix/Insertion) | 0.776 | 4,703 | **1.47×** |
| T_QRS (Quick/Radix/Selection) | 0.780 | 4,716 | **1.47×** |
| T_MRS (Merge/Radix/Selection) | 0.784 | 2,233 | **1.46×** |
| T_MRB (Merge/Radix/Bubble) | 0.787 | 2,233 | **1.45×** |
| T_MRI (Merge/Radix/Insertion) | 0.787 | 2,233 | **1.45×** |
| T_MQI (Merge/Quick/Insertion) | 0.865 | 7,565 | **1.32×** |
| T_QQI (Quick/Quick/Insertion) | 0.905 | 10,025 | **1.26×** |
| T_MQB (Merge/Quick/Bubble) | 0.979 | 8,721 | **1.17×** |
| T_QQB (Quick/Quick/Bubble) | 0.987 | 11,060 | **1.16×** |
| T_QMI (Quick/Merge/Insertion) | 1.019 | 8,638 | **1.12×** |
| T_MMI (Merge/Merge/Insertion) | 1.020 | 7,013 | **1.12×** |
| T_QMB (Quick/Merge/Bubble) | 1.089 | 9,393 | **1.05×** |
| T_MQS (Merge/Quick/Selection) | 1.123 | 11,686 | **1.02×** |
| *Tim baseline* | *1.144* | *8,595* | — |
| T_MMB | 1.186 | 7,962 | 1.04× slower |
| *(22 more, all ≥ 1.1× slower)* | … | … | |
| T_MSI (Merge/Selection/Insertion) | 4.150 | 67,257 | 3.6× slower |

All Selection-mid triplets finish below Tim; all Radix-mid triplets finish above it.

### A.4 Extended Poset P* — Component Sets and Scott-Open Set Count

| Poset | Points | Scott-open sets |
|-------|-------:|----------------:|
| P (base, 8 algorithms) | 8 | 56 |
| P* (+ Net_QR + Net_TR) | 10 | **72** |

| New point | ur-components | Position in P* |
|-----------|---------------|----------------|
| Net_QR = join(Quick, Radix) | Compare, Split, Recurse, Merge, Bucket, Iterate | Above Quick, Merge, Radix; incomparable to Tim and Heap |
| Net_TR = join(Tim, Radix) | Compare, Shift, Split, Merge, Iterate, Recurse, Accelerate, Bucket | Above Tim, Net_QR, Radix; one of two maximal elements |

The covering relation Radix → Net_QR adds one component ({Bucket} joins the comparison family). The covering relation Tim → Net_TR adds exactly one component ({Bucket}) to Tim's full set. Heap remains incomparable to both Net_QR and Net_TR.

The 16 new Scott-open sets are all upward-closed subsets that require passing through Net_QR or Net_TR: {Net_QR}, {Net_TR}, {Net_QR, Net_TR}, {Radix, Net_QR, Net_TR}, {Merge, Net_QR, Net_TR}, {Quick, Merge, Net_QR, Net_TR}, {Tim, Net_QR, Net_TR}, and their unions with other upward-closed sets from P.

### A.5 Pull Network Performance vs. Baselines (n = 1024, mean over 13 types × 8 seeds)

| Configuration | Mean comps | Mean ms | vs. Tim |
|---------------|----------:|--------:|:-------:|
| Pull(Quick+Radix) | 5,592 | 1.447 | **1.6× faster** |
| Quick (standalone) | 10,906 | 2.064 | **1.1× faster** |
| Pull(Merge+Radix) | 4,203 | 2.049 | **1.1× faster** |
| **Tim (standalone)** | **8,595** | **2.346** | — |
| Pull(Merge+Quick) | 8,735 | 2.612 | 1.1× slower |
| Pull(Quick+Merge) | 8,458 | 2.684 | 1.1× slower |
| Merge (standalone) | 6,547 | 2.911 | 1.2× slower |

Pull network timings use `src/benchmark_deep.py` instrumented sorts; standalone timings from `src/sort_test.py` use slightly different instrumentation, accounting for the apparent Tim discrepancy across tables.

---

## References

1. Darlington, J. "A synthesis of several sorting algorithms." *Acta Informatica* 11, 1–30 (1978).
2. Merritt, S.M. "An inverted taxonomy of sorting algorithms." *Communications of the ACM* 28(1): 96–99 (1985).
3. Lau, K.K. "A note on synthesis and classification of sorting algorithms." *Acta Informatica* (1994).
4. Knuth, D.E. *The Art of Computer Programming, Vol. 3: Sorting and Searching.* Addison-Wesley (1973).
5. Gierz, G., Hofmann, K.H., Keimel, K., Lawson, J.D., Mislove, M., Scott, D.S. *Continuous Lattices and Domains.* Cambridge University Press (2003).
6. Abramsky, S., Jung, A. "Domain Theory." *Handbook of Logic in Computer Science* Vol. 3 (1994).
7. Scott, D.S. "Continuous lattices." *Toposes, Algebraic Geometry and Logic.* Lecture Notes in Mathematics 274 (1972).

---

## License

MIT
