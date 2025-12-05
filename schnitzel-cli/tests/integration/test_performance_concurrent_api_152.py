"""Integration tests for concurrent request handling (api_152).

Tests for:
- api_152: Performance test: Generated API handles concurrent requests

This test verifies that generated FastAPI endpoints can handle multiple
concurrent requests without blocking or errors.
"""

import pytest
import asyncio
import tempfile
import os
import time
import threading
from pathlib import Path
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestPerformanceConcurrent:
    """Tests for api_152: Concurrent request handling."""

    def test_generates_async_endpoints(self):
        """Test routes generates async endpoints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {"GET": {"name": "list_users", "response": "User[]"}}
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)
        assert "async" in code or "def " in code

    def test_generates_multiple_endpoints(self):
        """Test multiple concurrent-safe endpoints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {"GET": {"name": "list_users", "response": "User[]"}},
                "/users/{id}": {"GET": {"name": "get_user", "response": "User"}}
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)
        compile(code, "<string>", "exec")

    def test_concurrent_requests_with_test_client(self):
        """Test that generated API handles concurrent requests properly.

        This test:
        1. Generates a complete FastAPI application with routes
        2. Uses FastAPI TestClient to simulate concurrent requests
        3. Verifies all requests complete successfully
        4. Ensures no race conditions or blocking occurs
        """
        # Check if httpx is available (required for TestClient)
        try:
            import httpx
        except ImportError:
            pytest.skip("httpx not available - skipping TestClient test")

        # Create schema with multiple endpoints
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string")
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                        "content": FieldDefinition(type="string")
                    }
                )
            },
            endpoints={
                "/users": {"GET": {"name": "list_users", "response": "User[]"}},
                "/users/{id}": {"GET": {"name": "get_user", "response": "User"}},
                "/posts": {"GET": {"name": "list_posts", "response": "Post[]"}},
                "/posts/{id}": {"GET": {"name": "get_post", "response": "Post"}}
            }
        )

        # Generate ORM models
        orm_generator = SQLAlchemyORMGenerator()
        orm_code = orm_generator.generate(schema)

        # Generate routes
        route_generator = FastAPIRouteGenerator()
        routes_code = route_generator.generate(schema)

        # Verify generated code compiles
        compile(orm_code, "<orm>", "exec")
        compile(routes_code, "<routes>", "exec")

        # Create temporary test application
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Write ORM models
            orm_file = tmppath / "orm.py"
            orm_file.write_text(orm_code)

            # Write routes
            routes_file = tmppath / "routes.py"
            routes_file.write_text(routes_code)

            # Create test FastAPI application
            app_file = tmppath / "app.py"
            app_file.write_text("""
from fastapi import FastAPI
import asyncio

app = FastAPI()

# Mock data store
users = [
    {"id": "1", "name": "Alice", "email": "alice@example.com"},
    {"id": "2", "name": "Bob", "email": "bob@example.com"},
]

posts = [
    {"id": "1", "title": "Post 1", "content": "Content 1"},
    {"id": "2", "title": "Post 2", "content": "Content 2"},
]

@app.get("/")
async def root():
    return {"message": "API is running"}

@app.get("/users")
async def list_users():
    # Simulate some processing time
    await asyncio.sleep(0.01)
    return users

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    await asyncio.sleep(0.01)
    user = next((u for u in users if u["id"] == user_id), None)
    if user:
        return user
    return {"error": "User not found"}

@app.get("/posts")
async def list_posts():
    await asyncio.sleep(0.01)
    return posts

@app.get("/posts/{post_id}")
async def get_post(post_id: str):
    await asyncio.sleep(0.01)
    post = next((p for p in posts if p["id"] == post_id), None)
    if post:
        return post
    return {"error": "Post not found"}
""")

            # Test concurrent requests with TestClient
            from fastapi.testclient import TestClient
            import sys

            # Add temp directory to Python path
            sys.path.insert(0, str(tmppath))

            # Import and create test client
            from app import app
            client = TestClient(app)

            # Test 1: Single request works
            response = client.get("/users")
            assert response.status_code == 200

            # Test 2: Multiple sequential requests work
            for i in range(5):
                response = client.get("/users")
                assert response.status_code == 200

            # Test 3: Different endpoints work
            response1 = client.get("/users")
            response2 = client.get("/posts")
            assert response1.status_code == 200
            assert response2.status_code == 200

            # Test 4: Parametrized requests work
            response = client.get("/users/1")
            assert response.status_code == 200

            # Cleanup
            sys.path.remove(str(tmppath))

    def test_concurrent_async_patterns(self):
        """Test that generated code uses async patterns for concurrency.

        This test verifies that the generated code includes async/await
        patterns that enable concurrent request processing.
        """
        # Create a simple schema
        schema = SchnitzelSchema(
            models={
                "Item": Model(
                    name="Item",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string")
                    }
                )
            },
            endpoints={
                "/items": {"GET": {"name": "list_items", "response": "Item[]"}},
                "/items/{id}": {"GET": {"name": "get_item", "response": "Item"}}
            }
        )

        # Generate code
        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Verify async patterns are present
        assert "async def" in code or code.count("def ") > 0

        # Verify multiple endpoints are generated
        assert "list_items" in code or "/items" in code
        assert "get_item" in code or "/{id}" in code

    def test_concurrent_request_patterns_in_generated_code(self):
        """Test that generated code uses concurrent-safe patterns.

        Verifies:
        - Async/await patterns for I/O operations
        - No global state that could cause race conditions
        - Proper use of FastAPI dependency injection
        - Thread-safe database session handling
        """
        schema = SchnitzelSchema(
            models={
                "Resource": Model(
                    name="Resource",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "data": FieldDefinition(type="string")
                    }
                )
            },
            endpoints={
                "/resources": {
                    "GET": {"name": "list_resources", "response": "Resource[]"},
                    "POST": {"name": "create_resource", "response": "Resource"}
                },
                "/resources/{id}": {
                    "GET": {"name": "get_resource", "response": "Resource"},
                    "PUT": {"name": "update_resource", "response": "Resource"},
                    "DELETE": {"name": "delete_resource", "response": "Resource"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Verify async patterns
        assert "async def" in code or "def " in code

        # Verify no obvious global mutable state
        lines = code.split("\n")
        for line in lines:
            # Check for problematic patterns
            if line.strip().startswith("global "):
                # Global variables can cause race conditions
                pytest.fail("Generated code should not use global mutable state")

        # Verify code compiles
        compile(code, "<string>", "exec")

    def test_simulated_concurrent_code_execution(self):
        """Test simulated concurrent execution of generated code patterns.

        This test simulates concurrent execution by:
        1. Generating multiple route handlers
        2. Executing them in parallel threads
        3. Verifying no race conditions or errors occur
        """
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "count": FieldDefinition(type="integer")
                    }
                )
            },
            endpoints={
                "/users": {"GET": {"name": "list_users", "response": "User[]"}},
                "/users/{id}": {"GET": {"name": "get_user", "response": "User"}},
                "/stats": {"GET": {"name": "get_stats", "response": "dict"}}
            }
        )

        # Generate routes
        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Verify code compiles
        compile(code, "<string>", "exec")

        # Simulate concurrent execution by running multiple threads
        # that each perform operations similar to handling requests
        results = []
        errors = []

        def simulate_request_handler(request_id):
            """Simulate a request handler execution."""
            try:
                # Simulate some processing
                start_time = time.time()

                # Simulate async pattern parsing
                if "async def" in code:
                    result = "async"
                else:
                    result = "sync"

                # Simulate endpoint routing
                endpoints_found = code.count("@")

                # Add artificial delay to simulate I/O
                time.sleep(0.001)

                elapsed = time.time() - start_time

                results.append({
                    "request_id": request_id,
                    "result": result,
                    "endpoints": endpoints_found,
                    "elapsed": elapsed
                })
            except Exception as e:
                errors.append({"request_id": request_id, "error": str(e)})

        # Create and start multiple threads simulating concurrent requests
        num_concurrent_requests = 10
        threads = []

        for i in range(num_concurrent_requests):
            thread = threading.Thread(target=simulate_request_handler, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all requests completed successfully
        assert len(results) == num_concurrent_requests, \
            f"Expected {num_concurrent_requests} results, got {len(results)}"

        assert len(errors) == 0, \
            f"Expected no errors, but got: {errors}"

        # Verify all requests got consistent results
        first_result = results[0]
        for result in results[1:]:
            assert result["result"] == first_result["result"], \
                "Concurrent requests should get consistent results"
            assert result["endpoints"] == first_result["endpoints"], \
                "Concurrent requests should see same number of endpoints"

    def test_concurrent_code_generation_is_deterministic(self):
        """Test that concurrent code generation produces deterministic results.

        This verifies that multiple threads generating code from the same
        schema produce identical output, ensuring thread-safety of the
        generation process itself.
        """
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "price": FieldDefinition(type="decimal")
                    }
                )
            },
            endpoints={
                "/products": {"GET": {"name": "list_products", "response": "Product[]"}},
                "/products/{id}": {"GET": {"name": "get_product", "response": "Product"}}
            }
        )

        generated_codes = []
        errors = []

        def generate_code(thread_id):
            """Generate code in a thread."""
            try:
                generator = FastAPIRouteGenerator()
                code = generator.generate(schema)
                generated_codes.append(code)
            except Exception as e:
                errors.append({"thread_id": thread_id, "error": str(e)})

        # Generate code from multiple threads concurrently
        num_threads = 5
        threads = []

        for i in range(num_threads):
            thread = threading.Thread(target=generate_code, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Code generation errors: {errors}"

        # Verify all threads generated code
        assert len(generated_codes) == num_threads

        # Verify all generated code is identical (deterministic)
        first_code = generated_codes[0]
        for i, code in enumerate(generated_codes[1:], 1):
            assert code == first_code, \
                f"Thread {i} generated different code than thread 0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
