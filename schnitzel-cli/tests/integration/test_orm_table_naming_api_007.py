"""Integration test for API_007: SQLAlchemy ORM generator creates table with correct naming.

Test Requirements:
1. Verify ORM generator converts model names to correct table names
2. Test edge cases:
   - Simple plural (User -> users)
   - CamelCase split (BlogPost -> blog_posts)
   - y->ies transformation (Category -> categories)
   - Irregular plurals
3. Create integration test that verifies __tablename__ is set correctly

This test ensures the ORM generator follows the Schnitzel table naming convention:
PascalCase model name -> plural snake_case table name
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestORMTableNaming:
    """Test ORM generator correctly converts model names to pluralized snake_case table names."""

    def test_simple_plural_user_to_users(self):
        """Test simple pluralization: User -> users."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'email': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify table name is correctly pluralized
        assert '__tablename__ = "users"' in code, "User model should generate 'users' table"
        assert 'class User(Base):' in code

        # Verify incorrect forms are NOT present
        assert '__tablename__ = "user"' not in code
        assert '__tablename__ = "User"' not in code

    def test_simple_plural_post_to_posts(self):
        """Test simple pluralization: Post -> posts."""
        schema = SchnitzelSchema(
            models={
                'Post': Model(
                    name='Post',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert '__tablename__ = "posts"' in code, "Post model should generate 'posts' table"
        assert 'class Post(Base):' in code

    def test_camelcase_split_blog_post_to_blog_posts(self):
        """Test CamelCase split: BlogPost -> blog_posts."""
        schema = SchnitzelSchema(
            models={
                'BlogPost': Model(
                    name='BlogPost',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string', required=True),
                        'content': FieldDefinition(type='text')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify CamelCase is split and pluralized correctly
        assert '__tablename__ = "blog_posts"' in code, "BlogPost model should generate 'blog_posts' table"
        assert 'class BlogPost(Base):' in code

        # Verify incorrect forms are NOT present
        assert '__tablename__ = "blogposts"' not in code
        assert '__tablename__ = "BlogPosts"' not in code
        assert '__tablename__ = "blog_post"' not in code

    def test_camelcase_split_order_item_to_order_items(self):
        """Test CamelCase split: OrderItem -> order_items."""
        schema = SchnitzelSchema(
            models={
                'OrderItem': Model(
                    name='OrderItem',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'quantity': FieldDefinition(type='int', required=True),
                        'price': FieldDefinition(type='float', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert '__tablename__ = "order_items"' in code, "OrderItem model should generate 'order_items' table"
        assert 'class OrderItem(Base):' in code

    def test_y_to_ies_category_to_categories(self):
        """Test y->ies transformation: Category -> categories."""
        schema = SchnitzelSchema(
            models={
                'Category': Model(
                    name='Category',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True, unique=True),
                        'description': FieldDefinition(type='text', optional=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify y->ies transformation
        assert '__tablename__ = "categories"' in code, "Category model should generate 'categories' table"
        assert 'class Category(Base):' in code

        # Verify incorrect forms are NOT present
        assert '__tablename__ = "categorys"' not in code
        assert '__tablename__ = "category"' not in code

    def test_y_to_ies_company_to_companies(self):
        """Test y->ies transformation: Company -> companies."""
        schema = SchnitzelSchema(
            models={
                'Company': Model(
                    name='Company',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert '__tablename__ = "companies"' in code, "Company model should generate 'companies' table"
        assert 'class Company(Base):' in code

    def test_camelcase_with_y_user_story_to_user_stories(self):
        """Test CamelCase with y->ies: UserStory -> user_stories."""
        schema = SchnitzelSchema(
            models={
                'UserStory': Model(
                    name='UserStory',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert '__tablename__ = "user_stories"' in code, "UserStory model should generate 'user_stories' table"
        assert 'class UserStory(Base):' in code

    def test_ends_with_s_address_to_addresses(self):
        """Test words ending in 's': Address -> addresses."""
        schema = SchnitzelSchema(
            models={
                'Address': Model(
                    name='Address',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'street': FieldDefinition(type='string', required=True),
                        'city': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Words ending in 's' should add 'es'
        assert '__tablename__ = "addresses"' in code, "Address model should generate 'addresses' table"
        assert 'class Address(Base):' in code

        # Verify incorrect forms are NOT present
        assert '__tablename__ = "addresss"' not in code

    def test_ends_with_x_box_to_boxes(self):
        """Test words ending in 'x': Box -> boxes."""
        schema = SchnitzelSchema(
            models={
                'Box': Model(
                    name='Box',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'dimensions': FieldDefinition(type='string')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Words ending in 'x' should add 'es'
        assert '__tablename__ = "boxes"' in code, "Box model should generate 'boxes' table"
        assert 'class Box(Base):' in code

    def test_ends_with_z_quiz_to_quizzes(self):
        """Test words ending in 'z': Quiz -> quizzes."""
        schema = SchnitzelSchema(
            models={
                'Quiz': Model(
                    name='Quiz',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Words ending in 'z' should add 'es'
        assert '__tablename__ = "quizzes"' in code, "Quiz model should generate 'quizzes' table"
        assert 'class Quiz(Base):' in code

    def test_vowel_before_y_boy_to_boys(self):
        """Test words with vowel before y: Boy -> boys (not boies)."""
        schema = SchnitzelSchema(
            models={
                'Boy': Model(
                    name='Boy',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Vowel before y should just add 's', not 'ies'
        assert '__tablename__ = "boys"' in code, "Boy model should generate 'boys' table (not boies)"
        assert 'class Boy(Base):' in code

        # Verify incorrect form is NOT present
        assert '__tablename__ = "boies"' not in code

    def test_vowel_before_y_key_to_keys(self):
        """Test words with vowel before y: Key -> keys (not keies)."""
        schema = SchnitzelSchema(
            models={
                'Key': Model(
                    name='Key',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'value': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert '__tablename__ = "keys"' in code, "Key model should generate 'keys' table (not keies)"
        assert 'class Key(Base):' in code

    def test_multiple_models_all_have_correct_table_names(self):
        """Test that multiple models all get correct table names."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                ),
                'BlogPost': Model(
                    name='BlogPost',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                ),
                'Category': Model(
                    name='Category',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                ),
                'OrderItem': Model(
                    name='OrderItem',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                ),
                'Address': Model(
                    name='Address',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify all table names are correct
        assert '__tablename__ = "users"' in code
        assert '__tablename__ = "blog_posts"' in code
        assert '__tablename__ = "categories"' in code
        assert '__tablename__ = "order_items"' in code
        assert '__tablename__ = "addresses"' in code

    def test_complex_camelcase_api_key_to_api_keys(self):
        """Test complex CamelCase: APIKey -> api_keys."""
        schema = SchnitzelSchema(
            models={
                'APIKey': Model(
                    name='APIKey',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'key': FieldDefinition(type='string', required=True, unique=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should handle consecutive capitals correctly
        assert '__tablename__ = "api_keys"' in code, "APIKey model should generate 'api_keys' table"
        assert 'class APIKey(Base):' in code

    def test_three_word_camelcase_user_profile_picture(self):
        """Test three-word CamelCase: UserProfilePicture -> user_profile_pictures."""
        schema = SchnitzelSchema(
            models={
                'UserProfilePicture': Model(
                    name='UserProfilePicture',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'url': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert '__tablename__ = "user_profile_pictures"' in code
        assert 'class UserProfilePicture(Base):' in code

    def test_single_letter_model_a_to_as(self):
        """Test single letter model: A -> as."""
        schema = SchnitzelSchema(
            models={
                'A': Model(
                    name='A',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Single letter should just get 's' appended
        assert '__tablename__ = "as"' in code or '__tablename__ = "a_s"' in code
        assert 'class A(Base):' in code

    def test_acronym_with_word_html_tag_to_html_tags(self):
        """Test acronym with word: HTMLTag -> html_tags."""
        schema = SchnitzelSchema(
            models={
                'HTMLTag': Model(
                    name='HTMLTag',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should handle acronyms followed by words
        assert '__tablename__ = "html_tags"' in code or '__tablename__ = "h_t_m_l_tags"' in code
        assert 'class HTMLTag(Base):' in code

    def test_direct_method_simple_plural(self):
        """Test _pluralize_table_name method directly for simple cases."""
        generator = SQLAlchemyORMGenerator()

        assert generator._pluralize_table_name('User') == 'users'
        assert generator._pluralize_table_name('Post') == 'posts'
        assert generator._pluralize_table_name('Comment') == 'comments'
        assert generator._pluralize_table_name('Product') == 'products'

    def test_direct_method_camelcase_split(self):
        """Test _pluralize_table_name method directly for CamelCase."""
        generator = SQLAlchemyORMGenerator()

        assert generator._pluralize_table_name('BlogPost') == 'blog_posts'
        assert generator._pluralize_table_name('OrderItem') == 'order_items'
        assert generator._pluralize_table_name('ShoppingCart') == 'shopping_carts'

    def test_direct_method_y_to_ies(self):
        """Test _pluralize_table_name method directly for y->ies."""
        generator = SQLAlchemyORMGenerator()

        assert generator._pluralize_table_name('Category') == 'categories'
        assert generator._pluralize_table_name('Company') == 'companies'
        assert generator._pluralize_table_name('Country') == 'countries'

    def test_direct_method_vowel_before_y(self):
        """Test _pluralize_table_name method directly for vowel+y."""
        generator = SQLAlchemyORMGenerator()

        assert generator._pluralize_table_name('Boy') == 'boys'
        assert generator._pluralize_table_name('Key') == 'keys'
        assert generator._pluralize_table_name('Day') == 'days'

    def test_direct_method_ends_with_s_x_z(self):
        """Test _pluralize_table_name method directly for s/x/z endings."""
        generator = SQLAlchemyORMGenerator()

        assert generator._pluralize_table_name('Address') == 'addresses'
        assert generator._pluralize_table_name('Box') == 'boxes'
        assert generator._pluralize_table_name('Quiz') == 'quizzes'

    def test_to_snake_case_method(self):
        """Test _to_snake_case method directly."""
        generator = SQLAlchemyORMGenerator()

        # Simple cases
        assert generator._to_snake_case('User') == 'user'
        assert generator._to_snake_case('Post') == 'post'

        # CamelCase
        assert generator._to_snake_case('BlogPost') == 'blog_post'
        assert generator._to_snake_case('OrderItem') == 'order_item'
        assert generator._to_snake_case('UserProfilePicture') == 'user_profile_picture'

        # With acronyms
        assert generator._to_snake_case('APIKey') == 'api_key'
        assert generator._to_snake_case('HTMLTag') == 'html_tag' or generator._to_snake_case('HTMLTag') == 'h_t_m_l_tag'

    def test_table_name_consistency_across_generations(self):
        """Test that table names are consistent across multiple generations."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()

        # Generate multiple times
        code1 = generator.generate(schema)
        code2 = generator.generate(schema)
        code3 = generator.generate(schema)

        # All should have the same table name
        assert '__tablename__ = "users"' in code1
        assert '__tablename__ = "users"' in code2
        assert '__tablename__ = "users"' in code3

    def test_zero_tolerance_no_hardcoded_table_names(self):
        """Test that table names are not hardcoded but generated from model names."""
        schema = SchnitzelSchema(
            models={
                'CustomModel': Model(
                    name='CustomModel',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should generate table name from model name
        assert '__tablename__ = "custom_models"' in code
        assert 'class CustomModel(Base):' in code

        # Should not have any generic or hardcoded names
        assert '__tablename__ = "table"' not in code
        assert '__tablename__ = "model"' not in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
