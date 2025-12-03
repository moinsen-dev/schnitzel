#!/usr/bin/env python3
"""
Verification script for F001: Schema parser can load a valid YAML file with basic model definition.

This script follows the exact test steps specified in the feature requirements.
"""

from pathlib import Path
from schnitzel.schema import SchemaParser

print("=" * 80)
print("F001 FEATURE VERIFICATION")
print("=" * 80)
print()

# Step 1: Create a minimal YAML schema file with one model (User) and two fields (id: uuid, name: string)
print("Step 1: Using minimal YAML schema file...")
schema_file = Path("tests/integration/fixtures/minimal_user_schema.yaml")
print(f"  File: {schema_file}")
print(f"  Exists: {schema_file.exists()}")
print()

# Step 2: Call SchemaParser.parse(filepath) with the test file
print("Step 2: Calling SchemaParser.parse()...")
parser = SchemaParser()
schema = parser.parse(schema_file)
print(f"  ✓ Parse successful")
print()

# Step 3: Verify parser returns a SchnitzelSchema object
print("Step 3: Verify parser returns a SchnitzelSchema object...")
from schnitzel.schema import SchnitzelSchema
assert isinstance(schema, SchnitzelSchema)
print(f"  ✓ Returned object type: {type(schema).__name__}")
print()

# Step 4: Verify schema.models contains exactly one model
print("Step 4: Verify schema.models contains exactly one model...")
assert len(schema.models) == 1
print(f"  ✓ Number of models: {len(schema.models)}")
print()

# Step 5: Verify model.name equals 'User'
print("Step 5: Verify model.name equals 'User'...")
assert "User" in schema.models
user_model = schema.models["User"]
assert user_model.name == "User"
print(f"  ✓ Model name: {user_model.name}")
print()

# Step 6: Verify model has two fields with correct names and types
print("Step 6: Verify model has two fields with correct names and types...")
assert len(user_model.fields) == 2
print(f"  ✓ Number of fields: {len(user_model.fields)}")

# Check id field
assert "id" in user_model.fields
id_field = user_model.fields["id"]
assert id_field.type == "uuid"
assert id_field.primary is True
print(f"  ✓ Field 'id': type={id_field.type}, primary={id_field.primary}")

# Check name field
assert "name" in user_model.fields
name_field = user_model.fields["name"]
assert name_field.type == "string"
print(f"  ✓ Field 'name': type={name_field.type}")
print()

# Step 7: Verify no parse errors are raised
print("Step 7: Verify no parse errors were raised...")
print("  ✓ All parsing completed successfully without errors")
print()

print("=" * 80)
print("✓ F001 FEATURE VERIFICATION PASSED")
print("=" * 80)
print()
print("Summary:")
print("  - Schema parser successfully loads valid YAML files")
print("  - Parser returns SchnitzelSchema objects")
print("  - Models are correctly parsed with fields and types")
print("  - Field metadata (primary, type) is preserved")
print()
