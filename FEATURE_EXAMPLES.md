# Feature Examples: Dart and Event Generators

## Feature 1: Connection State Management

### Generated Dart Code (WebSocket Client)
```dart
class WebSocketClient {
  final Map<String, bool> _isConnected = {};

  Stream<Map<String, dynamic>> matchStream(String matchId) {
    final streamKey = 'matchStream';
    
    Future<void> connect() async {
      // Prevents duplicate connections
      if (_isConnected[streamKey] == true) return;
      
      try {
        final channel = IOWebSocketChannel.connect(uri);
        _isConnected[streamKey] = true;  // Set connected
        
        channel.stream.listen(
          (message) { /* ... */ },
          onError: (error) {
            _isConnected[streamKey] = false;  // Reset on error
          },
          onDone: () {
            _isConnected[streamKey] = false;  // Reset on disconnect
          },
        );
      } catch (e) {
        _isConnected[streamKey] = false;  // Reset on exception
      }
    }
  }
  
  void send(String streamKey, Map<String, dynamic> message) {
    // Only send if connected
    if (_isConnected[streamKey] == true) {
      channel.sink.add(jsonEncode(message));
    }
  }
}
```

---

## Feature 2: SSE Parsing with 'data:' Prefix Stripping

### Generated Dart Code (SSE Client)
```dart
class SSEClient {
  Stream<Map<String, dynamic>> orderTracking(String orderId) {
    response.stream
      .transform(utf8.decoder)
      .transform(const LineSplitter())
      .listen(
        (line) {
          // Check for SSE data line
          if (line.startsWith('data: ')) {
            // Strip 'data: ' prefix (6 characters)
            final data = line.substring(6);
            try {
              // Parse JSON payload
              final json = jsonDecode(data) as Map<String, dynamic>;
              controller.add(json);
            } catch (e) {
              // Skip malformed JSON
            }
          }
        },
      );
  }
}
```

### Example SSE Stream
```
data: {"event": "order.updated", "order_id": "123", "status": "shipped"}
data: {"event": "order.updated", "order_id": "123", "status": "delivered"}
```

---

## Feature 3: BLoC Optimistic Updates with Rollback

### Generated Dart Code (BLoC)
```dart
class ProductBloc extends Bloc<ProductEvent, ProductState> {
  Future<void> _onCreate(ProductCreate event, Emitter<ProductState> emit) async {
    if (state is! ProductLoaded) return;
    
    // Save current state for potential rollback
    final currentState = state as ProductLoaded;
    emit(ProductLoading());
    
    try {
      final created = await repository.create(event.item);
      
      // Optimistic update: add to existing list immediately
      final updatedItems = List<Product>.from(currentState.items)..add(created);
      emit(ProductLoaded(items: updatedItems));
    } catch (error) {
      // Rollback to previous state on error
      emit(currentState);
      emit(ProductError(message: error.toString()));
    }
  }
  
  Future<void> _onUpdate(ProductUpdate event, Emitter<ProductState> emit) async {
    final currentState = state as ProductLoaded;
    emit(ProductLoading());
    
    try {
      final updated = await repository.update(event.item);
      
      // Optimistic update: replace in existing list
      final updatedItems = currentState.items.map((item) {
        return item.id == updated.id ? updated : item;
      }).toList();
      
      emit(ProductLoaded(items: updatedItems));
    } catch (error) {
      // Rollback to previous state on error
      emit(currentState);
      emit(ProductError(message: error.toString()));
    }
  }
  
  Future<void> _onDelete(ProductDelete event, Emitter<ProductState> emit) async {
    final currentState = state as ProductLoaded;
    emit(ProductLoading());
    
    try {
      await repository.delete(event.id);
      
      // Optimistic update: remove from existing list
      final updatedItems = currentState.items.where((item) => item.id != event.id).toList();
      emit(ProductLoaded(items: updatedItems));
    } catch (error) {
      // Rollback to previous state on error
      emit(currentState);
      emit(ProductError(message: error.toString()));
    }
  }
}
```

---

## Feature 4: BLoC Proper Imports

### Generated Dart Code (BLoC Files)

#### product_bloc.dart
```dart
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';

part 'product_event.dart';
part 'product_state.dart';

class ProductBloc extends Bloc<ProductEvent, ProductState> {
  final ProductRepository repository;
  
  ProductBloc({required this.repository}) : super(ProductInitial()) {
    on<ProductLoad>(_onLoad);
    on<ProductCreate>(_onCreate);
    on<ProductUpdate>(_onUpdate);
    on<ProductDelete>(_onDelete);
  }
  // ...
}
```

#### product_event.dart
```dart
part of 'product_bloc.dart';

abstract class ProductEvent extends Equatable {
  const ProductEvent();
  
  @override
  List<Object?> get props => [];
}

class ProductLoad extends ProductEvent {
  const ProductLoad();
}

class ProductCreate extends ProductEvent {
  final Product item;
  
  const ProductCreate({required this.item});
  
  @override
  List<Object?> get props => [item];
}
```

#### product_state.dart
```dart
part of 'product_bloc.dart';

abstract class ProductState extends Equatable {
  const ProductState();
  
  @override
  List<Object?> get props => [];
}

class ProductInitial extends ProductState {
  const ProductInitial();
}

class ProductLoaded extends ProductState {
  final List<Product> items;
  
  const ProductLoaded({required this.items});
  
  @override
  List<Object?> get props => [items];
}
```

---

## Feature 5: Complex Nested Payloads in Events

### Schema YAML
```yaml
events:
  order.placed:
    description: "Order placed with customer and items"
    payload:
      order_id: uuid
      customer_id: uuid
      total: decimal
      items_count: integer
      shipping_address: string
    channels:
      - websocket
      - redis
```

### Generated Python Code
```python
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel

class OrderPlacedPayload(BaseModel):
    """Order placed with customer and items"""
    
    order_id: UUID
    customer_id: UUID
    total: Decimal
    items_count: int
    shipping_address: str

class EventPublisher:
    async def publish_order_placed(self, payload: OrderPlacedPayload):
        """Publish order.placed event."""
        await self.publish(
            "order.placed",
            payload.model_dump(),
            channels=['websocket', 'redis']
        )
```

### Usage Example
```python
# Create event payload
payload = OrderPlacedPayload(
    order_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    customer_id=UUID("789e4567-e89b-12d3-a456-426614174111"),
    total=Decimal("99.99"),
    items_count=3,
    shipping_address="123 Main St"
)

# Publish to websocket and redis channels
await event_publisher.publish_order_placed(payload)
```

---

## Feature 6: List Payloads in Events

### Schema YAML
```yaml
events:
  inventory.updated:
    description: "Inventory updated with list of products"
    payload:
      product_ids: list<uuid>
      quantities: list<integer>
      categories: list<string>
    channels:
      - redis
```

### Generated Python Code
```python
from uuid import UUID
from pydantic import BaseModel

class InventoryUpdatedPayload(BaseModel):
    """Inventory updated with list of products"""
    
    product_ids: list[UUID]
    quantities: list[int]
    categories: list[str]

class EventPublisher:
    async def publish_inventory_updated(self, payload: InventoryUpdatedPayload):
        """Publish inventory.updated event."""
        await self.publish(
            "inventory.updated",
            payload.model_dump(),
            channels=['redis']
        )
```

### Usage Example
```python
# Create event payload with lists
payload = InventoryUpdatedPayload(
    product_ids=[
        UUID("123e4567-e89b-12d3-a456-426614174000"),
        UUID("223e4567-e89b-12d3-a456-426614174001"),
        UUID("323e4567-e89b-12d3-a456-426614174002"),
    ],
    quantities=[10, 25, 5],
    categories=["electronics", "computers", "accessories"]
)

# Publish to redis channel
await event_publisher.publish_inventory_updated(payload)
```

---

## Type Support Summary

### Supported Simple Types
- `string` / `str` → Python: `str`, Dart: `String`
- `integer` / `int` → Python: `int`, Dart: `int`
- `float` / `double` → Python: `float`, Dart: `double`
- `decimal` → Python: `Decimal`, Dart: `double`
- `bool` / `boolean` → Python: `bool`, Dart: `bool`
- `uuid` → Python: `UUID`, Dart: `String`
- `datetime` / `date` → Python: `datetime`, Dart: `DateTime`

### Supported List Types
- `list<string>` → Python: `list[str]`, Dart: `List<String>`
- `list<integer>` → Python: `list[int]`, Dart: `List<int>`
- `list<uuid>` → Python: `list[UUID]`, Dart: `List<String>`
- `list<float>` → Python: `list[float]`, Dart: `List<double>`

### Field Definition Formats
Both formats are supported:

**Simple format:**
```yaml
payload:
  order_id: uuid
  customer_name: string
```

**Dict format:**
```yaml
payload:
  order_id: 
    type: uuid
    optional: false
  customer_name:
    type: string
    optional: true
```
