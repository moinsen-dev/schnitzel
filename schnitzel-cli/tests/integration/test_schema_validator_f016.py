"""
Integration test for F016: Schema validator detects circular dependency in relationships.

Test steps:
1. Create A model with belongsTo: b
2. Create B model with belongsTo: a
3. Call SchemaValidator.validate(schema)
4. Verify validation fails or warns about circular dependency
5. Verify error shows the dependency cycle (A -> B -> A)
6. Verify error explains why this is problematic
7. Verify error suggests breaking the cycle
"""

from schnitzel.schema.models import FieldDefinition, Model, Relation, SchnitzelSchema
from schnitzel.schema.validator import SchemaValidator, ValidationResult


def test_simple_circular_dependency():
    """
    Test F016: Schema validator detects circular dependency in relationships.

    This test creates a schema with two models that have a circular dependency:
    - Model A has a belongsTo relationship to Model B
    - Model B has a belongsTo relationship to Model A
    The validator should detect this cycle and report it clearly.
    """
    # Step 1-2: Create A model with belongsTo: b and B model with belongsTo: a
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "A": Model(
                name="A",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "b_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "b": Relation(
                        type="belongsTo",
                        model="B",
                        foreign_key="b_id"
                    )
                }
            ),
            "B": Model(
                name="B",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "a_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "a": Relation(
                        type="belongsTo",
                        model="A",
                        foreign_key="a_id"
                    )
                }
            )
        }
    )

    # Step 3: Call SchemaValidator.validate(schema)
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Step 4: Verify validation fails or warns about circular dependency
    assert isinstance(result, ValidationResult), "Validator should return ValidationResult"
    assert result.valid is False, "Validation should fail when circular dependency exists"
    assert len(result.errors) > 0, "Should have at least one error"

    # Step 5: Verify error shows the dependency cycle (A -> B -> A)
    error_text = "\n".join(result.errors)
    assert "circular dependency" in error_text.lower(), "Error should mention circular dependency"
    assert "A" in error_text, "Error should mention model A"
    assert "B" in error_text, "Error should mention model B"
    assert "->" in error_text, "Error should show the cycle with arrows"

    # Step 6: Verify error explains why this is problematic
    assert (
        "database schema generation" in error_text.lower() or
        "data insertion order" in error_text.lower() or
        "issues" in error_text.lower()
    ), "Error should explain why circular dependencies are problematic"

    # Step 7: Verify error suggests breaking the cycle
    assert (
        "junction table" in error_text.lower() or
        "removing" in error_text.lower() or
        "suggestion" in error_text.lower()
    ), "Error should suggest how to break the cycle"

    print("\n" + "="*70)
    print("Test F016 passed: Schema validator detects circular dependency")
    print("="*70)
    print(f"\nError message:\n{error_text}")


def test_three_way_circular_dependency():
    """
    Test circular dependency with three models: A -> B -> C -> A.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "A": Model(
                name="A",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "b_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "b": Relation(type="belongsTo", model="B", foreign_key="b_id")
                }
            ),
            "B": Model(
                name="B",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "c_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "c": Relation(type="belongsTo", model="C", foreign_key="c_id")
                }
            ),
            "C": Model(
                name="C",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "a_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "a": Relation(type="belongsTo", model="A", foreign_key="a_id")
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation fails
    assert result.valid is False, "Validation should fail for three-way circular dependency"
    assert len(result.errors) > 0, "Should have at least one error"

    error_text = "\n".join(result.errors)
    assert "circular dependency" in error_text.lower(), "Error should mention circular dependency"
    # Check that all three models are mentioned
    assert "A" in error_text and "B" in error_text and "C" in error_text, (
        "Error should mention all three models in the cycle"
    )

    print("\n" + "="*70)
    print("Test passed: Three-way circular dependency detected")
    print("="*70)
    print(f"\nError message:\n{error_text}")


def test_valid_unidirectional_relationship():
    """
    Test that valid unidirectional relationships do not trigger false positives.
    A -> B (but B does not reference A)
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "A": Model(
                name="A",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "b_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "b": Relation(type="belongsTo", model="B", foreign_key="b_id")
                }
            ),
            "B": Model(
                name="B",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                }
                # No relations back to A
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passes
    assert result.valid is True, f"Unidirectional relationship should be valid. Errors: {result.errors}"
    assert len(result.errors) == 0, "Should have no errors for valid unidirectional relationship"

    print("\n" + "="*70)
    print("Test passed: Unidirectional relationship does not trigger false positive")
    print("="*70)


def test_valid_bidirectional_with_hasmany():
    """
    Test that valid bidirectional relationships (hasMany + belongsTo) are allowed.
    User hasMany Posts, Post belongsTo User - this is valid and common.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "posts": Relation(type="hasMany", model="Post")
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                    "user_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User",
                        foreign_key="user_id"
                    )
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passes - hasMany + belongsTo is valid
    assert result.valid is True, (
        f"Valid hasMany + belongsTo bidirectional relationship should pass. Errors: {result.errors}"
    )
    assert len(result.errors) == 0, "Should have no errors for valid bidirectional relationship"

    print("\n" + "="*70)
    print("Test passed: Valid hasMany + belongsTo bidirectional relationship allowed")
    print("="*70)


def test_circular_dependency_with_hasmany():
    """
    Test that hasMany relationships alone do NOT create problematic circular dependencies.
    A hasMany B, B hasMany A - this is valid because hasMany relationships don't create
    database-level circular dependencies (they're implemented via foreign keys on the
    opposite side).
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "A": Model(
                name="A",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                },
                relations={
                    "bs": Relation(type="hasMany", model="B")
                }
            ),
            "B": Model(
                name="B",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                },
                relations={
                    "as": Relation(type="hasMany", model="A")
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passes - hasMany relationships don't create problematic cycles
    assert result.valid is True, (
        f"hasMany relationships alone should not create circular dependencies. Errors: {result.errors}"
    )
    assert len(result.errors) == 0, "Should have no errors for hasMany relationships"

    print("\n" + "="*70)
    print("Test passed: hasMany relationships do not create circular dependencies")
    print("="*70)


def test_self_referential_relationship():
    """
    Test that self-referential relationships are detected.
    A model that references itself (e.g., Employee -> Manager, where Manager is also Employee).
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "Employee": Model(
                name="Employee",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "manager_id": FieldDefinition(type="uuid", optional=True),
                },
                relations={
                    "manager": Relation(
                        type="belongsTo",
                        model="Employee",
                        foreign_key="manager_id"
                    )
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation fails (self-reference is a cycle)
    assert result.valid is False, "Validation should fail for self-referential relationship"
    assert len(result.errors) > 0, "Should have at least one error"

    error_text = "\n".join(result.errors)
    assert "circular dependency" in error_text.lower(), "Error should mention circular dependency"
    assert "Employee" in error_text, "Error should mention Employee model"

    print("\n" + "="*70)
    print("Test passed: Self-referential relationship detected as circular")
    print("="*70)


def test_complex_graph_with_one_cycle():
    """
    Test a more complex graph where only part of it has a cycle.
    A -> B -> C -> D
         ^         |
         |_________|
    D and B form a cycle, but A and C are just in the path.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "A": Model(
                name="A",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "b_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "b": Relation(type="belongsTo", model="B", foreign_key="b_id")
                }
            ),
            "B": Model(
                name="B",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "c_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "c": Relation(type="belongsTo", model="C", foreign_key="c_id")
                }
            ),
            "C": Model(
                name="C",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "d_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "d": Relation(type="belongsTo", model="D", foreign_key="d_id")
                }
            ),
            "D": Model(
                name="D",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "b_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "b": Relation(type="belongsTo", model="B", foreign_key="b_id")
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation fails
    assert result.valid is False, "Validation should fail when there's a cycle in the graph"
    assert len(result.errors) > 0, "Should have at least one error"

    error_text = "\n".join(result.errors)
    assert "circular dependency" in error_text.lower(), "Error should mention circular dependency"
    # The cycle should involve B, C, and D
    assert "B" in error_text, "Error should mention B (part of cycle)"

    print("\n" + "="*70)
    print("Test passed: Complex graph with one cycle detected")
    print("="*70)


def test_no_relationships():
    """
    Test that models without any relationships pass validation.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "A": Model(
                name="A",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                }
            ),
            "B": Model(
                name="B",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "value": FieldDefinition(type="int"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passes
    assert result.valid is True, "Validation should pass when there are no relationships"
    assert len(result.errors) == 0, "Should have no errors"

    print("\n" + "="*70)
    print("Test passed: Models without relationships pass validation")
    print("="*70)


def test_error_message_format():
    """
    Verify the error message format matches requirements:
    - Shows the dependency cycle
    - Explains why it's problematic
    - Suggests breaking the cycle
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "A": Model(
                name="A",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "b_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "b": Relation(type="belongsTo", model="B", foreign_key="b_id")
                }
            ),
            "B": Model(
                name="B",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "a_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "a": Relation(type="belongsTo", model="A", foreign_key="a_id")
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    assert len(result.errors) > 0

    error = result.errors[0]

    # Verify error format matches requirements
    lines = error.split("\n")
    assert len(lines) >= 3, "Error should be multi-line with detailed information"

    # Line 1: Should show the cycle
    assert "Circular dependency detected in relationships:" in lines[0]
    assert "->" in lines[0], "Should show cycle with arrows"

    # Line 2: Should explain the problem
    assert (
        "database schema generation" in lines[1].lower() or
        "data insertion order" in lines[1].lower()
    ), "Should explain why circular dependencies are problematic"

    # Line 3: Should suggest solution
    assert "Suggestion:" in lines[2] or "suggestion" in lines[2].lower()
    assert (
        "junction table" in lines[2].lower() or
        "removing" in lines[2].lower()
    ), "Should suggest how to break the cycle"

    print("\n" + "="*70)
    print("Test passed: Error message format is correct")
    print("="*70)
    print(f"\nFull error message:\n{error}")


if __name__ == "__main__":
    # Run all tests
    print("\n" + "="*70)
    print("Running F016 circular dependency detection tests")
    print("="*70)

    test_simple_circular_dependency()
    test_three_way_circular_dependency()
    test_valid_unidirectional_relationship()
    test_valid_bidirectional_with_hasmany()
    test_circular_dependency_with_hasmany()
    test_self_referential_relationship()
    test_complex_graph_with_one_cycle()
    test_no_relationships()
    test_error_message_format()

    print("\n" + "="*70)
    print("All F016 circular dependency tests passed!")
    print("="*70)
