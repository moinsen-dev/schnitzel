# F016 Code Summary

## Key Code Additions

### 1. Circular Dependency Detection Method

**Location:** `schnitzel-cli/src/schnitzel/schema/validator.py`

```python
def _detect_circular_dependencies(self, schema: SchnitzelSchema) -> List[str]:
    """
    Detect circular dependencies in relationships.
    
    Builds a directed graph of relationships and detects cycles using
    depth-first search. Only tracks belongsTo and hasOne relationships.
    """
    errors: List[str] = []

    # Build relationship graph (adjacency list)
    graph: dict[str, List[tuple[str, str, str]]] = {}

    for model_name, model in schema.models.items():
        if model.relations is None:
            continue

        if model_name not in graph:
            graph[model_name] = []

        for relation_name, relation in model.relations.items():
            target_model = relation.model
            # Only track belongsTo and hasOne (actual dependencies)
            if target_model in schema.models and relation.type in ["belongsTo", "hasOne"]:
                graph[model_name].append((target_model, relation.type, relation_name))

    # DFS cycle detection
    visited: Set[str] = set()
    in_path: Set[str] = set()
    cycles_found: List[List[str]] = []

    def dfs(node: str, path: List[str]) -> None:
        if node in in_path:
            # Found a cycle - extract it from path
            cycle_start_idx = path.index(node)
            cycle = path[cycle_start_idx:] + [node]
            if cycle not in cycles_found:
                cycles_found.append(cycle)
            return

        if node in visited:
            return

        visited.add(node)
        in_path.add(node)
        path.append(node)

        # Visit all neighbors
        if node in graph:
            for target_model, _, _ in graph[node]:
                dfs(target_model, path.copy())

        in_path.remove(node)

    # Run DFS from each unvisited node
    for model_name in schema.models.keys():
        if model_name not in visited:
            dfs(model_name, [])

    # Build error messages for each cycle
    for cycle in cycles_found:
        error_msg = self._build_circular_dependency_error(cycle)
        errors.append(error_msg)

    return errors
```

### 2. Error Message Builder

```python
def _build_circular_dependency_error(self, cycle: List[str]) -> str:
    """
    Build an error message for a circular dependency.
    
    Args:
        cycle: List of model names forming the cycle (last element repeats first)
    
    Returns:
        Formatted error message string
    """
    error_parts = []

    # Build cycle visualization
    cycle_str = " -> ".join(cycle)

    # Main error
    error_parts.append(f"Circular dependency detected in relationships: {cycle_str}")

    # Explanation of why this is problematic
    error_parts.append(
        "This may cause issues with database schema generation and data insertion order."
    )

    # Helpful suggestion
    error_parts.append(
        "Suggestion: Consider using a junction table or removing one relationship."
    )

    return "\n".join(error_parts)
```

### 3. Integration with Validator

```python
def _validate_relationships(self, schema: SchnitzelSchema) -> List[str]:
    """Validate that all relationship targets reference existing models."""
    errors: List[str] = []

    # ... existing validation code ...

    # Check for circular dependencies in relationships
    circular_errors = self._detect_circular_dependencies(schema)
    errors.extend(circular_errors)

    return errors
```

## Algorithm Overview

### Graph Construction
1. Build adjacency list from model relationships
2. Only include belongsTo and hasOne edges (not hasMany)
3. Store target model, relation type, and relation name

### Cycle Detection (DFS)
1. Track visited nodes globally
2. Track nodes in current path
3. When node is already in path → cycle found
4. Extract cycle from path starting at first occurrence
5. Avoid duplicate cycles

### Error Reporting
1. Format each cycle as "A -> B -> C -> A"
2. Explain why it's problematic
3. Suggest solutions

## Test Coverage

- Simple cycles (A -> B -> A)
- Multi-way cycles (A -> B -> C -> A)
- Self-referential (A -> A)
- Valid patterns (hasMany + belongsTo)
- Complex graphs with partial cycles
- Edge cases (no relationships, unidirectional)
