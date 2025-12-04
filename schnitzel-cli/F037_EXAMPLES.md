# F037 Examples: Dart snake_case to camelCase Conversion

This document provides practical examples of Feature F037 in action.

---

## Example 1: Basic User Model

### Input Schema (YAML)
```yaml
models:
  User:
    fields:
      userId:
        type: string
      firstName:
        type: string
      lastName:
        type: string
      email:
        type: string
      isActive:
        type: boolean
        default: true
      createdAt:
        type: datetime
```

### Generated Dart Code
```dart
@freezed
class User with _$User {
  const factory User({
    @JsonKey(name: 'user_id') required String userId,
    @JsonKey(name: 'first_name') required String firstName,
    @JsonKey(name: 'last_name') required String lastName,
    required String email,                                    // No @JsonKey needed
    @JsonKey(name: 'is_active') @Default(true) bool isActive,
    @JsonKey(name: 'created_at') required DateTime createdAt,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}
```

### JSON Mapping
```json
{
  "user_id": "123",           // Maps to userId
  "first_name": "John",       // Maps to firstName
  "last_name": "Doe",         // Maps to lastName
  "email": "john@example.com", // Maps to email
  "is_active": true,          // Maps to isActive
  "created_at": "2025-12-03T10:00:00Z"  // Maps to createdAt
}
```

---

## Example 2: Mixed Naming Conventions

### Input Schema
```yaml
models:
  Product:
    fields:
      # camelCase fields
      productId:
        type: string
      productName:
        type: string

      # Single-word fields
      name:
        type: string
      price:
        type: float

      # snake_case fields (from legacy API)
      legacy_id:
        type: int
        optional: true
      api_key:
        type: string
        optional: true
```

### Generated Dart Code
```dart
@freezed
class Product with _$Product {
  const factory Product({
    @JsonKey(name: 'product_id') required String productId,
    @JsonKey(name: 'product_name') required String productName,
    required String name,           // No @JsonKey - single word
    required double price,          // No @JsonKey - single word
    int? legacy_id,                 // No @JsonKey - already snake_case
    String? api_key,                // No @JsonKey - already snake_case
  }) = _Product;

  factory Product.fromJson(Map<String, dynamic> json) => _$ProductFromJson(json);
}
```

### Why Each Field Has/Doesn't Have @JsonKey

| Field         | Has @JsonKey? | Reason                                    |
|---------------|---------------|-------------------------------------------|
| `productId`   | ✅ YES        | camelCase → converts to `product_id`      |
| `productName` | ✅ YES        | camelCase → converts to `product_name`    |
| `name`        | ❌ NO         | Single word, same in snake_case           |
| `price`       | ❌ NO         | Single word, same in snake_case           |
| `legacy_id`   | ❌ NO         | Already in snake_case                     |
| `api_key`     | ❌ NO         | Already in snake_case                     |

---

## Example 3: Model with Relationships

### Input Schema
```yaml
models:
  BlogPost:
    fields:
      postId:
        type: string
      title:
        type: string
      content:
        type: string
      publishedAt:
        type: datetime
        optional: true

    relations:
      createdBy:
        type: belongsTo
        model: User

      postComments:
        type: hasMany
        model: Comment

      featuredImage:
        type: hasOne
        model: Image
```

### Generated Dart Code
```dart
@freezed
class BlogPost with _$BlogPost {
  const factory BlogPost({
    @JsonKey(name: 'post_id') required String postId,
    required String title,
    required String content,
    @JsonKey(name: 'published_at') DateTime? publishedAt,
    @JsonKey(name: 'created_by') User? createdBy,
    @JsonKey(name: 'post_comments') List<Comment>? postComments,
    @JsonKey(name: 'featured_image') Image? featuredImage,
  }) = _BlogPost;

  factory BlogPost.fromJson(Map<String, dynamic> json) => _$BlogPostFromJson(json);
}
```

### JSON Structure
```json
{
  "post_id": "abc123",
  "title": "My First Post",
  "content": "Hello, world!",
  "published_at": "2025-12-03T10:00:00Z",
  "created_by": {
    "user_id": "user123",
    "first_name": "John"
  },
  "post_comments": [
    {"comment_id": "c1", "text": "Great post!"},
    {"comment_id": "c2", "text": "Thanks for sharing!"}
  ],
  "featured_image": {
    "image_id": "img1",
    "url": "https://example.com/image.jpg"
  }
}
```

---

## Example 4: Complete E-Commerce Model

### Generated Dart Code
```dart
@freezed
class Order with _$Order {
  const factory Order({
    // Primary identifiers (camelCase)
    @JsonKey(name: 'order_id') required String orderId,
    @JsonKey(name: 'customer_id') required String customerId,

    // Order info (camelCase)
    @JsonKey(name: 'order_number') required String orderNumber,
    @JsonKey(name: 'order_date') required DateTime orderDate,
    @JsonKey(name: 'total_amount') required double totalAmount,

    // Status fields (camelCase with defaults)
    @JsonKey(name: 'is_paid') @Default(false) bool isPaid,
    @JsonKey(name: 'is_shipped') @Default(false) bool isShipped,
    @JsonKey(name: 'is_delivered') @Default(false) bool isDelivered,

    // Single-word fields (no @JsonKey)
    required String status,
    String? notes,

    // Timestamps (camelCase)
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @JsonKey(name: 'updated_at') required DateTime updatedAt,
    @JsonKey(name: 'shipped_at') DateTime? shippedAt,
    @JsonKey(name: 'delivered_at') DateTime? deliveredAt,

    // Relationships (camelCase)
    @JsonKey(name: 'order_items') List<OrderItem>? orderItems,
    @JsonKey(name: 'shipping_address') Address? shippingAddress,
    @JsonKey(name: 'billing_address') Address? billingAddress,
  }) = _Order;

  factory Order.fromJson(Map<String, dynamic> json) => _$OrderFromJson(json);
}
```

---

## Example 5: Edge Cases and Special Scenarios

### Consecutive Capitals
```dart
// Input field: HTTPResponse
@JsonKey(name: 'h_t_t_p_response') required String HTTPResponse,

// Input field: URLPath
@JsonKey(name: 'u_r_l_path') required String URLPath,

// Input field: APIKey
@JsonKey(name: 'a_p_i_key') required String APIKey,
```

### Already snake_case
```dart
// Input field: user_id (no conversion needed)
required String user_id,

// Input field: created_at (no conversion needed)
DateTime? created_at,
```

### Single Character
```dart
// Input field: a
required String a,

// Input field: x
int? x,
```

### Single Word (Any Case)
```dart
// Input field: name
required String name,

// Input field: Name
required String Name,  // Still becomes: required String name,
```

---

## Conversion Reference Table

### Common Field Names

| Dart Field (Input)  | JSON Key (Output) | @JsonKey Added? |
|---------------------|-------------------|-----------------|
| `id`                | `id`              | ❌ NO           |
| `name`              | `name`            | ❌ NO           |
| `email`             | `email`           | ❌ NO           |
| `userId`            | `user_id`         | ✅ YES          |
| `userName`          | `user_name`       | ✅ YES          |
| `firstName`         | `first_name`      | ✅ YES          |
| `lastName`          | `last_name`       | ✅ YES          |
| `isActive`          | `is_active`       | ✅ YES          |
| `isVerified`        | `is_verified`     | ✅ YES          |
| `createdAt`         | `created_at`      | ✅ YES          |
| `updatedAt`         | `updated_at`      | ✅ YES          |
| `deletedAt`         | `deleted_at`      | ✅ YES          |
| `user_id`           | `user_id`         | ❌ NO           |
| `created_at`        | `created_at`      | ❌ NO           |
| `api_key`           | `api_key`         | ❌ NO           |

### Timestamp Fields

| Dart Field          | JSON Key          | @JsonKey Added? |
|---------------------|-------------------|-----------------|
| `createdAt`         | `created_at`      | ✅ YES          |
| `updatedAt`         | `updated_at`      | ✅ YES          |
| `deletedAt`         | `deleted_at`      | ✅ YES          |
| `publishedAt`       | `published_at`    | ✅ YES          |
| `lastLoginAt`       | `last_login_at`   | ✅ YES          |
| `expiresAt`         | `expires_at`      | ✅ YES          |

### Boolean Fields

| Dart Field          | JSON Key          | @JsonKey Added? |
|---------------------|-------------------|-----------------|
| `isActive`          | `is_active`       | ✅ YES          |
| `isVerified`        | `is_verified`     | ✅ YES          |
| `isDeleted`         | `is_deleted`      | ✅ YES          |
| `isPaid`            | `is_paid`         | ✅ YES          |
| `isPublished`       | `is_published`    | ✅ YES          |
| `hasAccess`         | `has_access`      | ✅ YES          |
| `canEdit`           | `can_edit`        | ✅ YES          |

### Relationship Fields

| Dart Field          | JSON Key          | @JsonKey Added? |
|---------------------|-------------------|-----------------|
| `createdBy`         | `created_by`      | ✅ YES          |
| `updatedBy`         | `updated_by`      | ✅ YES          |
| `assignedTo`        | `assigned_to`     | ✅ YES          |
| `userPosts`         | `user_posts`      | ✅ YES          |
| `postComments`      | `post_comments`   | ✅ YES          |
| `orderItems`        | `order_items`     | ✅ YES          |

---

## Usage in Real API Integration

### Scenario: Fetching User from REST API

**API Endpoint:**
```
GET /api/users/123
```

**JSON Response:**
```json
{
  "user_id": "123",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-12-03T10:00:00Z",
  "user_posts": [
    {
      "post_id": "p1",
      "title": "My First Post"
    }
  ]
}
```

**Dart Code:**
```dart
// Deserialize JSON to Dart object
final user = User.fromJson(jsonResponse);

// Access fields using camelCase (Dart convention)
print(user.userId);        // "123"
print(user.firstName);     // "John"
print(user.lastName);      // "Doe"
print(user.email);         // "john@example.com"
print(user.isActive);      // true
print(user.createdAt);     // DateTime object
print(user.userPosts);     // List<Post>

// Serialize back to JSON (snake_case automatically)
final json = user.toJson();
// Produces:
// {
//   "user_id": "123",
//   "first_name": "John",
//   "last_name": "Doe",
//   ...
// }
```

---

## Benefits Summary

1. **Convention Compliance**
   - Dart code uses idiomatic camelCase
   - JSON API uses standard snake_case

2. **Automatic Mapping**
   - No manual conversion code needed
   - json_serializable handles everything

3. **Type Safety**
   - Compile-time checking
   - No runtime errors from typos

4. **Clean Code**
   - Readable Dart field names
   - No manual serialization logic

5. **API Compatibility**
   - Works with any snake_case JSON API
   - Seamless integration with backends

---

## Testing Your Models

```dart
void main() {
  // Test JSON deserialization
  final jsonString = '''
  {
    "user_id": "123",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true
  }
  ''';

  final json = jsonDecode(jsonString);
  final user = User.fromJson(json);

  // Verify camelCase access works
  assert(user.userId == "123");
  assert(user.firstName == "John");
  assert(user.lastName == "Doe");
  assert(user.isActive == true);

  // Test JSON serialization
  final outputJson = user.toJson();
  assert(outputJson['user_id'] == "123");
  assert(outputJson['first_name'] == "John");
  assert(outputJson['is_active'] == true);

  print("All tests passed! ✅");
}
```

---

This feature makes Dart/Flutter development with JSON APIs seamless and follows best practices for both ecosystems.
