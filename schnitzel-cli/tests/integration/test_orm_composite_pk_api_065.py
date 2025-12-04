"""Integration test for API_065: SQLAlchemy ORM generator handles composite primary keys.

Test Requirements:
1. Detect multiple fields with primary: true
2. Generate proper SQLAlchemy PrimaryKeyConstraint for composite keys
3. Verify generated code includes __table_args__ with PrimaryKeyConstraint
4. Test database table creation works with composite primary keys
5. Verify CRUD operations work correctly with composite primary keys

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


class TestORMCompositePrimaryKey:
    """Test SQLAlchemy ORM generator composite primary key support (API_065)."""

    def test_composite_pk_generates_constraint(self):
        """Test that models with multiple primary fields generate PrimaryKeyConstraint."""
        schema = SchnitzelSchema(
            models={
                'OrderItem': Model(
                    name='OrderItem',
                    fields={
                        'order_id': FieldDefinition(type='uuid', primary=True),
                        'product_id': FieldDefinition(type='uuid', primary=True),
                        'quantity': FieldDefinition(type='int', required=True),
                        'price': FieldDefinition(type='float', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify __table_args__ with PrimaryKeyConstraint is generated
        assert '__table_args__ = (' in code
        assert 'sa.PrimaryKeyConstraint("order_id", "product_id")' in code

        # Verify individual fields do NOT have primary_key=True
        assert 'order_id: Mapped[uuid.UUID] = mapped_column(sa.UUID, nullable=False)' in code
        assert 'product_id: Mapped[uuid.UUID] = mapped_column(sa.UUID, nullable=False)' in code

    def test_single_pk_no_constraint(self):
        """Test that models with single primary key do NOT use PrimaryKeyConstraint."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify __table_args__ is NOT generated for single primary key
        assert '__table_args__' not in code

        # Verify single primary key uses primary_key=True
        assert 'id: Mapped[uuid.UUID] = mapped_column(sa.UUID, primary_key=True, nullable=False)' in code

    def test_composite_pk_database_creation(self):
        """Test that composite primary keys create proper database constraints."""
        schema = SchnitzelSchema(
            models={
                'OrderItem': Model(
                    name='OrderItem',
                    fields={
                        'order_id': FieldDefinition(type='int', primary=True),
                        'product_id': FieldDefinition(type='int', primary=True),
                        'quantity': FieldDefinition(type='int', required=True),
                        'unit_price': FieldDefinition(type='float', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_composite_pk_db")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")

        # Create all tables
        orm_models.Base.metadata.create_all(engine)

        # Verify table was created successfully
        inspector = inspect(engine)
        assert 'order_items' in inspector.get_table_names()

        # Verify primary key constraint
        pk_constraint = inspector.get_pk_constraint('order_items')
        pk_columns = pk_constraint['constrained_columns']

        # Verify both columns are part of the primary key
        assert len(pk_columns) == 2
        assert 'order_id' in pk_columns
        assert 'product_id' in pk_columns

    def test_composite_pk_crud_operations(self):
        """Test that CRUD operations work correctly with composite primary keys."""
        schema = SchnitzelSchema(
            models={
                'OrderItem': Model(
                    name='OrderItem',
                    fields={
                        'order_id': FieldDefinition(type='int', primary=True),
                        'product_id': FieldDefinition(type='int', primary=True),
                        'quantity': FieldDefinition(type='int', required=True),
                        'unit_price': FieldDefinition(type='float', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_composite_pk_crud")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Test CRUD operations
        with Session(engine) as session:
            # CREATE - Insert records with composite keys
            item1 = orm_models.OrderItem(
                order_id=1,
                product_id=101,
                quantity=5,
                unit_price=19.99
            )
            item2 = orm_models.OrderItem(
                order_id=1,
                product_id=102,
                quantity=3,
                unit_price=29.99
            )
            item3 = orm_models.OrderItem(
                order_id=2,
                product_id=101,
                quantity=2,
                unit_price=19.99
            )
            session.add_all([item1, item2, item3])
            session.commit()

            # READ - Query by composite primary key
            stmt = select(orm_models.OrderItem).where(
                orm_models.OrderItem.order_id == 1,
                orm_models.OrderItem.product_id == 101
            )
            result = session.execute(stmt).scalar_one()
            assert result.quantity == 5
            assert result.unit_price == 19.99

            # UPDATE - Modify record
            result.quantity = 10
            session.commit()

            # Verify update
            stmt = select(orm_models.OrderItem).where(
                orm_models.OrderItem.order_id == 1,
                orm_models.OrderItem.product_id == 101
            )
            updated_item = session.execute(stmt).scalar_one()
            assert updated_item.quantity == 10

            # DELETE - Remove record
            session.delete(updated_item)
            session.commit()

            # Verify deletion
            stmt = select(orm_models.OrderItem).where(
                orm_models.OrderItem.order_id == 1,
                orm_models.OrderItem.product_id == 101
            )
            deleted_result = session.execute(stmt).one_or_none()
            assert deleted_result is None

            # Verify other records still exist
            stmt = select(orm_models.OrderItem)
            remaining_items = session.execute(stmt).scalars().all()
            assert len(remaining_items) == 2

    def test_composite_pk_uniqueness_constraint(self):
        """Test that composite primary keys enforce uniqueness."""
        schema = SchnitzelSchema(
            models={
                'OrderItem': Model(
                    name='OrderItem',
                    fields={
                        'order_id': FieldDefinition(type='int', primary=True),
                        'product_id': FieldDefinition(type='int', primary=True),
                        'quantity': FieldDefinition(type='int', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_composite_pk_unique")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Test uniqueness constraint
        with Session(engine) as session:
            # Insert first record
            item1 = orm_models.OrderItem(
                order_id=1,
                product_id=101,
                quantity=5
            )
            session.add(item1)
            session.commit()

            # Attempt to insert duplicate composite key (should fail)
            item2 = orm_models.OrderItem(
                order_id=1,
                product_id=101,
                quantity=10
            )
            session.add(item2)

            # Expect IntegrityError due to duplicate primary key
            from sqlalchemy.exc import IntegrityError
            with pytest.raises(IntegrityError):
                session.commit()

            # Rollback to continue testing
            session.rollback()

            # Insert with different composite key (should succeed)
            item3 = orm_models.OrderItem(
                order_id=1,
                product_id=102,  # Different product_id
                quantity=3
            )
            session.add(item3)
            session.commit()

            # Verify both records exist
            stmt = select(orm_models.OrderItem)
            items = session.execute(stmt).scalars().all()
            assert len(items) == 2

    def test_composite_pk_with_three_fields(self):
        """Test composite primary key with three fields."""
        schema = SchnitzelSchema(
            models={
                'Enrollment': Model(
                    name='Enrollment',
                    fields={
                        'student_id': FieldDefinition(type='int', primary=True),
                        'course_id': FieldDefinition(type='int', primary=True),
                        'semester': FieldDefinition(type='string', primary=True),
                        'grade': FieldDefinition(type='string', optional=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify PrimaryKeyConstraint with three fields
        assert 'sa.PrimaryKeyConstraint("student_id", "course_id", "semester")' in code

        # Load and test
        orm_models = load_generated_module(code, "test_orm_composite_pk_three")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Verify primary key constraint
        inspector = inspect(engine)
        pk_constraint = inspector.get_pk_constraint('enrollments')
        pk_columns = pk_constraint['constrained_columns']

        assert len(pk_columns) == 3
        assert 'student_id' in pk_columns
        assert 'course_id' in pk_columns
        assert 'semester' in pk_columns

    def test_composite_pk_with_different_types(self):
        """Test composite primary key with different field types."""
        schema = SchnitzelSchema(
            models={
                'UserSession': Model(
                    name='UserSession',
                    fields={
                        'user_id': FieldDefinition(type='uuid', primary=True),
                        'session_start': FieldDefinition(type='datetime', primary=True),
                        'ip_address': FieldDefinition(type='string', optional=True),
                        'user_agent': FieldDefinition(type='string', optional=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify PrimaryKeyConstraint
        assert 'sa.PrimaryKeyConstraint("user_id", "session_start")' in code

        # Verify field types
        assert 'user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID, nullable=False)' in code
        assert 'session_start: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)' in code

    def test_composite_pk_with_foreign_key(self):
        """Test composite primary key where one field is also a foreign key."""
        schema = SchnitzelSchema(
            models={
                'Order': Model(
                    name='Order',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'total': FieldDefinition(type='float', required=True)
                    },
                    relations={
                        'items': Relation(type='hasMany', model='OrderItem')
                    }
                ),
                'Product': Model(
                    name='Product',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'order_items': Relation(type='hasMany', model='OrderItem')
                    }
                ),
                'OrderItem': Model(
                    name='OrderItem',
                    fields={
                        'quantity': FieldDefinition(type='int', required=True)
                    },
                    relations={
                        'order': Relation(type='belongsTo', model='Order', foreign_key='order_id'),
                        'product': Relation(type='belongsTo', model='Product', foreign_key='product_id')
                    }
                )
            }
        )

        # Manually add composite primary key to OrderItem
        # Note: In the current schema model, we need to mark the FK fields as primary
        schema.models['OrderItem'].fields['order_id'] = FieldDefinition(type='uuid', primary=True)
        schema.models['OrderItem'].fields['product_id'] = FieldDefinition(type='uuid', primary=True)

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load and test
        orm_models = load_generated_module(code, "test_orm_composite_pk_fk")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Verify tables were created
        inspector = inspect(engine)
        assert 'orders' in inspector.get_table_names()
        assert 'products' in inspector.get_table_names()
        assert 'order_items' in inspector.get_table_names()

        # Verify composite primary key
        pk_constraint = inspector.get_pk_constraint('order_items')
        pk_columns = pk_constraint['constrained_columns']
        assert 'order_id' in pk_columns
        assert 'product_id' in pk_columns

        # Verify foreign keys exist
        fk_constraints = inspector.get_foreign_keys('order_items')
        fk_columns = [fk['constrained_columns'][0] for fk in fk_constraints]
        assert 'order_id' in fk_columns
        assert 'product_id' in fk_columns

    def test_composite_pk_nullable_false(self):
        """Test that composite primary key fields are marked as non-nullable."""
        schema = SchnitzelSchema(
            models={
                'OrderItem': Model(
                    name='OrderItem',
                    fields={
                        'order_id': FieldDefinition(type='int', primary=True),
                        'product_id': FieldDefinition(type='int', primary=True),
                        'quantity': FieldDefinition(type='int', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify composite PK fields are nullable=False
        assert 'order_id: Mapped[int] = mapped_column(sa.Integer, nullable=False)' in code
        assert 'product_id: Mapped[int] = mapped_column(sa.Integer, nullable=False)' in code

        # Load and verify in database
        orm_models = load_generated_module(code, "test_orm_composite_pk_nullable")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Verify columns are not nullable
        inspector = inspect(engine)
        columns = inspector.get_columns('order_items')

        order_id_col = next(col for col in columns if col['name'] == 'order_id')
        product_id_col = next(col for col in columns if col['name'] == 'product_id')

        assert order_id_col['nullable'] is False
        assert product_id_col['nullable'] is False

    def test_mixed_models_single_and_composite_pk(self):
        """Test schema with both single and composite primary key models."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                ),
                'OrderItem': Model(
                    name='OrderItem',
                    fields={
                        'order_id': FieldDefinition(type='int', primary=True),
                        'product_id': FieldDefinition(type='int', primary=True),
                        'quantity': FieldDefinition(type='int', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify User has single primary key (no __table_args__)
        user_class = code.split('class User(Base):')[1].split('class OrderItem(Base):')[0]
        assert '__table_args__' not in user_class
        assert 'id: Mapped[uuid.UUID] = mapped_column(sa.UUID, primary_key=True, nullable=False)' in code

        # Verify OrderItem has composite primary key (with __table_args__)
        order_item_class = code.split('class OrderItem(Base):')[1]
        assert '__table_args__' in order_item_class
        assert 'sa.PrimaryKeyConstraint("order_id", "product_id")' in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
