"""Integration tests for BLoC State generation.

Test Requirements:
1. Generates Event classes (Load, Create, Update, Delete)
2. Generates State classes (Initial, Loading, Loaded, Error)
3. Generates main Bloc class with event handlers
4. Repository integration pattern
5. Error handling with typed failures

This test validates the BLoC generator creates production-ready state management
code following Flutter BLoC patterns and best practices.
"""

import tempfile
import os
from pathlib import Path
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.dart.bloc import BlocStateGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_bloc_generates_event_classes(temp_dir: Path) -> None:
    """Test that Event classes are generated (Load, Create, Update, Delete) (requirement 1)."""
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id: { type: uuid, primary: true }
      customer_id: { type: uuid }
      total: { type: decimal }
      status: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    files = generator.generate(schema, "Order")

    # Verify event file is generated
    assert "order_event.dart" in files
    event_code = files["order_event.dart"]

    # Verify base event class
    assert "abstract class OrderEvent extends Equatable" in event_code
    assert "const OrderEvent();" in event_code

    # Verify Load event
    assert "class OrderLoad extends OrderEvent" in event_code
    assert "const OrderLoad();" in event_code

    # Verify Create event
    assert "class OrderCreate extends OrderEvent" in event_code
    assert "final Order item;" in event_code
    assert "const OrderCreate({required this.item});" in event_code

    # Verify Update event
    assert "class OrderUpdate extends OrderEvent" in event_code
    assert "final Order item;" in event_code
    assert "const OrderUpdate({required this.item});" in event_code

    # Verify Delete event
    assert "class OrderDelete extends OrderEvent" in event_code
    assert "final String id;" in event_code
    assert "const OrderDelete({required this.id});" in event_code

    # Verify Refresh event
    assert "class OrderRefresh extends OrderEvent" in event_code
    assert "const OrderRefresh();" in event_code

    # Verify Equatable props
    assert "List<Object?> get props => [];" in event_code
    assert "List<Object?> get props => [item];" in event_code
    assert "List<Object?> get props => [id];" in event_code

    # Verify part directive (events are part of the main bloc file)
    assert "part of 'order_bloc.dart';" in event_code


def test_bloc_generates_state_classes(temp_dir: Path) -> None:
    """Test that State classes are generated (Initial, Loading, Loaded, Error) (requirement 2)."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id: { type: uuid, primary: true }
      name: { type: string }
      email: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    files = generator.generate(schema, "User")

    # Verify state file is generated
    assert "user_state.dart" in files
    state_code = files["user_state.dart"]

    # Verify base state class
    assert "abstract class UserState extends Equatable" in state_code
    assert "const UserState();" in state_code

    # Verify Initial state
    assert "class UserInitial extends UserState" in state_code
    assert "const UserInitial();" in state_code
    assert "/// Initial state before any operation" in state_code

    # Verify Loading state
    assert "class UserLoading extends UserState" in state_code
    assert "const UserLoading();" in state_code
    assert "/// Loading state during async operations" in state_code

    # Verify Loaded state
    assert "class UserLoaded extends UserState" in state_code
    assert "final List<User> items;" in state_code
    assert "const UserLoaded({required this.items});" in state_code
    assert "/// Loaded state with items" in state_code

    # Verify Error state
    assert "class UserError extends UserState" in state_code
    assert "final String message;" in state_code
    assert "const UserError({required this.message});" in state_code
    assert "/// Error state with message" in state_code

    # Verify Equatable props
    assert "List<Object?> get props => [];" in state_code
    assert "List<Object?> get props => [items];" in state_code
    assert "List<Object?> get props => [message];" in state_code

    # Verify part directive (states are part of the main bloc file)
    assert "part of 'user_bloc.dart';" in state_code


def test_bloc_generates_main_bloc_class(temp_dir: Path) -> None:
    """Test that main BLoC class is generated with event handlers (requirement 3)."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id: { type: uuid, primary: true }
      name: { type: string }
      price: { type: decimal }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    files = generator.generate(schema, "Product")

    # Verify bloc file is generated
    assert "product_bloc.dart" in files
    bloc_code = files["product_bloc.dart"]

    # Verify BLoC class extends proper base class
    assert "class ProductBloc extends Bloc<ProductEvent, ProductState>" in bloc_code

    # Verify repository dependency
    assert "final ProductRepository repository;" in bloc_code
    assert "ProductBloc({required this.repository})" in bloc_code

    # Verify initial state
    assert "super(ProductInitial())" in bloc_code

    # Verify event handler registrations
    assert "on<ProductLoad>(_onLoad);" in bloc_code
    assert "on<ProductCreate>(_onCreate);" in bloc_code
    assert "on<ProductUpdate>(_onUpdate);" in bloc_code
    assert "on<ProductDelete>(_onDelete);" in bloc_code
    assert "on<ProductRefresh>(_onRefresh);" in bloc_code

    # Verify Load handler
    assert "Future<void> _onLoad(ProductLoad event, Emitter<ProductState> emit) async" in bloc_code
    assert "emit(ProductLoading());" in bloc_code
    assert "final items = await repository.getAll();" in bloc_code
    assert "emit(ProductLoaded(items: items));" in bloc_code
    assert "emit(ProductError(message: error.toString()));" in bloc_code

    # Verify Create handler with optimistic update
    assert "Future<void> _onCreate(ProductCreate event, Emitter<ProductState> emit) async" in bloc_code
    assert "final created = await repository.create(event.item);" in bloc_code
    assert "final updatedItems = List<Product>.from(currentState.items)..add(created);" in bloc_code

    # Verify Update handler with optimistic update
    assert "Future<void> _onUpdate(ProductUpdate event, Emitter<ProductState> emit) async" in bloc_code
    assert "final updated = await repository.update(event.item);" in bloc_code
    assert "item.id == updated.id ? updated : item" in bloc_code

    # Verify Delete handler with optimistic update
    assert "Future<void> _onDelete(ProductDelete event, Emitter<ProductState> emit) async" in bloc_code
    assert "await repository.delete(event.id);" in bloc_code
    assert "currentState.items.where((item) => item.id != event.id)" in bloc_code

    # Verify Refresh handler (without loading state)
    assert "Future<void> _onRefresh(ProductRefresh event, Emitter<ProductState> emit) async" in bloc_code
    assert "// Refresh without showing loading state" in bloc_code

    # Verify imports
    assert "import 'package:flutter_bloc/flutter_bloc.dart';" in bloc_code
    assert "import 'package:equatable/equatable.dart';" in bloc_code

    # Verify part directives (events and states are split into separate files)
    assert "part 'product_event.dart';" in bloc_code
    assert "part 'product_state.dart';" in bloc_code


def test_bloc_repository_integration_pattern(temp_dir: Path) -> None:
    """Test that repository integration pattern is correctly implemented (requirement 4)."""
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id: { type: uuid, primary: true }
      status: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    files = generator.generate(schema, "Order")

    bloc_code = files["order_bloc.dart"]

    # Verify repository is injected via constructor
    assert "final OrderRepository repository;" in bloc_code
    assert "OrderBloc({required this.repository})" in bloc_code

    # Verify repository methods are called
    assert "repository.getAll()" in bloc_code
    assert "repository.create(event.item)" in bloc_code
    assert "repository.update(event.item)" in bloc_code
    assert "repository.delete(event.id)" in bloc_code


def test_bloc_error_handling(temp_dir: Path) -> None:
    """Test that error handling with typed failures is implemented (requirement 5)."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id: { type: uuid, primary: true }
      name: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    files = generator.generate(schema, "User")

    bloc_code = files["user_bloc.dart"]

    # Verify try-catch blocks in all handlers
    assert bloc_code.count("try {") >= 5  # Load, Create, Update, Delete, Refresh
    assert bloc_code.count("} catch (error) {") >= 5

    # Verify error state emission
    assert "emit(UserError(message: error.toString()));" in bloc_code

    # Verify rollback on error for Create/Update/Delete
    assert "// Rollback to previous state on error" in bloc_code
    assert "emit(currentState);" in bloc_code

    # Verify state validation before operations
    assert "if (state is! UserLoaded) return;" in bloc_code

    # Verify error message from exception
    assert "error.toString()" in bloc_code


def test_bloc_optimistic_updates(temp_dir: Path) -> None:
    """Test that optimistic updates are implemented."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id: { type: uuid, primary: true }
      name: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    files = generator.generate(schema, "Product")

    bloc_code = files["product_bloc.dart"]

    # Verify optimistic update comment
    assert "// Optimistic update: add to existing list" in bloc_code
    assert "// Optimistic update: replace in existing list" in bloc_code
    assert "// Optimistic update: remove from existing list" in bloc_code

    # Verify current state preservation
    assert "final currentState = state as ProductLoaded;" in bloc_code
    assert "List<Product>.from(currentState.items)" in bloc_code

    # Verify rollback mechanism
    assert "// Rollback to previous state on error" in bloc_code
    assert "emit(currentState);" in bloc_code


def test_bloc_snake_case_conversion(temp_dir: Path) -> None:
    """Test that model names are converted to snake_case for file names."""
    schema_content = """schnitzel: "1.0"

models:
  OrderItem:
    fields:
      id: { type: uuid, primary: true }
      product_name: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    files = generator.generate(schema, "OrderItem")

    # Verify snake_case file names
    assert "order_item_bloc.dart" in files
    assert "order_item_event.dart" in files
    assert "order_item_state.dart" in files

    # Verify PascalCase class names
    bloc_code = files["order_item_bloc.dart"]
    assert "class OrderItemBloc" in bloc_code
    assert "class OrderItemLoad" in files["order_item_event.dart"]
    assert "class OrderItemInitial" in files["order_item_state.dart"]

    # Verify snake_case part directives
    assert "part 'order_item_event.dart';" in bloc_code
    assert "part 'order_item_state.dart';" in bloc_code


def test_bloc_generate_to_file(temp_dir: Path) -> None:
    """Test that generate_to_file creates files with proper headers."""
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id: { type: uuid, primary: true }
      total: { type: decimal }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    output_dir = temp_dir / "lib" / "bloc"

    files_info = generator.generate_to_file(
        schema,
        "Order",
        output_dir,
        schema_source="schema.yaml"
    )

    # Verify all three files were created
    assert len(files_info) == 3

    # Verify file paths
    bloc_file = output_dir / "order_bloc.dart"
    event_file = output_dir / "order_event.dart"
    state_file = output_dir / "order_state.dart"

    assert bloc_file in files_info
    assert event_file in files_info
    assert state_file in files_info

    # Verify files exist
    assert bloc_file.exists()
    assert event_file.exists()
    assert state_file.exists()

    # Verify file sizes
    assert files_info[bloc_file] > 0
    assert files_info[event_file] > 0
    assert files_info[state_file] > 0

    # Verify header comments
    bloc_content = bloc_file.read_text()
    assert "Generated by Schnitzel Framework" in bloc_content
    assert "DO NOT EDIT - This file is auto-generated" in bloc_content
    assert "Source: schema.yaml" in bloc_content

    event_content = event_file.read_text()
    assert "Generated by Schnitzel Framework" in event_content

    state_content = state_file.read_text()
    assert "Generated by Schnitzel Framework" in state_content


def test_bloc_dry_run_mode(temp_dir: Path) -> None:
    """Test that dry_run mode returns file info without writing."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id: { type: uuid, primary: true }
      name: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    output_dir = temp_dir / "lib" / "bloc"

    files_info = generator.generate_to_file(
        schema,
        "User",
        output_dir,
        dry_run=True
    )

    # Verify file info is returned
    assert len(files_info) == 3

    # Verify all file sizes are positive
    for file_path, file_size in files_info.items():
        assert file_size > 0
        assert file_path.name in ["user_bloc.dart", "user_event.dart", "user_state.dart"]

    # Verify files were NOT created
    for file_path in files_info.keys():
        assert not file_path.exists()
    assert not output_dir.exists()


def test_bloc_invalid_model_name(temp_dir: Path) -> None:
    """Test that error is raised for invalid model name."""
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id: { type: uuid, primary: true }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()

    # Verify error is raised for non-existent model
    with pytest.raises(ValueError) as exc_info:
        generator.generate(schema, "NonExistentModel")

    assert "Model 'NonExistentModel' not found in schema" in str(exc_info.value)
    assert "Available models: Order" in str(exc_info.value)


def test_bloc_multiple_models(temp_dir: Path) -> None:
    """Test that BLoC can be generated for different models."""
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id: { type: uuid, primary: true }
      total: { type: decimal }

  Product:
    fields:
      id: { type: uuid, primary: true }
      name: { type: string }

  Customer:
    fields:
      id: { type: uuid, primary: true }
      email: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()

    # Generate BLoC for Order
    order_files = generator.generate(schema, "Order")
    assert "order_bloc.dart" in order_files
    assert "class OrderBloc" in order_files["order_bloc.dart"]

    # Generate BLoC for Product
    product_files = generator.generate(schema, "Product")
    assert "product_bloc.dart" in product_files
    assert "class ProductBloc" in product_files["product_bloc.dart"]

    # Generate BLoC for Customer
    customer_files = generator.generate(schema, "Customer")
    assert "customer_bloc.dart" in customer_files
    assert "class CustomerBloc" in customer_files["customer_bloc.dart"]

    # Verify they are independent
    assert "Order" not in product_files["product_bloc.dart"]
    assert "Product" not in customer_files["customer_bloc.dart"]
    assert "Customer" not in order_files["order_bloc.dart"]


def test_bloc_documentation_comments(temp_dir: Path) -> None:
    """Test that generated code includes proper documentation comments."""
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id: { type: uuid, primary: true }
      status: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    files = generator.generate(schema, "Order")

    bloc_code = files["order_bloc.dart"]
    event_code = files["order_event.dart"]
    state_code = files["order_state.dart"]

    # Verify BLoC documentation
    assert "/// BLoC for managing Order state" in bloc_code

    # Verify Event documentation
    assert "/// Base event class for Order" in event_code
    assert "/// Load all Order items" in event_code
    assert "/// Create a new Order" in event_code
    assert "/// Update an existing Order" in event_code
    assert "/// Delete a Order" in event_code
    assert "/// Refresh Order list without showing loading state" in event_code

    # Verify State documentation
    assert "/// Base state class for Order" in state_code
    assert "/// Initial state before any operation" in state_code
    assert "/// Loading state during async operations" in state_code
    assert "/// Loaded state with items" in state_code
    assert "/// Error state with message" in state_code


def test_bloc_id_field_assumption(temp_dir: Path) -> None:
    """Test that BLoC assumes models have an 'id' field for comparisons."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id: { type: uuid, primary: true }
      name: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    files = generator.generate(schema, "Product")

    bloc_code = files["product_bloc.dart"]

    # Verify id field is used for comparison in Update handler
    assert "item.id == updated.id ? updated : item" in bloc_code

    # Verify id field is used for filtering in Delete handler
    assert "item.id != event.id" in bloc_code

    # Verify comment about id assumption
    assert "// Assuming model has an 'id' field for comparison" in bloc_code


def test_bloc_refresh_without_loading(temp_dir: Path) -> None:
    """Test that Refresh event updates data without showing loading state."""
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id: { type: uuid, primary: true }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    files = generator.generate(schema, "Order")

    bloc_code = files["order_bloc.dart"]

    # Verify Refresh handler doesn't emit Loading state
    # Extract the _onRefresh method properly
    start_idx = bloc_code.find("Future<void> _onRefresh")
    assert start_idx != -1, "_onRefresh method not found"

    # Find the end of the method (next method or class closing brace)
    next_method_idx = bloc_code.find("\n  Future<void>", start_idx + 1)
    end_idx = bloc_code.find("\n}", start_idx) + 2 if next_method_idx == -1 else next_method_idx

    refresh_handler = bloc_code[start_idx:end_idx]
    assert "OrderLoading()" not in refresh_handler
    assert "// Refresh without showing loading state" in refresh_handler

    # Verify Refresh still fetches data and emits Loaded/Error
    assert "repository.getAll()" in refresh_handler
    assert "emit(OrderLoaded(items: items));" in refresh_handler or "emit(OrderLoaded(" in refresh_handler
    assert "emit(OrderError(message: error.toString()));" in refresh_handler


def test_bloc_pagination_support(temp_dir: Path) -> None:
    """Test that BLoC generator supports pagination for list loading (F74)."""
    schema_content = """schnitzel: "1.0"

models:
  Recipe:
    fields:
      id: { type: uuid, primary: true }
      title: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    files = generator.generate(schema, "Recipe")

    event_code = files["recipe_event.dart"]
    state_code = files["recipe_state.dart"]
    bloc_code = files["recipe_bloc.dart"]

    # Verify LoadEvent accepts pagination parameters
    assert "final int page;" in event_code
    assert "final int pageSize;" in event_code
    assert "this.page = 1" in event_code
    assert "this.pageSize = 20" in event_code

    # Verify LoadedState includes pagination info
    assert "final bool hasMore;" in state_code
    assert "final int currentPage;" in state_code

    # Verify LoadMoreEvent is generated for infinite scrolling
    assert "class RecipeLoadMore extends RecipeEvent" in event_code

    # Verify BLoC registers LoadMore handler
    assert "on<RecipeLoadMore>(_onLoadMore);" in bloc_code

    # Verify repository call includes pagination parameters
    assert "page: event.page" in bloc_code
    assert "pageSize: event.pageSize" in bloc_code


def test_bloc_filtering_and_sorting(temp_dir: Path) -> None:
    """Test that BLoC generator supports filtering and sorting (F75)."""
    schema_content = """schnitzel: "1.0"

models:
  Recipe:
    fields:
      id: { type: uuid, primary: true }
      title: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    files = generator.generate(schema, "Recipe")

    event_code = files["recipe_event.dart"]
    state_code = files["recipe_state.dart"]
    bloc_code = files["recipe_bloc.dart"]

    # Verify LoadEvent accepts filters, sortBy, and sortOrder parameters
    assert "final Map<String, dynamic>? filters;" in event_code
    assert "final String? sortBy;" in event_code
    assert "final String? sortOrder;" in event_code

    # Verify LoadedState preserves current filters
    assert "final Map<String, dynamic>? currentFilters;" in state_code
    assert "final String? currentSortBy;" in state_code
    assert "final String? currentSortOrder;" in state_code

    # Verify FilterEvent and SortEvent are generated
    assert "class RecipeFilter extends RecipeEvent" in event_code
    assert "class RecipeSort extends RecipeEvent" in event_code

    # Verify BLoC registers Filter and Sort handlers
    assert "on<RecipeFilter>(_onFilter);" in bloc_code
    assert "on<RecipeSort>(_onSort);" in bloc_code

    # Verify repository call includes filter/sort parameters
    assert "filters: event.filters" in bloc_code
    assert "sortBy: event.sortBy" in bloc_code
    assert "sortOrder: event.sortOrder" in bloc_code


def test_bloc_offline_cache_support(temp_dir: Path) -> None:
    """Test that BLoC supports offline mode with local cache (F119)."""
    schema_content = """schnitzel: "1.0"

models:
  Recipe:
    fields:
      id: { type: uuid, primary: true }
      title: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = BlocStateGenerator()
    files = generator.generate(schema, "Recipe")

    bloc_code = files["recipe_bloc.dart"]
    state_code = files["recipe_state.dart"]

    # Verify LoadedState has isFromCache flag
    assert "final bool isFromCache;" in state_code
    assert "this.isFromCache = false" in state_code

    # Verify BLoC loads from cache first
    assert "repository.getAllFromCache()" in bloc_code
    assert "// Load from cache first for offline support" in bloc_code

    # Verify cache is updated on API success
    assert "repository.updateCache(items)" in bloc_code or "updateCache" in bloc_code

    # Verify cached data is kept visible if API fails
    assert "if (currentState.isFromCache)" in bloc_code or "isFromCache" in bloc_code
