"""Integration test for API_070: SQLAlchemy ORM generator handles self-referential relationships.

Test Requirements:
1. Verify ORM generator handles self-referential relationships (belongsTo where model references itself)
2. Verify generated code includes foreign key to same table
3. Verify generated code includes relationship() with remote_side parameter
4. Test database operations with self-referential relationships (e.g., Employee with manager)

Example: Employee model where an Employee can have a manager (who is also an Employee)
- Employee.manager_id -> Foreign key to employees.id
- Employee.manager -> relationship(remote_side=[id]) for belongsTo side
- Employee.subordinates -> relationship() for hasMany side

This test uses an in-memory SQLite database for testing.
"""

import pytest
import sys
from pathlib import Path
from sqlalchemy import create_engine, select, inspect
from sqlalchemy.orm import Session

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


def load_generated_module(code: str, module_name: str = "test_orm"):
    """Helper function to load generated ORM code as a Python module.

    Args:
        code: The generated Python code
        module_name: Name for the module (must be unique per test)

    Returns:
        The loaded module
    """
    import importlib.util

    # Create module spec
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    module = importlib.util.module_from_spec(spec)

    # Register the module in sys.modules BEFORE executing code
    # This is necessary for SQLAlchemy to resolve type annotations
    sys.modules[module_name] = module

    try:
        # Execute the code in the module's namespace
        exec(code, module.__dict__)
        return module
    except Exception:
        # Clean up on failure
        if module_name in sys.modules:
            del sys.modules[module_name]
        raise


class TestORMSelfReferentialRelationship:
    """Test SQLAlchemy ORM generator self-referential relationship support (API_070)."""

    def test_self_referential_foreign_key(self):
        """Test that self-referential belongsTo generates foreign key to same table."""
        schema = SchnitzelSchema(
            models={
                'Employee': Model(
                    name='Employee',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True),
                        'position': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'manager': Relation(type='belongsTo', model='Employee'),
                        'subordinates': Relation(type='hasMany', model='Employee')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify foreign key points to same table (employees.id)
        assert 'manager_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID, sa.ForeignKey("employees.id")' in code

    def test_self_referential_relationship_remote_side(self):
        """Test that self-referential relationship includes remote_side parameter."""
        schema = SchnitzelSchema(
            models={
                'Employee': Model(
                    name='Employee',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'manager': Relation(type='belongsTo', model='Employee'),
                        'subordinates': Relation(type='hasMany', model='Employee')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify belongsTo relationship includes remote_side parameter
        # remote_side should point to the id column of the remote (parent) object
        assert 'manager: Mapped["Employee | None"] = relationship(' in code
        assert 'remote_side="id"' in code or 'remote_side=[id]' in code

        # Verify hasMany relationship (reverse side)
        assert 'subordinates: Mapped[list["Employee"]] = relationship(' in code

    def test_self_referential_back_populates(self):
        """Test that self-referential relationships have correct back_populates."""
        schema = SchnitzelSchema(
            models={
                'Employee': Model(
                    name='Employee',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'manager': Relation(type='belongsTo', model='Employee'),
                        'subordinates': Relation(type='hasMany', model='Employee')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify back_populates references
        assert 'back_populates="subordinates"' in code  # manager -> subordinates
        assert 'back_populates="manager"' in code  # subordinates -> manager

    def test_self_referential_database_creation(self):
        """Test that self-referential relationships create proper database schema."""
        schema = SchnitzelSchema(
            models={
                'Employee': Model(
                    name='Employee',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'name': FieldDefinition(type='string', required=True),
                        'position': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'manager': Relation(type='belongsTo', model='Employee'),
                        'subordinates': Relation(type='hasMany', model='Employee')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_self_ref_db")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")

        # Create all tables
        orm_models.Base.metadata.create_all(engine)

        # Verify table was created
        inspector = inspect(engine)
        assert 'employees' in inspector.get_table_names()

        # Verify foreign key constraint exists and points to same table
        fk_constraints = inspector.get_foreign_keys('employees')
        assert len(fk_constraints) >= 1

        # Find the manager_id foreign key
        manager_fk = next(
            (fk for fk in fk_constraints if 'manager_id' in fk['constrained_columns']),
            None
        )
        assert manager_fk is not None
        assert manager_fk['referred_table'] == 'employees'
        assert 'id' in manager_fk['referred_columns']

    def test_self_referential_crud_operations(self):
        """Test CRUD operations with self-referential relationships."""
        schema = SchnitzelSchema(
            models={
                'Employee': Model(
                    name='Employee',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'name': FieldDefinition(type='string', required=True),
                        'position': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'manager': Relation(type='belongsTo', model='Employee'),
                        'subordinates': Relation(type='hasMany', model='Employee')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_self_ref_crud")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Test CRUD operations with hierarchical data
        with Session(engine) as session:
            # CREATE - Build organizational hierarchy
            ceo = orm_models.Employee(
                id=1,
                name="Alice Johnson",
                position="CEO"
            )
            cto = orm_models.Employee(
                id=2,
                name="Bob Smith",
                position="CTO",
                manager=ceo  # Bob reports to Alice
            )
            engineer1 = orm_models.Employee(
                id=3,
                name="Charlie Davis",
                position="Senior Engineer",
                manager=cto  # Charlie reports to Bob
            )
            engineer2 = orm_models.Employee(
                id=4,
                name="Diana Martinez",
                position="Engineer",
                manager=cto  # Diana reports to Bob
            )

            session.add_all([ceo, cto, engineer1, engineer2])
            session.commit()

            # READ - Query employee and their manager
            stmt = select(orm_models.Employee).where(orm_models.Employee.id == 2)
            bob = session.execute(stmt).scalar_one()
            assert bob.name == "Bob Smith"
            assert bob.manager is not None
            assert bob.manager.name == "Alice Johnson"
            assert bob.manager.position == "CEO"

            # READ - Query manager's subordinates
            stmt = select(orm_models.Employee).where(orm_models.Employee.id == 1)
            alice = session.execute(stmt).scalar_one()
            assert len(alice.subordinates) == 1
            assert alice.subordinates[0].name == "Bob Smith"

            # Query CTO's subordinates
            stmt = select(orm_models.Employee).where(orm_models.Employee.id == 2)
            bob = session.execute(stmt).scalar_one()
            assert len(bob.subordinates) == 2
            subordinate_names = {emp.name for emp in bob.subordinates}
            assert "Charlie Davis" in subordinate_names
            assert "Diana Martinez" in subordinate_names

            # UPDATE - Promote engineer to manager role
            stmt = select(orm_models.Employee).where(orm_models.Employee.id == 3)
            charlie = session.execute(stmt).scalar_one()
            charlie.position = "Engineering Manager"
            charlie.manager = ceo  # Charlie now reports directly to CEO
            session.commit()

            # Verify update
            session.refresh(charlie)
            assert charlie.position == "Engineering Manager"
            assert charlie.manager.name == "Alice Johnson"

            # Verify Bob's subordinates list updated
            session.refresh(bob)
            assert len(bob.subordinates) == 1  # Only Diana now
            assert bob.subordinates[0].name == "Diana Martinez"

            # Verify Alice's subordinates list updated
            session.refresh(alice)
            assert len(alice.subordinates) == 2  # Bob and Charlie
            subordinate_names = {emp.name for emp in alice.subordinates}
            assert "Bob Smith" in subordinate_names
            assert "Charlie Davis" in subordinate_names

            # DELETE - Remove employee
            session.delete(engineer2)
            session.commit()

            # Verify deletion
            stmt = select(orm_models.Employee).where(orm_models.Employee.id == 4)
            result = session.execute(stmt).one_or_none()
            assert result is None

            # Verify remaining employees
            stmt = select(orm_models.Employee)
            remaining = session.execute(stmt).scalars().all()
            assert len(remaining) == 3

    def test_self_referential_null_manager(self):
        """Test that self-referential relationship allows null (top-level employees)."""
        schema = SchnitzelSchema(
            models={
                'Employee': Model(
                    name='Employee',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'manager': Relation(type='belongsTo', model='Employee'),
                        'subordinates': Relation(type='hasMany', model='Employee')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load and test
        orm_models = load_generated_module(code, "test_orm_self_ref_null")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        with Session(engine) as session:
            # Create CEO with no manager (manager_id is NULL)
            ceo = orm_models.Employee(
                id=1,
                name="CEO",
                manager=None
            )
            session.add(ceo)
            session.commit()

            # Verify CEO has no manager
            stmt = select(orm_models.Employee).where(orm_models.Employee.id == 1)
            ceo_retrieved = session.execute(stmt).scalar_one()
            assert ceo_retrieved.manager is None
            assert ceo_retrieved.subordinates == []

    def test_self_referential_multiple_levels(self):
        """Test self-referential relationships work across multiple hierarchy levels."""
        schema = SchnitzelSchema(
            models={
                'Category': Model(
                    name='Category',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'parent': Relation(type='belongsTo', model='Category'),
                        'children': Relation(type='hasMany', model='Category')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load and test
        orm_models = load_generated_module(code, "test_orm_self_ref_levels")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        with Session(engine) as session:
            # Build multi-level category tree
            # Electronics
            #   -> Computers
            #      -> Laptops
            #      -> Desktops
            #   -> Phones
            electronics = orm_models.Category(id=1, name="Electronics")
            computers = orm_models.Category(id=2, name="Computers", parent=electronics)
            laptops = orm_models.Category(id=3, name="Laptops", parent=computers)
            desktops = orm_models.Category(id=4, name="Desktops", parent=computers)
            phones = orm_models.Category(id=5, name="Phones", parent=electronics)

            session.add_all([electronics, computers, laptops, desktops, phones])
            session.commit()

            # Verify top-level category
            stmt = select(orm_models.Category).where(orm_models.Category.id == 1)
            elec = session.execute(stmt).scalar_one()
            assert elec.parent is None
            assert len(elec.children) == 2
            child_names = {cat.name for cat in elec.children}
            assert "Computers" in child_names
            assert "Phones" in child_names

            # Verify mid-level category
            stmt = select(orm_models.Category).where(orm_models.Category.id == 2)
            comp = session.execute(stmt).scalar_one()
            assert comp.parent.name == "Electronics"
            assert len(comp.children) == 2
            child_names = {cat.name for cat in comp.children}
            assert "Laptops" in child_names
            assert "Desktops" in child_names

            # Verify leaf-level category
            stmt = select(orm_models.Category).where(orm_models.Category.id == 3)
            lap = session.execute(stmt).scalar_one()
            assert lap.parent.name == "Computers"
            assert len(lap.children) == 0

    def test_self_referential_custom_foreign_key(self):
        """Test self-referential relationship with custom foreign key name."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'username': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'referrer': Relation(
                            type='belongsTo',
                            model='User',
                            foreign_key='referred_by_id'
                        ),
                        'referrals': Relation(type='hasMany', model='User')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify custom foreign key name is used
        assert 'referred_by_id: Mapped[uuid.UUID | None] = mapped_column' in code
        assert 'sa.ForeignKey("users.id")' in code

    def test_self_referential_no_warnings_errors(self):
        """Test that generated self-referential ORM code has no errors or warnings."""
        schema = SchnitzelSchema(
            models={
                'Employee': Model(
                    name='Employee',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'manager': Relation(type='belongsTo', model='Employee'),
                        'subordinates': Relation(type='hasMany', model='Employee')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load the module - should not raise any errors
        orm_models = load_generated_module(code, "test_orm_self_ref_no_errors")

        # Create database - should work without warnings
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Verify the model is properly configured
        assert hasattr(orm_models, 'Employee')
        assert hasattr(orm_models.Employee, 'manager')
        assert hasattr(orm_models.Employee, 'subordinates')
        assert hasattr(orm_models.Employee, 'manager_id')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
