"""Integration test for F079: Python generator handles models with many-to-many relationships.

Many-to-many relationships in Schnitzel schemas can be implemented using:
1. Junction table pattern: intermediate model with belongsTo to both models
2. Bidirectional hasMany: both models have hasMany to each other (less common)

This test verifies that the Python generator correctly handles junction tables
for many-to-many relationships.

Test Steps:
1. Create Student and Course models with a StudentCourse junction table
2. Junction table has belongsTo relationships to both Student and Course
3. Student and Course both have hasMany relationships to StudentCourse
4. Generate Python models and verify all relationships are correct
5. Test that both sides generate appropriate list fields via junction
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.models import PythonModelGenerator


def test_many_to_many_generates():
    """Test that many-to-many via junction table generates correct models.

    Pattern: Student <-> StudentCourse <-> Course
    - StudentCourse has belongsTo: student and belongsTo: course
    - Student has hasMany: enrollments (StudentCourse)
    - Course has hasMany: enrollments (StudentCourse)
    """
    schema = SchnitzelSchema(
        models={
            "Student": Model(
                name="Student",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
                },
                relations={
                    "enrollments": Relation(
                        type="hasMany",
                        model="StudentCourse"
                    )
                }
            ),
            "Course": Model(
                name="Course",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                    "credits": FieldDefinition(type="int"),
                },
                relations={
                    "enrollments": Relation(
                        type="hasMany",
                        model="StudentCourse"
                    )
                }
            ),
            "StudentCourse": Model(
                name="StudentCourse",
                description="Junction table for many-to-many relationship between Student and Course",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "student_id": FieldDefinition(type="uuid"),
                    "course_id": FieldDefinition(type="uuid"),
                    "enrolled_at": FieldDefinition(type="datetime"),
                    "grade": FieldDefinition(type="string", optional=True),
                },
                relations={
                    "student": Relation(
                        type="belongsTo",
                        model="Student",
                        foreign_key="student_id"
                    ),
                    "course": Relation(
                        type="belongsTo",
                        model="Course",
                        foreign_key="course_id"
                    )
                }
            )
        }
    )

    # Generate Python code
    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Python code for many-to-many:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify Student model
    assert "class Student(BaseModel):" in generated_code, \
        "Student model should be generated"
    assert 'enrollments: list[StudentCourse] = []' in generated_code, \
        "Student should have enrollments list field"

    # Verify Course model
    assert "class Course(BaseModel):" in generated_code, \
        "Course model should be generated"
    assert 'enrollments: list[StudentCourse] = []' in generated_code or \
           generated_code.count('enrollments: list[StudentCourse] = []') >= 2, \
        "Course should have enrollments list field"

    # Verify StudentCourse junction table
    assert "class StudentCourse(BaseModel):" in generated_code, \
        "StudentCourse junction table should be generated"
    assert 'student: Student | None = None' in generated_code, \
        "StudentCourse should have belongsTo student relationship"
    assert 'course: Course | None = None' in generated_code, \
        "StudentCourse should have belongsTo course relationship"

    # Verify the code is valid Python
    try:
        compile(generated_code, "<string>", "exec")
        print("\n✓ Generated code is valid Python!")
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax error: {e}")


def test_both_sides_have_list():
    """Test that both sides of many-to-many have list fields via junction."""
    schema = SchnitzelSchema(
        models={
            "Author": Model(
                name="Author",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "book_authors": Relation(
                        type="hasMany",
                        model="BookAuthor"
                    )
                }
            ),
            "Book": Model(
                name="Book",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                },
                relations={
                    "book_authors": Relation(
                        type="hasMany",
                        model="BookAuthor"
                    )
                }
            ),
            "BookAuthor": Model(
                name="BookAuthor",
                description="Junction table for many-to-many between Book and Author",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "book_id": FieldDefinition(type="uuid"),
                    "author_id": FieldDefinition(type="uuid"),
                    "author_order": FieldDefinition(type="int"),  # Co-authors can be ordered
                },
                relations={
                    "book": Relation(
                        type="belongsTo",
                        model="Book",
                        foreign_key="book_id"
                    ),
                    "author": Relation(
                        type="belongsTo",
                        model="Author",
                        foreign_key="author_id"
                    )
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated code for Book-Author many-to-many:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Both Author and Book should have list fields pointing to junction
    assert 'book_authors: list[BookAuthor] = []' in generated_code, \
        "Both models should have list fields via junction table"

    # Verify we have both models with the list field (should appear twice in code)
    list_field_count = generated_code.count('book_authors: list[BookAuthor] = []')
    assert list_field_count >= 2, \
        f"Expected 2 occurrences of 'book_authors: list[BookAuthor] = []', found {list_field_count}"

    # Junction table should have belongsTo to both sides
    assert 'book: Book | None = None' in generated_code, \
        "Junction should have belongsTo book"
    assert 'author: Author | None = None' in generated_code, \
        "Junction should have belongsTo author"


def test_many_to_many_with_extra_fields():
    """Test junction table with additional fields beyond the foreign keys.

    Many-to-many junction tables often store extra information about the relationship,
    like enrollment date, status, permissions, etc.
    """
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "username": FieldDefinition(type="string"),
                },
                relations={
                    "memberships": Relation(
                        type="hasMany",
                        model="TeamMember"
                    )
                }
            ),
            "Team": Model(
                name="Team",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "members": Relation(
                        type="hasMany",
                        model="TeamMember"
                    )
                }
            ),
            "TeamMember": Model(
                name="TeamMember",
                description="Junction table with extra fields for team membership",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "user_id": FieldDefinition(type="uuid"),
                    "team_id": FieldDefinition(type="uuid"),
                    "role": FieldDefinition(type="string"),  # admin, member, viewer
                    "joined_at": FieldDefinition(type="datetime"),
                    "is_active": FieldDefinition(type="bool", default=True),
                },
                relations={
                    "user": Relation(
                        type="belongsTo",
                        model="User",
                        foreign_key="user_id"
                    ),
                    "team": Relation(
                        type="belongsTo",
                        model="Team",
                        foreign_key="team_id"
                    )
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated code for many-to-many with extra fields:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify junction table has all fields including extra ones
    assert "class TeamMember(BaseModel):" in generated_code
    assert "role: str" in generated_code, \
        "Junction table should have extra field 'role'"
    assert "joined_at: datetime" in generated_code, \
        "Junction table should have extra field 'joined_at'"
    assert "is_active: bool = True" in generated_code, \
        "Junction table should have extra field 'is_active' with default"

    # Verify relationships work correctly
    assert 'memberships: list[TeamMember] = []' in generated_code, \
        "User should have memberships list"
    assert 'members: list[TeamMember] = []' in generated_code, \
        "Team should have members list"

    # Verify imports for datetime
    assert "from datetime import datetime" in generated_code, \
        "Should import datetime for junction table fields"


def test_complex_many_to_many_scenario():
    """Test a complex scenario with multiple many-to-many relationships.

    Scenario: A project management system where:
    - Projects have many Users (via ProjectMember)
    - Projects have many Tags (via ProjectTag)
    - Users have many Teams (via TeamMember) - separate from projects
    """
    schema = SchnitzelSchema(
        models={
            "Project": Model(
                name="Project",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "members": Relation(type="hasMany", model="ProjectMember"),
                    "tags": Relation(type="hasMany", model="ProjectTag"),
                }
            ),
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string"),
                },
                relations={
                    "project_memberships": Relation(type="hasMany", model="ProjectMember"),
                    "team_memberships": Relation(type="hasMany", model="TeamMember"),
                }
            ),
            "Tag": Model(
                name="Tag",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "label": FieldDefinition(type="string"),
                },
                relations={
                    "project_tags": Relation(type="hasMany", model="ProjectTag"),
                }
            ),
            "Team": Model(
                name="Team",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "members": Relation(type="hasMany", model="TeamMember"),
                }
            ),
            "ProjectMember": Model(
                name="ProjectMember",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "project_id": FieldDefinition(type="uuid"),
                    "user_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "project": Relation(type="belongsTo", model="Project", foreign_key="project_id"),
                    "user": Relation(type="belongsTo", model="User", foreign_key="user_id"),
                }
            ),
            "ProjectTag": Model(
                name="ProjectTag",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "project_id": FieldDefinition(type="uuid"),
                    "tag_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "project": Relation(type="belongsTo", model="Project", foreign_key="project_id"),
                    "tag": Relation(type="belongsTo", model="Tag", foreign_key="tag_id"),
                }
            ),
            "TeamMember": Model(
                name="TeamMember",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "team_id": FieldDefinition(type="uuid"),
                    "user_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "team": Relation(type="belongsTo", model="Team", foreign_key="team_id"),
                    "user": Relation(type="belongsTo", model="User", foreign_key="user_id"),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated code for complex many-to-many scenario:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify all models are generated
    assert "class Project(BaseModel):" in generated_code
    assert "class User(BaseModel):" in generated_code
    assert "class Tag(BaseModel):" in generated_code
    assert "class Team(BaseModel):" in generated_code
    assert "class ProjectMember(BaseModel):" in generated_code
    assert "class ProjectTag(BaseModel):" in generated_code
    assert "class TeamMember(BaseModel):" in generated_code

    # Verify Project has multiple hasMany relationships
    assert 'members: list[ProjectMember] = []' in generated_code
    assert 'tags: list[ProjectTag] = []' in generated_code

    # Verify User has multiple hasMany relationships
    assert 'project_memberships: list[ProjectMember] = []' in generated_code
    assert 'team_memberships: list[TeamMember] = []' in generated_code

    # Verify all junction tables have belongsTo relationships
    assert 'project: Project | None = None' in generated_code
    assert 'user: User | None = None' in generated_code
    assert 'tag: Tag | None = None' in generated_code
    assert 'team: Team | None = None' in generated_code

    # Verify the code is valid Python
    try:
        compile(generated_code, "<string>", "exec")
        print("\n✓ Complex many-to-many generated code is valid Python!")
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax error: {e}")


def test_self_referential_many_to_many():
    """Test many-to-many relationship where a model relates to itself.

    Example: User can follow other Users (follower/following relationship).
    This requires a junction table that references the same model twice.
    """
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "username": FieldDefinition(type="string"),
                },
                relations={
                    "following": Relation(type="hasMany", model="UserFollow"),
                    "followers": Relation(type="hasMany", model="UserFollow"),
                }
            ),
            "UserFollow": Model(
                name="UserFollow",
                description="Self-referential junction table for follower/following",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "follower_id": FieldDefinition(type="uuid"),
                    "following_id": FieldDefinition(type="uuid"),
                    "followed_at": FieldDefinition(type="datetime"),
                },
                relations={
                    "follower": Relation(type="belongsTo", model="User", foreign_key="follower_id"),
                    "following_user": Relation(type="belongsTo", model="User", foreign_key="following_id"),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated code for self-referential many-to-many:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify User has both relationship lists
    assert 'following: list[UserFollow] = []' in generated_code, \
        "User should have following list"
    assert 'followers: list[UserFollow] = []' in generated_code, \
        "User should have followers list"

    # Verify UserFollow has both belongsTo relationships to User
    assert 'follower: User | None = None' in generated_code, \
        "UserFollow should have follower relationship"
    assert 'following_user: User | None = None' in generated_code, \
        "UserFollow should have following_user relationship"

    # Verify the code compiles
    try:
        compile(generated_code, "<string>", "exec")
        print("\n✓ Self-referential many-to-many generated code is valid Python!")
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax error: {e}")


if __name__ == "__main__":
    # Run tests manually for development
    test_many_to_many_generates()
    test_both_sides_have_list()
    test_many_to_many_with_extra_fields()
    test_complex_many_to_many_scenario()
    test_self_referential_many_to_many()

    print("\n" + "=" * 80)
    print("✓ All F079 many-to-many tests passed!")
    print("=" * 80)
