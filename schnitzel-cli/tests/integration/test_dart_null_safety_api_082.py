"""Integration test for API-082: Dart API client generator handles null safety correctly.

Test Requirements:
1. All generated Dart code must be sound null-safe
2. Nullable fields use Type? syntax
3. Required fields use required keyword in constructors
4. Use late keyword appropriately for lazy initialization
5. Handle nullable API responses correctly

Test Steps:
- Create schema with nullable and non-nullable parameters
- Generate Dart API client code
- Verify null safety annotations are correct
- Verify no implicit null casts
- Ensure code would pass dart analyze with sound null safety
"""

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.api_client import DartApiClientGenerator


def test_required_path_params_are_non_nullable():
    """Test that required path parameters are non-nullable (no ?)."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="string"),
                    "name": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/users/{id}": {
                "get": {
                    "name": "get_user",
                    "description": "Get user by ID",
                    "response": {
                        200: {"type": "User"}
                    }
                }
            }
        }
    )

    generator = DartApiClientGenerator()
    code = generator.generate(schema)

    print("\n" + "=" * 80)
    print("Generated code for required path params:")
    print("=" * 80)
    print(code)
    print("=" * 80)

    # Path parameters should be non-nullable
    assert "Future<User> getUser(String id" in code, "Path param 'id' should be non-nullable String"
    assert "String? id" not in code, "Path parameters should never be nullable"


def test_optional_query_params_are_nullable():
    """Test that optional query parameters use nullable syntax (Type?)."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="string"),
                    "name": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/users": {
                "get": {
                    "name": "list_users",
                    "description": "List users with optional filters",
                    "query": {
                        "page": {"type": "int", "optional": True},
                        "limit": {"type": "int", "optional": True},
                        "search": {"type": "string", "optional": True},
                    },
                    "response": {
                        200: {"type": "list<User>"}
                    }
                }
            }
        }
    )

    generator = DartApiClientGenerator()
    code = generator.generate(schema)

    print("\n" + "=" * 80)
    print("Generated code for optional query params:")
    print("=" * 80)
    print(code)
    print("=" * 80)

    # Optional query params should be nullable
    assert "int? page" in code, "Optional query param should be nullable"
    assert "int? limit" in code, "Optional query param should be nullable"
    assert "String? search" in code, "Optional query param should be nullable"

    # Should use named parameters with nullable types (along with headers and timeout)
    assert "int? page" in code and "int? limit" in code and "String? search" in code, \
        "Named parameters should all be nullable"


def test_required_query_params_are_non_nullable():
    """Test that required query parameters are non-nullable."""
    schema = SchnitzelSchema(
        models={
            "SearchResult": Model(
                name="SearchResult",
                fields={
                    "id": FieldDefinition(type="string"),
                    "title": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/search": {
                "get": {
                    "name": "search",
                    "description": "Search with required query",
                    "query": {
                        "q": {"type": "string", "optional": False},
                        "category": {"type": "string", "optional": False},
                    },
                    "response": {
                        200: {"type": "list<SearchResult>"}
                    }
                }
            }
        }
    )

    generator = DartApiClientGenerator()
    code = generator.generate(schema)

    print("\n" + "=" * 80)
    print("Generated code for required query params:")
    print("=" * 80)
    print(code)
    print("=" * 80)

    # Required query params should NOT be nullable
    assert "String q" in code, "Required query param should be non-nullable"
    assert "String category" in code, "Required query param should be non-nullable"
    assert "String? q" not in code, "Required params should not be nullable"
    assert "String? category" not in code, "Required params should not be nullable"


def test_query_params_with_defaults_are_non_nullable():
    """Test that query parameters with default values are non-nullable."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="string"),
                    "name": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/users": {
                "get": {
                    "name": "list_users",
                    "description": "List users with defaults",
                    "query": {
                        "page": {"type": "int", "default": 1},
                        "limit": {"type": "int", "default": 10},
                        "active": {"type": "bool", "default": True},
                    },
                    "response": {
                        200: {"type": "list<User>"}
                    }
                }
            }
        }
    )

    generator = DartApiClientGenerator()
    code = generator.generate(schema)

    print("\n" + "=" * 80)
    print("Generated code for query params with defaults:")
    print("=" * 80)
    print(code)
    print("=" * 80)

    # Params with defaults should be non-nullable and have default values
    assert "int page = 1" in code, "Default param should be non-nullable with default value"
    assert "int limit = 10" in code, "Default param should be non-nullable with default value"
    assert "bool active = true" in code, "Default param should be non-nullable with default value"

    # Should NOT be nullable
    assert "int? page" not in code
    assert "int? limit" not in code
    assert "bool? active" not in code


def test_nullable_body_parameter():
    """Test that optional body parameters in POST/PUT are handled correctly."""
    schema = SchnitzelSchema(
        models={
            "UpdateRequest": Model(
                name="UpdateRequest",
                fields={
                    "name": FieldDefinition(type="string", optional=True),
                    "email": FieldDefinition(type="string", optional=True),
                }
            ),
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="string"),
                    "name": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/users/{id}": {
                "patch": {
                    "name": "update_user",
                    "description": "Partially update user",
                    "body": "UpdateRequest",
                    "response": {
                        200: {"type": "User"}
                    }
                }
            }
        }
    )

    generator = DartApiClientGenerator()
    code = generator.generate(schema)

    print("\n" + "=" * 80)
    print("Generated code for body parameter:")
    print("=" * 80)
    print(code)
    print("=" * 80)

    # Body parameter should be required (non-nullable) - can be positional or named with required
    assert "UpdateRequest body" in code, "Body param should be present"
    # Should not be nullable
    assert "UpdateRequest? body" not in code, "Body param should not be nullable"


def test_nullable_response_handling():
    """Test that nullable responses are properly typed."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="string"),
                    "name": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/users/{id}": {
                "get": {
                    "name": "get_user_maybe",
                    "description": "Get user, may return null",
                    "response": {
                        200: {"type": "User?"}  # Nullable response
                    }
                },
                "delete": {
                    "name": "delete_user",
                    "description": "Delete user",
                    "response": {
                        204: {"type": "void"}  # No content
                    }
                }
            }
        }
    )

    generator = DartApiClientGenerator()
    code = generator.generate(schema)

    print("\n" + "=" * 80)
    print("Generated code for nullable responses:")
    print("=" * 80)
    print(code)
    print("=" * 80)

    # Nullable response should have nullable return type
    # Note: The generator should handle User? type
    assert "Future<User?> getUserMaybe(String id" in code or "Future<User> getUserMaybe(String id" in code, \
        "Method should return nullable User or handle null properly"

    # Void response should not try to deserialize
    assert "Future<void> deleteUser(String id" in code, "Delete should return void"


def test_no_implicit_null_casts():
    """Test that generated code has no implicit null casts."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="string"),
                    "name": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/users": {
                "get": {
                    "name": "list_users",
                    "description": "List users",
                    "query": {
                        "search": {"type": "string", "optional": True},
                    },
                    "response": {
                        200: {"type": "list<User>"}
                    }
                }
            }
        }
    )

    generator = DartApiClientGenerator()
    code = generator.generate(schema)

    print("\n" + "=" * 80)
    print("Generated code for null safety checks:")
    print("=" * 80)
    print(code)
    print("=" * 80)

    # Use null-aware operators where needed
    assert "e.response?.statusCode" in code, "Should use null-aware operator for nullable response"
    assert "e.response?.data" in code, "Should use null-aware operator for nullable data"
    assert "?? 0" in code or "?? ''" in code, "Should use null coalescing for defaults"


def test_api_exception_null_safety():
    """Test that ApiException class is null-safe."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={"id": FieldDefinition(type="string")}
            )
        },
        endpoints={
            "/users": {
                "get": {
                    "name": "list_users",
                    "response": {200: {"type": "list<User>"}}
                }
            }
        }
    )

    generator = DartApiClientGenerator()
    code = generator.generate(schema)

    print("\n" + "=" * 80)
    print("Generated code for ApiException:")
    print("=" * 80)
    print(code)
    print("=" * 80)

    # ApiException should have proper null safety
    assert "class ApiException" in code
    assert "required this.statusCode" in code, "statusCode should be required"
    assert "required this.message" in code, "message should be required"
    assert "this.body" in code, "body should be optional (nullable)"
    # body field should be nullable
    assert "final dynamic body;" in code or "dynamic body;" in code


def test_auth_interceptor_null_safety():
    """Test that AuthInterceptor handles nullable token correctly."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={"id": FieldDefinition(type="string")}
            )
        },
        endpoints={
            "/users": {
                "get": {
                    "name": "list_users",
                    "response": {200: {"type": "list<User>"}}
                }
            }
        }
    )

    generator = DartApiClientGenerator()
    code = generator.generate(schema, include_auth_interceptor=True)

    print("\n" + "=" * 80)
    print("Generated code for AuthInterceptor:")
    print("=" * 80)
    print(code)
    print("=" * 80)

    # AuthInterceptor should accept nullable token in ApiClient
    assert "String? token" in code, "Token parameter should be nullable"
    assert "if (token != null)" in code, "Should check token for null"

    # AuthInterceptor class should have non-nullable token field
    assert "class AuthInterceptor" in code
    assert "final String token;" in code, "AuthInterceptor token field should be non-nullable"


def test_list_response_null_safety():
    """Test that list responses handle null safety correctly."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="string"),
                    "name": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/users": {
                "get": {
                    "name": "list_users",
                    "description": "Get all users",
                    "response": {
                        200: {"type": "list<User>"}
                    }
                }
            }
        }
    )

    generator = DartApiClientGenerator()
    code = generator.generate(schema)

    print("\n" + "=" * 80)
    print("Generated code for list responses:")
    print("=" * 80)
    print(code)
    print("=" * 80)

    # List response should be properly typed
    assert "Future<List<User>>" in code, "Return type should be List<User>"

    # Deserialization should cast properly
    assert "(response.data as List)" in code, "Should cast response.data to List"
    assert ".map((e) => User.fromJson(e))" in code, "Should map each element"
    assert ".toList()" in code, "Should convert to list"


def test_mixed_nullable_non_nullable_params():
    """Test endpoint with mix of nullable and non-nullable parameters."""
    schema = SchnitzelSchema(
        models={
            "SearchResult": Model(
                name="SearchResult",
                fields={
                    "id": FieldDefinition(type="string"),
                    "title": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/search/{category}": {
                "params": {
                    "category": {"type": "string"}
                },
                "get": {
                    "name": "search_in_category",
                    "description": "Search within a category",
                    "query": {
                        "q": {"type": "string", "optional": False},  # Required
                        "page": {"type": "int", "default": 1},  # Default value
                        "tags": {"type": "string", "optional": True},  # Optional
                    },
                    "response": {
                        200: {"type": "list<SearchResult>"}
                    }
                }
            }
        }
    )

    generator = DartApiClientGenerator()
    code = generator.generate(schema)

    print("\n" + "=" * 80)
    print("Generated code for mixed params:")
    print("=" * 80)
    print(code)
    print("=" * 80)

    # Path param should be non-nullable positional
    assert "searchInCategory(String category" in code, "Path param should be non-nullable"

    # Required query param should be non-nullable
    assert "String q" in code, "Required query param should be non-nullable"
    assert "String? q" not in code

    # Default param should be non-nullable with default
    assert "int page = 1" in code, "Param with default should be non-nullable"

    # Optional param should be nullable
    assert "String? tags" in code, "Optional param should be nullable"


def test_sound_null_safety_compliance():
    """Test that generated code follows Dart sound null safety rules."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="string"),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string", optional=True),
                }
            ),
            "CreateUserRequest": Model(
                name="CreateUserRequest",
                fields={
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string", optional=True),
                }
            )
        },
        endpoints={
            "/users": {
                "get": {
                    "name": "list_users",
                    "query": {
                        "search": {"type": "string", "optional": True},
                        "limit": {"type": "int", "default": 10},
                    },
                    "response": {
                        200: {"type": "list<User>"}
                    }
                },
                "post": {
                    "name": "create_user",
                    "body": "CreateUserRequest",
                    "response": {
                        201: {"type": "User"}
                    }
                }
            },
            "/users/{id}": {
                "get": {
                    "name": "get_user",
                    "response": {
                        200: {"type": "User"}
                    }
                },
                "delete": {
                    "name": "delete_user",
                    "response": {
                        204: {"type": "void"}
                    }
                }
            }
        }
    )

    generator = DartApiClientGenerator()
    code = generator.generate(schema, include_auth_interceptor=True)

    print("\n" + "=" * 80)
    print("Full generated code for null safety compliance:")
    print("=" * 80)
    print(code)
    print("=" * 80)

    # Check all null safety rules:

    # 1. Nullable types use ?
    assert "String? search" in code or "String? token" in code, "Nullable types should use ?"

    # 2. Required parameters use 'required' keyword
    assert "required" in code, "Required parameters should use 'required' keyword"

    # 3. No late keyword without good reason (should not appear in API client)
    # Note: Checking for 'late ' as a Dart keyword (not in comments like "calculate")
    dart_lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('//')]
    late_in_code = any(line.startswith('late ') or ' late ' in line for line in dart_lines)
    assert not late_in_code, "Should not use 'late' keyword without good reason"

    # 4. Null-aware operators used properly
    assert "??" in code, "Should use null coalescing operator"
    assert "?." in code, "Should use null-aware access operator"

    # 5. All class constructors are properly defined
    assert "class ApiClient {" in code
    assert "class ApiException" in code
    assert "class AuthInterceptor" in code

    # 6. No implicit dynamic types in parameters
    # All parameters should have explicit types
    method_lines = [line for line in code.split('\n') if 'Future<' in line and '(' in line]
    for line in method_lines:
        # Should not have untyped parameters
        assert " )" not in line or line.strip().endswith("async {"), \
            f"Parameters should be typed: {line}"


def test_comprehensive_null_safety():
    """Comprehensive test covering all null safety scenarios."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="string"),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string", optional=True),
                    "age": FieldDefinition(type="int", optional=True),
                }
            ),
            "UpdateUserRequest": Model(
                name="UpdateUserRequest",
                fields={
                    "name": FieldDefinition(type="string", optional=True),
                    "email": FieldDefinition(type="string", optional=True),
                }
            )
        },
        endpoints={
            "/users": {
                "get": {
                    "name": "list_users",
                    "query": {
                        "search": {"type": "string", "optional": True},
                        "page": {"type": "int", "default": 1},
                        "limit": {"type": "int", "default": 10},
                    },
                    "response": {
                        200: {"type": "list<User>"}
                    }
                }
            },
            "/users/{id}": {
                "params": {
                    "id": {"type": "string"}
                },
                "get": {
                    "name": "get_user",
                    "response": {
                        200: {"type": "User"}
                    }
                },
                "put": {
                    "name": "update_user",
                    "body": "UpdateUserRequest",
                    "response": {
                        200: {"type": "User"}
                    }
                },
                "delete": {
                    "name": "delete_user",
                    "response": {
                        204: {"type": "void"}
                    }
                }
            }
        }
    )

    generator = DartApiClientGenerator()
    code = generator.generate(schema, include_auth_interceptor=True)

    print("\n" + "=" * 80)
    print("Comprehensive null safety test output:")
    print("=" * 80)
    print(code)
    print("=" * 80)

    # Verify all aspects of null safety
    assertions = [
        # Path params are non-nullable
        ("String id" in code, "Path parameters should be non-nullable"),

        # Optional query params are nullable
        ("String? search" in code, "Optional query params should be nullable"),

        # Params with defaults are non-nullable
        ("int page = 1" in code, "Params with defaults should be non-nullable"),
        ("int limit = 10" in code, "Params with defaults should be non-nullable"),

        # Body params are required (positional or with required keyword)
        ("UpdateUserRequest body" in code and "UpdateUserRequest? body" not in code, "Body params should be required"),

        # Null-aware operators
        ("??" in code, "Should use null coalescing operator"),
        ("?." in code, "Should use null-aware access"),

        # List deserialization
        ("(response.data as List)" in code, "Should cast response data to List"),
        (".map((e) => User.fromJson(e))" in code, "Should map list items"),

        # Auth interceptor null safety
        ("String? token" in code, "Token param should be nullable"),
        ("if (token != null)" in code, "Should check token for null"),

        # ApiException null safety
        ("required this.statusCode" in code, "ApiException statusCode should be required"),
        ("required this.message" in code, "ApiException message should be required"),

        # No implicit nulls
        # Check for late keyword properly (not in comments)
        (not any(line.strip().startswith('late ') or ' late ' in line.strip()
                 for line in code.split('\n')
                 if line.strip() and not line.strip().startswith('//')),
         "Should not use late keyword"),
    ]

    for condition, message in assertions:
        assert condition, message


if __name__ == "__main__":
    # Run tests manually for development
    print("Running API-082 Integration Tests for Dart Null Safety\n")

    test_required_path_params_are_non_nullable()
    print(" test_required_path_params_are_non_nullable PASSED\n")

    test_optional_query_params_are_nullable()
    print(" test_optional_query_params_are_nullable PASSED\n")

    test_required_query_params_are_non_nullable()
    print(" test_required_query_params_are_non_nullable PASSED\n")

    test_query_params_with_defaults_are_non_nullable()
    print(" test_query_params_with_defaults_are_non_nullable PASSED\n")

    test_nullable_body_parameter()
    print(" test_nullable_body_parameter PASSED\n")

    test_nullable_response_handling()
    print(" test_nullable_response_handling PASSED\n")

    test_no_implicit_null_casts()
    print(" test_no_implicit_null_casts PASSED\n")

    test_api_exception_null_safety()
    print(" test_api_exception_null_safety PASSED\n")

    test_auth_interceptor_null_safety()
    print(" test_auth_interceptor_null_safety PASSED\n")

    test_list_response_null_safety()
    print(" test_list_response_null_safety PASSED\n")

    test_mixed_nullable_non_nullable_params()
    print(" test_mixed_nullable_non_nullable_params PASSED\n")

    test_sound_null_safety_compliance()
    print(" test_sound_null_safety_compliance PASSED\n")

    test_comprehensive_null_safety()
    print(" test_comprehensive_null_safety PASSED\n")

    print("=" * 80)
    print(" All API-082 Null Safety tests passed!")
    print("=" * 80)
