import ast
import json
import sys

# Sorting algorithm implementations
ALGORITHMS = {
"bubble_sort": '''
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
    return arr
''',

"insertion_sort": '''
def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr
''',

"selection_sort": '''
def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr
''',

"merge_sort": '''
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
''',

"quicksort": '''
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
''',

"heap_sort": '''
def heap_sort(arr):
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)
    return arr

def heapify(arr, n, i):
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2
    if left < n and arr[left] > arr[largest]:
        largest = left
    if right < n and arr[right] > arr[largest]:
        largest = right
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)
''',

"shell_sort": '''
def shell_sort(arr):
    n = len(arr)
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            temp = arr[i]
            j = i
            while j >= gap and arr[j - gap] > temp:
                arr[j] = arr[j - gap]
                j -= gap
            arr[j] = temp
        gap //= 2
    return arr
''',

"radix_sort": '''
def radix_sort(arr):
    if not arr:
        return arr
    max_val = max(arr)
    exp = 1
    while max_val // exp > 0:
        counting_sort_by_digit(arr, exp)
        exp *= 10
    return arr

def counting_sort_by_digit(arr, exp):
    n = len(arr)
    output = [0] * n
    count = [0] * 10
    for i in range(n):
        index = arr[i] // exp % 10
        count[index] += 1
    for i in range(1, 10):
        count[i] += count[i - 1]
    for i in range(n - 1, -1, -1):
        index = arr[i] // exp % 10
        output[count[index] - 1] = arr[i]
        count[index] -= 1
    for i in range(n):
        arr[i] = output[i]
''',

"tim_sort": '''
def tim_sort(arr):
    min_run = 32
    n = len(arr)
    for start in range(0, n, min_run):
        end = min(start + min_run - 1, n - 1)
        insertion_sort_range(arr, start, end)
    size = min_run
    while size < n:
        for left in range(0, n, 2 * size):
            mid = min(left + size - 1, n - 1)
            right = min(left + 2 * size - 1, n - 1)
            if mid < right:
                merge_inplace(arr, left, mid, right)
        size *= 2
    return arr

def insertion_sort_range(arr, left, right):
    for i in range(left + 1, right + 1):
        key = arr[i]
        j = i - 1
        while j >= left and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key

def merge_inplace(arr, left, mid, right):
    left_part = arr[left:mid + 1]
    right_part = arr[mid + 1:right + 1]
    i = j = 0
    k = left
    while i < len(left_part) and j < len(right_part):
        if left_part[i] <= right_part[j]:
            arr[k] = left_part[i]
            i += 1
        else:
            arr[k] = right_part[j]
            j += 1
        k += 1
    while i < len(left_part):
        arr[k] = left_part[i]
        i += 1
        k += 1
    while j < len(right_part):
        arr[k] = right_part[j]
        j += 1
        k += 1
''',
}

class CFGBuilder(ast.NodeVisitor):
    """Extract control flow graph structure from AST."""
    
    def __init__(self):
        self.blocks = []
        self.edges = []
        self.block_id = 0
        self.current_block = None
        
    def new_block(self, label=""):
        self.block_id += 1
        b = {"id": self.block_id, "label": label, "stmts": 0, "type": "basic"}
        self.blocks.append(b)
        return b
    
    def analyze(self, source):
        tree = ast.parse(source)
        # Count structural elements
        stats = {
            "loops": 0,
            "nested_loops": 0,
            "max_loop_depth": 0,
            "conditionals": 0,
            "branches": 0,
            "recursive_calls": 0,
            "function_calls": 0,
            "assignments": 0,
            "comparisons": 0,
            "swaps": 0,
            "list_comprehensions": 0,
            "while_loops": 0,
            "for_loops": 0,
            "break_stmts": 0,
            "return_stmts": 0,
            "augmented_assigns": 0,
            "index_accesses": 0,
            "slices": 0,
            "function_defs": 0,
            "total_lines": len([l for l in source.strip().split('\n') if l.strip() and not l.strip().startswith('#')]),
        }
        
        func_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_names.add(node.name)
                stats["function_defs"] += 1
        
        self._analyze_node(tree, stats, func_names, loop_depth=0)
        
        # Derive CFG properties
        stats["cfg_nodes"] = (stats["loops"] + stats["conditionals"] + 
                              stats["function_defs"] + stats["return_stmts"] + 2)  # +entry+exit
        stats["cfg_edges"] = (stats["cfg_nodes"] - 1 + stats["loops"] + 
                              stats["branches"] + stats["break_stmts"])
        stats["cyclomatic_complexity"] = stats["cfg_edges"] - stats["cfg_nodes"] + 2
        
        return stats
    
    def _analyze_node(self, node, stats, func_names, loop_depth):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.For):
                stats["for_loops"] += 1
                stats["loops"] += 1
                if loop_depth > 0:
                    stats["nested_loops"] += 1
                stats["max_loop_depth"] = max(stats["max_loop_depth"], loop_depth + 1)
                self._analyze_node(child, stats, func_names, loop_depth + 1)
            elif isinstance(child, ast.While):
                stats["while_loops"] += 1
                stats["loops"] += 1
                if loop_depth > 0:
                    stats["nested_loops"] += 1
                stats["max_loop_depth"] = max(stats["max_loop_depth"], loop_depth + 1)
                self._analyze_node(child, stats, func_names, loop_depth + 1)
            elif isinstance(child, ast.If):
                stats["conditionals"] += 1
                stats["branches"] += 1
                if child.orelse:
                    stats["branches"] += 1
                self._analyze_node(child, stats, func_names, loop_depth)
            elif isinstance(child, ast.Break):
                stats["break_stmts"] += 1
            elif isinstance(child, ast.Return):
                stats["return_stmts"] += 1
            elif isinstance(child, ast.Assign):
                stats["assignments"] += 1
                # Detect swaps: a, b = b, a pattern
                if (isinstance(child.value, ast.Tuple) and 
                    len(child.targets) == 1 and isinstance(child.targets[0], ast.Tuple)):
                    stats["swaps"] += 1
                self._analyze_node(child, stats, func_names, loop_depth)
            elif isinstance(child, ast.AugAssign):
                stats["augmented_assigns"] += 1
                self._analyze_node(child, stats, func_names, loop_depth)
            elif isinstance(child, ast.Compare):
                stats["comparisons"] += 1
                self._analyze_node(child, stats, func_names, loop_depth)
            elif isinstance(child, ast.Call):
                stats["function_calls"] += 1
                if isinstance(child.func, ast.Name) and child.func.id in func_names:
                    stats["recursive_calls"] += 1
                self._analyze_node(child, stats, func_names, loop_depth)
            elif isinstance(child, ast.ListComp):
                stats["list_comprehensions"] += 1
                self._analyze_node(child, stats, func_names, loop_depth)
            elif isinstance(child, ast.Subscript):
                stats["index_accesses"] += 1
                if isinstance(child.slice, ast.Slice):
                    stats["slices"] += 1
                self._analyze_node(child, stats, func_names, loop_depth)
            else:
                self._analyze_node(child, stats, func_names, loop_depth)


class DFGBuilder(ast.NodeVisitor):
    """Extract data flow patterns."""
    
    def analyze(self, source):
        tree = ast.parse(source)
        
        stats = {
            "variables_defined": set(),
            "variables_read": set(),
            "def_use_chains": 0,
            "data_dependencies": 0,
            "array_reads": 0,
            "array_writes": 0,
            "temp_variables": 0,
            "accumulator_pattern": False,
            "divide_and_conquer": False,
            "in_place_mutation": False,
            "auxiliary_space": False,
            "data_flow_pattern": "",
        }
        
        # Collect all names
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    stats["variables_defined"].add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    stats["variables_read"].add(node.id)
            if isinstance(node, ast.Subscript):
                if isinstance(node.ctx, ast.Store):
                    stats["array_writes"] += 1
                elif isinstance(node.ctx, ast.Load):
                    stats["array_reads"] += 1
        
        # Count unique variables
        all_vars = stats["variables_defined"] | stats["variables_read"]
        stats["total_variables"] = len(all_vars)
        stats["variables_defined"] = len(stats["variables_defined"])
        stats["variables_read"] = len(stats["variables_read"])
        
        # Detect patterns from source
        src = source.lower()
        stats["accumulator_pattern"] = "result" in src or "output" in src or "append" in src
        stats["divide_and_conquer"] = "mid" in src and ("left" in src or "right" in src)
        stats["in_place_mutation"] = stats["array_writes"] > 0 and not stats["accumulator_pattern"]
        stats["auxiliary_space"] = "output" in src or "result = []" in src or "count" in src
        
        # Approximate def-use chains
        stats["def_use_chains"] = min(stats["variables_defined"], stats["variables_read"])
        stats["data_dependencies"] = stats["array_reads"] + stats["array_writes"]
        
        return stats


# Run analysis
cfg_builder = CFGBuilder()
dfg_builder = DFGBuilder()

results = {}
for name, source in ALGORITHMS.items():
    cfg = cfg_builder.analyze(source)
    dfg = dfg_builder.analyze(source)
    results[name] = {"cfg": cfg, "dfg": dfg}

# Output as JSON
print(json.dumps(results, indent=2))
