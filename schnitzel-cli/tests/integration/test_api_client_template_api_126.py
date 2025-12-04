"""Integration test for API_126: API client template correctly iterates over endpoints.

Test Requirements:
1. Create schema with multiple endpoints (GET, POST, PUT, DELETE)
2. Generate Dart API client
3. Verify each endpoint produces a method
4. Verify proper path parameter interpolation (/users/{id} → /users/$id)
5. Verify all HTTP methods are handled correctly

This test verifies the Dart API client generator correctly processes all endpoints
in a schema, properly iterating over different HTTP methods and handling path parameters.
"""

import pytest
from pathlib import Path
import tempfile
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestApiClientTemplateIteration:
    """Test Dart API client generator correctly iterates over all endpoints."""

    def test_all_http_methods_generated(self):
        """Test that GET, POST, PUT, DELETE methods all generate correctly."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True),
                        'email': FieldDefinition(type='string', required=True)
                    }
                ),
                'CreateUserRequest': Model(
                    name='CreateUserRequest',
                    fields={
                        'name': FieldDefinition(type='string', required=True),
                        'email': FieldDefinition(type='string', required=True)
                    }
                ),
                'UpdateUserRequest': Model(
                    name='UpdateUserRequest',
                    fields={
                        'name': FieldDefinition(type='string', optional=True),
                        'email': FieldDefinition(type='string', optional=True)
                    }
                )
            },
            endpoints={
                '/users': {
                    'GET': {
                        'name': 'list_users',
                        'description': 'Get all users',
                        'response': {
                            200: {'type': 'List[User]'}
                        }
                    },
                    'POST': {
                        'name': 'create_user',
                        'description': 'Create a new user',
                        'body': 'CreateUserRequest',
                        'response': {
                            201: {'type': 'User'}
                        }
                    }
                },
                '/users/{id}': {
                    'params': {
                        'id': {'type': 'uuid'}
                    },
                    'GET': {
                        'name': 'get_user',
                        'description': 'Get a user by ID',
                        'response': {
                            200: {'type': 'User'}
                        }
                    },
                    'PUT': {
                        'name': 'update_user',
                        'description': 'Update a user',
                        'body': 'UpdateUserRequest',
                        'response': {
                            200: {'type': 'User'}
                        }
                    },
                    'DELETE': {
                        'name': 'delete_user',
                        'description': 'Delete a user',
                        'response': {
                            204: {'type': 'void'}
                        }
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Verify all methods are generated
        assert 'Future<List<User>> listUsers()' in code, "GET /users should generate listUsers method"
        assert 'Future<User> createUser(' in code, "POST /users should generate createUser method"
        assert 'Future<User> getUser(String id)' in code, "GET /users/{id} should generate getUser method"
        assert 'Future<User> updateUser(' in code, "PUT /users/{id} should generate updateUser method"
        assert 'Future<void> deleteUser(String id)' in code, "DELETE /users/{id} should generate deleteUser method"

        # Verify HTTP method calls
        assert "_dio.get('/users')" in code, "listUsers should call _dio.get"
        assert "_dio.post('/users'" in code, "createUser should call _dio.post"
        assert "_dio.get('/users/$id')" in code, "getUser should call _dio.get with path param"
        assert "_dio.put('/users/$id'" in code, "updateUser should call _dio.put with path param"
        assert "_dio.delete('/users/$id')" in code, "deleteUser should call _dio.delete with path param"

    def test_path_parameter_interpolation(self):
        """Test that path parameters are correctly interpolated from {id} to $id."""
        schema = SchnitzelSchema(
            models={
                'Post': Model(
                    name='Post',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string')
                    }
                ),
                'Comment': Model(
                    name='Comment',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'text': FieldDefinition(type='string')
                    }
                )
            },
            endpoints={
                '/posts/{postId}': {
                    'params': {
                        'postId': {'type': 'uuid'}
                    },
                    'GET': {
                        'name': 'get_post',
                        'response': {
                            200: {'type': 'Post'}
                        }
                    }
                },
                '/posts/{postId}/comments/{commentId}': {
                    'params': {
                        'postId': {'type': 'uuid'},
                        'commentId': {'type': 'uuid'}
                    },
                    'GET': {
                        'name': 'get_comment',
                        'response': {
                            200: {'type': 'Comment'}
                        }
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Verify single path parameter
        assert "Future<Post> getPost(String postId)" in code
        assert "_dio.get('/posts/$postId')" in code

        # Verify multiple path parameters
        assert "Future<Comment> getComment(String postId, String commentId)" in code
        assert "_dio.get('/posts/$postId/comments/$commentId')" in code

    def test_multiple_endpoints_same_path_different_methods(self):
        """Test that multiple HTTP methods on same path all generate correctly."""
        schema = SchnitzelSchema(
            models={
                'Resource': Model(
                    name='Resource',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string')
                    }
                )
            },
            endpoints={
                '/resources/{id}': {
                    'params': {
                        'id': {'type': 'uuid'}
                    },
                    'GET': {
                        'name': 'get_resource',
                        'response': {200: {'type': 'Resource'}}
                    },
                    'PUT': {
                        'name': 'update_resource',
                        'body': 'Resource',
                        'response': {200: {'type': 'Resource'}}
                    },
                    'DELETE': {
                        'name': 'delete_resource',
                        'response': {204: {'type': 'void'}}
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # All three methods should be present
        assert 'Future<Resource> getResource(String id)' in code
        assert 'Future<Resource> updateResource(' in code
        assert 'Future<void> deleteResource(String id)' in code

        # Verify correct HTTP verbs
        method_count_get = code.count("_dio.get('/resources/$id')")
        method_count_put = code.count("_dio.put('/resources/$id'")
        method_count_delete = code.count("_dio.delete('/resources/$id')")

        assert method_count_get == 1, "Should have exactly one GET call"
        assert method_count_put == 1, "Should have exactly one PUT call"
        assert method_count_delete == 1, "Should have exactly one DELETE call"

    def test_endpoint_iteration_preserves_all_endpoints(self):
        """Test that all endpoints in schema are generated, none are skipped."""
        schema = SchnitzelSchema(
            models={
                'User': Model(name='User', fields={'id': FieldDefinition(type='uuid', primary=True)}),
                'Post': Model(name='Post', fields={'id': FieldDefinition(type='uuid', primary=True)}),
                'Comment': Model(name='Comment', fields={'id': FieldDefinition(type='uuid', primary=True)}),
                'Tag': Model(name='Tag', fields={'id': FieldDefinition(type='uuid', primary=True)}),
            },
            endpoints={
                '/users': {
                    'GET': {
                        'name': 'list_users',
                        'response': {200: {'type': 'List[User]'}}
                    }
                },
                '/users/{id}': {
                    'params': {'id': {'type': 'uuid'}},
                    'GET': {
                        'name': 'get_user',
                        'response': {200: {'type': 'User'}}
                    }
                },
                '/posts': {
                    'GET': {
                        'name': 'list_posts',
                        'response': {200: {'type': 'List[Post]'}}
                    }
                },
                '/posts/{id}': {
                    'params': {'id': {'type': 'uuid'}},
                    'GET': {
                        'name': 'get_post',
                        'response': {200: {'type': 'Post'}}
                    }
                },
                '/comments': {
                    'GET': {
                        'name': 'list_comments',
                        'response': {200: {'type': 'List[Comment]'}}
                    }
                },
                '/tags': {
                    'GET': {
                        'name': 'list_tags',
                        'response': {200: {'type': 'List[Tag]'}}
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Verify all 6 methods are generated
        assert 'Future<List<User>> listUsers()' in code
        assert 'Future<User> getUser(String id)' in code
        assert 'Future<List<Post>> listPosts()' in code
        assert 'Future<Post> getPost(String id)' in code
        assert 'Future<List<Comment>> listComments()' in code
        assert 'Future<List<Tag>> listTags()' in code

        # Count the number of Future methods (should be 6)
        future_count = code.count('Future<')
        assert future_count == 6, f"Expected 6 Future methods, found {future_count}"

    def test_endpoint_order_independence(self):
        """Test that endpoint generation works regardless of definition order."""
        schema = SchnitzelSchema(
            models={
                'Item': Model(
                    name='Item',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                )
            },
            endpoints={
                '/items/{id}': {
                    'params': {'id': {'type': 'uuid'}},
                    'DELETE': {
                        'name': 'delete_item',
                        'response': {204: {'type': 'void'}}
                    },
                    'GET': {
                        'name': 'get_item',
                        'response': {200: {'type': 'Item'}}
                    },
                    'PUT': {
                        'name': 'update_item',
                        'body': 'Item',
                        'response': {200: {'type': 'Item'}}
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # All methods should be generated regardless of order
        assert 'Future<void> deleteItem(String id)' in code
        assert 'Future<Item> getItem(String id)' in code
        assert 'Future<Item> updateItem(' in code

    def test_complex_path_parameters(self):
        """Test handling of complex paths with multiple parameters."""
        schema = SchnitzelSchema(
            models={
                'Comment': Model(
                    name='Comment',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'text': FieldDefinition(type='string')
                    }
                )
            },
            endpoints={
                '/users/{userId}/posts/{postId}/comments/{commentId}': {
                    'params': {
                        'userId': {'type': 'uuid'},
                        'postId': {'type': 'uuid'},
                        'commentId': {'type': 'uuid'}
                    },
                    'GET': {
                        'name': 'get_user_post_comment',
                        'response': {200: {'type': 'Comment'}}
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Verify method signature has all parameters
        assert 'Future<Comment> getUserPostComment(String userId, String postId, String commentId)' in code

        # Verify path interpolation
        assert "_dio.get('/users/$userId/posts/$postId/comments/$commentId')" in code

    def test_empty_endpoints_dict(self):
        """Test that generator handles empty endpoints dict gracefully."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                )
            },
            endpoints={}
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should still have class structure
        assert 'class ApiClient {' in code
        assert 'final Dio _dio;' in code
        assert 'ApiClient(this._dio);' in code

        # But no methods
        assert 'Future<' not in code

    def test_none_endpoints(self):
        """Test that generator handles None endpoints gracefully."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                )
            },
            endpoints=None
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should still have class structure
        assert 'class ApiClient {' in code
        assert 'final Dio _dio;' in code

    def test_mixed_endpoints_with_and_without_params(self):
        """Test endpoints with and without path parameters work correctly."""
        schema = SchnitzelSchema(
            models={
                'Product': Model(
                    name='Product',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string')
                    }
                )
            },
            endpoints={
                '/products': {
                    'GET': {
                        'name': 'list_products',
                        'response': {200: {'type': 'List[Product]'}}
                    },
                    'POST': {
                        'name': 'create_product',
                        'body': 'Product',
                        'response': {201: {'type': 'Product'}}
                    }
                },
                '/products/{id}': {
                    'params': {'id': {'type': 'uuid'}},
                    'GET': {
                        'name': 'get_product',
                        'response': {200: {'type': 'Product'}}
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Methods without params should have empty or body-only signatures
        assert 'Future<List<Product>> listProducts()' in code
        assert 'Future<Product> createProduct(' in code

        # Methods with params should include them
        assert 'Future<Product> getProduct(String id)' in code

        # Verify correct paths
        assert "_dio.get('/products')" in code
        assert "_dio.post('/products'" in code
        assert "_dio.get('/products/$id')" in code

    def test_post_put_with_body_parameter(self):
        """Test that POST and PUT methods correctly include body parameter."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string')
                    }
                ),
                'CreateUserRequest': Model(
                    name='CreateUserRequest',
                    fields={'name': FieldDefinition(type='string')}
                )
            },
            endpoints={
                '/users': {
                    'POST': {
                        'name': 'create_user',
                        'body': 'CreateUserRequest',
                        'response': {201: {'type': 'User'}}
                    }
                },
                '/users/{id}': {
                    'params': {'id': {'type': 'uuid'}},
                    'PUT': {
                        'name': 'update_user',
                        'body': 'User',
                        'response': {200: {'type': 'User'}}
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # POST should have body parameter
        assert 'Future<User> createUser(' in code
        assert 'CreateUserRequest body' in code or 'required CreateUserRequest body' in code
        assert "data: body.toJson()" in code

        # PUT should have both id and body parameters
        assert 'Future<User> updateUser(String id' in code
        assert 'User body' in code or 'required User body' in code

    def test_generate_to_file_with_endpoints(self):
        """Test that generate_to_file creates proper file with all endpoints."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                )
            },
            endpoints={
                '/users': {
                    'GET': {
                        'name': 'list_users',
                        'response': {200: {'type': 'List[User]'}}
                    }
                },
                '/users/{id}': {
                    'params': {'id': {'type': 'uuid'}},
                    'GET': {
                        'name': 'get_user',
                        'response': {200: {'type': 'User'}}
                    }
                }
            }
        )

        generator = DartApiClientGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "generated"
            api_client_file, size = generator.generate_to_file(schema, output_dir)

            # Verify file was created
            assert api_client_file.exists()
            assert api_client_file.name == "api_client.dart"
            assert size > 0

            # Read and verify content
            content = api_client_file.read_text()

            # Verify both endpoints are in the file
            assert 'Future<List<User>> listUsers()' in content
            assert 'Future<User> getUser(String id)' in content

            # Verify header comments
            assert 'Generated by Schnitzel Framework' in content
            assert 'DO NOT EDIT' in content

    def test_endpoint_descriptions_preserved(self):
        """Test that endpoint descriptions are included as doc comments."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                )
            },
            endpoints={
                '/users/{id}': {
                    'params': {'id': {'type': 'uuid'}},
                    'GET': {
                        'name': 'get_user',
                        'description': 'Retrieve a single user by their unique identifier',
                        'response': {200: {'type': 'User'}}
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Verify description is included as doc comment
        assert '/// Retrieve a single user by their unique identifier' in code

    def test_large_schema_with_many_endpoints(self):
        """Test that generator handles schemas with many endpoints correctly."""
        # Create a schema with 10 different endpoints
        models = {
            'User': Model(name='User', fields={'id': FieldDefinition(type='uuid', primary=True)}),
            'Post': Model(name='Post', fields={'id': FieldDefinition(type='uuid', primary=True)}),
            'Comment': Model(name='Comment', fields={'id': FieldDefinition(type='uuid', primary=True)}),
        }

        endpoints = {}
        expected_methods = []

        # Create multiple endpoints for each resource
        for resource in ['users', 'posts', 'comments']:
            model_name = resource.capitalize()[:-1]  # users -> User

            endpoints[f'/{resource}'] = {
                'GET': {
                    'name': f'list_{resource}',
                    'response': {200: {'type': f'List[{model_name}]'}}
                },
                'POST': {
                    'name': f'create_{resource[:-1]}',
                    'body': model_name,
                    'response': {201: {'type': model_name}}
                }
            }
            expected_methods.append(f'list{model_name}s')
            expected_methods.append(f'create{model_name}')

            endpoints[f'/{resource}/{{id}}'] = {
                'params': {'id': {'type': 'uuid'}},
                'GET': {
                    'name': f'get_{resource[:-1]}',
                    'response': {200: {'type': model_name}}
                },
                'DELETE': {
                    'name': f'delete_{resource[:-1]}',
                    'response': {204: {'type': 'void'}}
                }
            }
            expected_methods.append(f'get{model_name}')
            expected_methods.append(f'delete{model_name}')

        schema = SchnitzelSchema(models=models, endpoints=endpoints)

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Verify all 12 methods are present
        future_count = code.count('Future<')
        assert future_count == 12, f"Expected 12 Future methods, found {future_count}"

        # Verify each expected method name appears
        for method in expected_methods:
            assert method in code, f"Expected method {method} not found in generated code"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
