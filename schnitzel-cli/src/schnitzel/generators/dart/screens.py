"""Flutter screens generator for Schnitzel schemas.

Generates CRUD screens for each model:
- List screen with pagination
- Detail screen
- Form screen (create/edit)
- Home screen with navigation
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema, DART_TYPE_MAP


class FlutterScreensGenerator:
    """Generates Flutter CRUD screens for models."""

    def __init__(self):
        """Initialize the Flutter screens generator."""
        pass

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase."""
        if '_' not in name and '-' not in name:
            return name[0].upper() + name[1:] if name else name
        parts = name.replace('-', '_').split('_')
        return ''.join(part.capitalize() for part in parts)

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _to_camel_case(self, name: str) -> str:
        """Convert snake_case to camelCase."""
        if '_' not in name:
            return name
        parts = name.split('_')
        return parts[0] + ''.join(part.capitalize() for part in parts[1:])

    def _to_title_case(self, name: str) -> str:
        """Convert snake_case to Title Case with spaces."""
        parts = name.replace('-', '_').split('_')
        return ' '.join(part.capitalize() for part in parts)

    def _pluralize(self, name: str) -> str:
        """Simple pluralization."""
        if name.endswith('y') and len(name) > 1 and name[-2] not in 'aeiou':
            return name[:-1] + 'ies'
        elif name.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return name + 'es'
        else:
            return name + 's'

    def _get_dart_type(self, schema_type: str) -> str:
        """Map schema type to Dart type."""
        return DART_TYPE_MAP.get(schema_type.lower(), schema_type)

    def _get_crud_models(self, schema: SchnitzelSchema) -> Dict[str, Any]:
        """Get models that have crud enabled."""
        crud_models = {}
        if schema.models:
            for model_name, model in schema.models.items():
                if model.crud:
                    crud_models[model_name] = model
        return crud_models

    def _get_display_fields(self, model: Any) -> List[str]:
        """Get fields suitable for display (excluding auto fields and relations)."""
        display_fields = []
        for field_name, field_def in model.fields.items():
            # Skip auto-generated fields for display
            if field_def.auto:
                continue
            display_fields.append(field_name)
        return display_fields

    def _get_form_fields(self, model: Any) -> List[tuple]:
        """Get fields for form input (excluding auto, primary, and computed fields)."""
        form_fields = []
        for field_name, field_def in model.fields.items():
            # Skip auto-generated and primary key fields
            if field_def.auto or field_def.primary:
                continue
            dart_type = self._get_dart_type(field_def.type)
            optional = field_def.optional
            form_fields.append((field_name, dart_type, optional, field_def))
        return form_fields

    def generate_home_screen(self, schema: SchnitzelSchema) -> str:
        """Generate home screen with navigation to all CRUD models."""
        crud_models = self._get_crud_models(schema)

        app_name = "My App"
        if schema.meta:
            app_name = self._to_title_case(schema.meta.name)

        # Build navigation cards for each model
        nav_cards = []
        for model_name in crud_models:
            snake_name = self._to_snake_case(model_name)
            plural_name = self._pluralize(snake_name)
            title = self._to_title_case(model_name)
            plural_title = self._to_title_case(plural_name)

            nav_cards.append(f'''          _NavCard(
            title: '{plural_title}',
            icon: Icons.list_alt,
            route: '/{plural_name}',
          ),''')

        nav_cards_code = '\n'.join(nav_cards) if nav_cards else "          const Center(child: Text('No models defined')),"

        return f'''import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends StatelessWidget {{
  const HomeScreen({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('{app_name}'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Welcome to {app_name}',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Select a resource to manage:',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 24),
            Expanded(
              child: GridView.count(
                crossAxisCount: 2,
                mainAxisSpacing: 16,
                crossAxisSpacing: 16,
                children: [
{nav_cards_code}
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }}
}}

class _NavCard extends StatelessWidget {{
  final String title;
  final IconData icon;
  final String route;

  const _NavCard({{
    required this.title,
    required this.icon,
    required this.route,
  }});

  @override
  Widget build(BuildContext context) {{
    return Card(
      elevation: 2,
      child: InkWell(
        onTap: () => context.go(route),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 48, color: Theme.of(context).colorScheme.primary),
              const SizedBox(height: 8),
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium,
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }}
}}
'''

    def generate_list_screen(self, model_name: str, model: Any, schema: SchnitzelSchema) -> str:
        """Generate list screen for a model."""
        snake_name = self._to_snake_case(model_name)
        plural_name = self._pluralize(snake_name)
        pascal_name = self._to_pascal_case(model_name)
        title = self._to_title_case(model_name)
        plural_title = self._to_title_case(plural_name)

        # Get package name for imports
        package_name = "app"
        if schema.meta:
            package_name = schema.meta.name.lower().replace('-', '_')
        shared_package = f"{package_name}_shared"

        # Get display fields (first 3 non-auto fields)
        display_fields = self._get_display_fields(model)[:3]

        # Build list tile subtitle
        subtitle_parts = []
        for field_name in display_fields[1:]:  # Skip first field (used in title)
            camel_name = self._to_camel_case(field_name)
            subtitle_parts.append(f'${{item.{camel_name}}}')
        subtitle = ' | '.join(subtitle_parts) if subtitle_parts else ''

        # First display field for title
        title_field = self._to_camel_case(display_fields[0]) if display_fields else 'id'

        return f'''import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:{shared_package}/models/models.dart';
import '../main.dart';

class {pascal_name}ListScreen extends StatefulWidget {{
  const {pascal_name}ListScreen({{super.key}});

  @override
  State<{pascal_name}ListScreen> createState() => _{pascal_name}ListScreenState();
}}

class _{pascal_name}ListScreenState extends State<{pascal_name}ListScreen> {{
  List<{pascal_name}>? _items;
  bool _loading = true;
  String? _error;
  final int _page = 1;
  static const int _limit = 20;

  @override
  void initState() {{
    super.initState();
    _loadItems();
  }}

  Future<void> _loadItems() async {{
    setState(() {{
      _loading = true;
      _error = null;
    }});

    try {{
      final items = await ApiClientProvider.instance.list{pascal_name}s(
        page: _page,
        limit: _limit,
      );
      setState(() {{
        _items = items;
        _loading = false;
      }});
    }} catch (e) {{
      setState(() {{
        _error = e.toString();
        _loading = false;
      }});
    }}
  }}

  Future<void> _deleteItem(String id) async {{
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Delete'),
        content: const Text('Are you sure you want to delete this {title.lower()}?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed == true) {{
      try {{
        await ApiClientProvider.instance.delete{pascal_name}(id);
        _loadItems();
        if (mounted) {{
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('{title} deleted successfully')),
          );
        }}
      }} catch (e) {{
        if (mounted) {{
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e')),
          );
        }}
      }}
    }}
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('{plural_title}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadItems,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.go('/{plural_name}/new'),
        child: const Icon(Icons.add),
      ),
      body: _buildBody(),
    );
  }}

  Widget _buildBody() {{
    if (_loading) {{
      return const Center(child: CircularProgressIndicator());
    }}

    if (_error != null) {{
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text('Error: $_error'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadItems,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }}

    if (_items == null || _items!.isEmpty) {{
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.inbox, size: 48, color: Colors.grey),
            const SizedBox(height: 16),
            const Text('No {plural_title.lower()} found'),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: () => context.go('/{plural_name}/new'),
              icon: const Icon(Icons.add),
              label: const Text('Create {title}'),
            ),
          ],
        ),
      );
    }}

    return RefreshIndicator(
      onRefresh: _loadItems,
      child: ListView.builder(
        itemCount: _items!.length,
        itemBuilder: (context, index) {{
          final item = _items![index];
          return ListTile(
            title: Text(item.{title_field}.toString()),
            subtitle: {f"Text('{subtitle}')" if subtitle else "null"},
            trailing: PopupMenuButton<String>(
              onSelected: (value) {{
                switch (value) {{
                  case 'view':
                    context.go('/{plural_name}/${{item.id}}');
                    break;
                  case 'edit':
                    context.go('/{plural_name}/${{item.id}}/edit');
                    break;
                  case 'delete':
                    _deleteItem(item.id.toString());
                    break;
                }}
              }},
              itemBuilder: (context) => [
                const PopupMenuItem(value: 'view', child: Text('View')),
                const PopupMenuItem(value: 'edit', child: Text('Edit')),
                const PopupMenuItem(
                  value: 'delete',
                  child: Text('Delete', style: TextStyle(color: Colors.red)),
                ),
              ],
            ),
            onTap: () => context.go('/{plural_name}/${{item.id}}'),
          );
        }},
      ),
    );
  }}
}}
'''

    def generate_detail_screen(self, model_name: str, model: Any, schema: SchnitzelSchema) -> str:
        """Generate detail screen for a model."""
        snake_name = self._to_snake_case(model_name)
        plural_name = self._pluralize(snake_name)
        pascal_name = self._to_pascal_case(model_name)
        title = self._to_title_case(model_name)

        # Get package name for imports
        package_name = "app"
        if schema.meta:
            package_name = schema.meta.name.lower().replace('-', '_')
        shared_package = f"{package_name}_shared"

        # Build detail fields
        detail_fields = []
        for field_name, field_def in model.fields.items():
            camel_name = self._to_camel_case(field_name)
            label = self._to_title_case(field_name)
            detail_fields.append(f'''            _DetailRow(label: '{label}', value: item.{camel_name}.toString()),''')

        detail_fields_code = '\n'.join(detail_fields)

        return f'''import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:{shared_package}/models/models.dart';
import '../main.dart';

class {pascal_name}DetailScreen extends StatefulWidget {{
  final String id;

  const {pascal_name}DetailScreen({{super.key, required this.id}});

  @override
  State<{pascal_name}DetailScreen> createState() => _{pascal_name}DetailScreenState();
}}

class _{pascal_name}DetailScreenState extends State<{pascal_name}DetailScreen> {{
  {pascal_name}? _item;
  bool _loading = true;
  String? _error;

  @override
  void initState() {{
    super.initState();
    _loadItem();
  }}

  Future<void> _loadItem() async {{
    setState(() {{
      _loading = true;
      _error = null;
    }});

    try {{
      final item = await ApiClientProvider.instance.get{pascal_name}(widget.id);
      setState(() {{
        _item = item;
        _loading = false;
      }});
    }} catch (e) {{
      setState(() {{
        _error = e.toString();
        _loading = false;
      }});
    }}
  }}

  Future<void> _deleteItem() async {{
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Delete'),
        content: const Text('Are you sure you want to delete this {title.lower()}?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed == true) {{
      try {{
        await ApiClientProvider.instance.delete{pascal_name}(widget.id);
        if (mounted) {{
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('{title} deleted successfully')),
          );
          context.go('/{plural_name}');
        }}
      }} catch (e) {{
        if (mounted) {{
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e')),
          );
        }}
      }}
    }}
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('{title} Details'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () => context.go('/{plural_name}/${{widget.id}}/edit'),
          ),
          IconButton(
            icon: const Icon(Icons.delete),
            onPressed: _deleteItem,
          ),
        ],
      ),
      body: _buildBody(),
    );
  }}

  Widget _buildBody() {{
    if (_loading) {{
      return const Center(child: CircularProgressIndicator());
    }}

    if (_error != null) {{
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text('Error: $_error'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadItem,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }}

    if (_item == null) {{
      return const Center(child: Text('{title} not found'));
    }}

    final item = _item!;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
{detail_fields_code}
            ],
          ),
        ),
      ),
    );
  }}
}}

class _DetailRow extends StatelessWidget {{
  final String label;
  final String value;

  const _DetailRow({{required this.label, required this.value}});

  @override
  Widget build(BuildContext context) {{
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: Colors.grey[600],
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
          ),
        ],
      ),
    );
  }}
}}
'''

    def generate_form_screen(self, model_name: str, model: Any, schema: SchnitzelSchema) -> str:
        """Generate form screen for creating/editing a model."""
        snake_name = self._to_snake_case(model_name)
        plural_name = self._pluralize(snake_name)
        pascal_name = self._to_pascal_case(model_name)
        title = self._to_title_case(model_name)

        # Get package name for imports
        package_name = "app"
        if schema.meta:
            package_name = schema.meta.name.lower().replace('-', '_')
        shared_package = f"{package_name}_shared"

        # Get form fields
        form_fields = self._get_form_fields(model)

        # Build controller declarations
        controllers = []
        for field_name, dart_type, optional, field_def in form_fields:
            camel_name = self._to_camel_case(field_name)
            if dart_type == 'bool':
                controllers.append(f"  bool _{camel_name} = false;")
            else:
                controllers.append(f"  final _{camel_name}Controller = TextEditingController();")

        controllers_code = '\n'.join(controllers)

        # Build dispose calls
        dispose_calls = []
        for field_name, dart_type, optional, field_def in form_fields:
            camel_name = self._to_camel_case(field_name)
            if dart_type != 'bool':
                dispose_calls.append(f"    _{camel_name}Controller.dispose();")

        dispose_code = '\n'.join(dispose_calls)

        # Build populate fields (for edit mode)
        populate_fields = []
        for field_name, dart_type, optional, field_def in form_fields:
            camel_name = self._to_camel_case(field_name)
            if dart_type == 'bool':
                populate_fields.append(f"      _{camel_name} = item.{camel_name};")
            elif optional:
                # Optional fields may be null, use null-aware operator
                populate_fields.append(f"      _{camel_name}Controller.text = item.{camel_name}?.toString() ?? '';")
            else:
                # Required fields - no null-aware needed
                populate_fields.append(f"      _{camel_name}Controller.text = item.{camel_name}.toString();")

        populate_code = '\n'.join(populate_fields)

        # Build form fields widgets
        form_widgets = []
        for field_name, dart_type, optional, field_def in form_fields:
            camel_name = self._to_camel_case(field_name)
            label = self._to_title_case(field_name)
            required_marker = "" if optional else "*"

            if dart_type == 'bool':
                form_widgets.append(f'''            SwitchListTile(
              title: const Text('{label}'),
              value: _{camel_name},
              onChanged: (value) => setState(() => _{camel_name} = value),
            ),''')
            elif dart_type in ('int', 'double'):
                keyboard_type = "TextInputType.number"
                form_widgets.append(f'''            TextFormField(
              controller: _{camel_name}Controller,
              decoration: const InputDecoration(
                labelText: '{label}{required_marker}',
                border: OutlineInputBorder(),
              ),
              keyboardType: {keyboard_type},
              validator: {f"(v) => v?.isEmpty ?? true ? 'Required' : null" if not optional else "null"},
            ),
            const SizedBox(height: 16),''')
            elif field_def.type == 'text':
                form_widgets.append(f'''            TextFormField(
              controller: _{camel_name}Controller,
              decoration: const InputDecoration(
                labelText: '{label}{required_marker}',
                border: OutlineInputBorder(),
              ),
              maxLines: 4,
              validator: {f"(v) => v?.isEmpty ?? true ? 'Required' : null" if not optional else "null"},
            ),
            const SizedBox(height: 16),''')
            else:
                form_widgets.append(f'''            TextFormField(
              controller: _{camel_name}Controller,
              decoration: const InputDecoration(
                labelText: '{label}{required_marker}',
                border: OutlineInputBorder(),
              ),
              validator: {f"(v) => v?.isEmpty ?? true ? 'Required' : null" if not optional else "null"},
            ),
            const SizedBox(height: 16),''')

        form_widgets_code = '\n'.join(form_widgets)

        # Build model creation from form values
        model_fields = []

        # First add auto/primary fields with placeholder values (server generates these)
        for field_name, field_def in model.fields.items():
            camel_name = self._to_camel_case(field_name)
            dart_type = self._get_dart_type(field_def.type)

            # Skip optional fields - they can be omitted
            if field_def.optional:
                continue

            # Add placeholder for auto/primary fields not in form_fields
            if field_def.auto or field_def.primary:
                if dart_type == 'DateTime':
                    model_fields.append(f"        {camel_name}: DateTime.now(),  // Server will override")
                elif dart_type in ('int', 'double'):
                    model_fields.append(f"        {camel_name}: 0,  // Server will override")
                else:
                    model_fields.append(f"        {camel_name}: '',  // Server will override")

        # Then add form fields
        for field_name, dart_type, optional, field_def in form_fields:
            camel_name = self._to_camel_case(field_name)
            if dart_type == 'bool':
                model_fields.append(f"        {camel_name}: _{camel_name},")
            elif dart_type == 'int':
                if optional:
                    model_fields.append(f"        {camel_name}: int.tryParse(_{camel_name}Controller.text),")
                else:
                    model_fields.append(f"        {camel_name}: int.parse(_{camel_name}Controller.text),")
            elif dart_type == 'double':
                if optional:
                    model_fields.append(f"        {camel_name}: double.tryParse(_{camel_name}Controller.text),")
                else:
                    model_fields.append(f"        {camel_name}: double.parse(_{camel_name}Controller.text),")
            else:
                if optional:
                    model_fields.append(f"        {camel_name}: _{camel_name}Controller.text.isEmpty ? null : _{camel_name}Controller.text,")
                else:
                    model_fields.append(f"        {camel_name}: _{camel_name}Controller.text,")

        model_fields_code = '\n'.join(model_fields)

        return f'''import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:{shared_package}/models/models.dart';
import '../main.dart';

class {pascal_name}FormScreen extends StatefulWidget {{
  final String? id;

  const {pascal_name}FormScreen({{super.key, this.id}});

  @override
  State<{pascal_name}FormScreen> createState() => _{pascal_name}FormScreenState();
}}

class _{pascal_name}FormScreenState extends State<{pascal_name}FormScreen> {{
  final _formKey = GlobalKey<FormState>();
  bool _loading = false;
  bool _loadingItem = false;
  String? _error;

{controllers_code}

  bool get _isEditMode => widget.id != null;

  @override
  void initState() {{
    super.initState();
    if (_isEditMode) {{
      _loadItem();
    }}
  }}

  @override
  void dispose() {{
{dispose_code}
    super.dispose();
  }}

  Future<void> _loadItem() async {{
    setState(() {{
      _loadingItem = true;
      _error = null;
    }});

    try {{
      final item = await ApiClientProvider.instance.get{pascal_name}(widget.id!);
{populate_code}
      setState(() {{
        _loadingItem = false;
      }});
    }} catch (e) {{
      setState(() {{
        _error = e.toString();
        _loadingItem = false;
      }});
    }}
  }}

  Future<void> _save() async {{
    if (!_formKey.currentState!.validate()) return;

    setState(() {{
      _loading = true;
      _error = null;
    }});

    try {{
      final data = {pascal_name}(
{model_fields_code}
      );

      if (_isEditMode) {{
        await ApiClientProvider.instance.update{pascal_name}(widget.id!, data);
      }} else {{
        await ApiClientProvider.instance.create{pascal_name}(data);
      }}

      if (mounted) {{
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('{title} ${{_isEditMode ? "updated" : "created"}} successfully')),
        );
        context.go('/{plural_name}');
      }}
    }} catch (e) {{
      setState(() {{
        _error = e.toString();
        _loading = false;
      }});
    }}
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditMode ? 'Edit {title}' : 'Create {title}'),
      ),
      body: _buildBody(),
    );
  }}

  Widget _buildBody() {{
    if (_loadingItem) {{
      return const Center(child: CircularProgressIndicator());
    }}

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_error != null)
              Card(
                color: Colors.red[50],
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Text(
                    _error!,
                    style: const TextStyle(color: Colors.red),
                  ),
                ),
              ),
            const SizedBox(height: 16),
{form_widgets_code}
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _loading ? null : _save,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: _loading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(_isEditMode ? 'Update {title}' : 'Create {title}'),
            ),
          ],
        ),
      ),
    );
  }}
}}
'''

    def generate_to_files(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        schema_source: str = "schema.schnitzel.yaml",
        dry_run: bool = False,
    ) -> List[tuple[Path, int]]:
        """Generate all screen files and write them.

        Args:
            schema: The Schnitzel schema
            output_dir: Directory where screens should be written (apps/{name}/lib/screens/)
            schema_source: Optional name of the source schema file for documentation
            dry_run: If True, return file info without writing (default: False)

        Returns:
            List of tuples (Path to file, size in bytes)
        """
        output_path = Path(output_dir)
        results = []

        # Build header comment
        timestamp = datetime.now().isoformat()
        header = f"""// Generated by Schnitzel Framework v{__version__}
// DO NOT EDIT - This file is auto-generated
// Generated at: {timestamp}
// Source: {schema_source}

"""

        if not dry_run:
            output_path.mkdir(parents=True, exist_ok=True)

        # Generate home screen
        home_code = header + self.generate_home_screen(schema)
        home_file = output_path / "home_screen.dart"
        home_size = len(home_code.encode("utf-8"))
        results.append((home_file, home_size))

        if not dry_run:
            home_file.write_text(home_code, encoding="utf-8")

        # Generate screens for each CRUD model
        crud_models = self._get_crud_models(schema)
        for model_name, model in crud_models.items():
            snake_name = self._to_snake_case(model_name)

            # List screen
            list_code = header + self.generate_list_screen(model_name, model, schema)
            list_file = output_path / f"{snake_name}_list_screen.dart"
            list_size = len(list_code.encode("utf-8"))
            results.append((list_file, list_size))
            if not dry_run:
                list_file.write_text(list_code, encoding="utf-8")

            # Detail screen
            detail_code = header + self.generate_detail_screen(model_name, model, schema)
            detail_file = output_path / f"{snake_name}_detail_screen.dart"
            detail_size = len(detail_code.encode("utf-8"))
            results.append((detail_file, detail_size))
            if not dry_run:
                detail_file.write_text(detail_code, encoding="utf-8")

            # Form screen
            form_code = header + self.generate_form_screen(model_name, model, schema)
            form_file = output_path / f"{snake_name}_form_screen.dart"
            form_size = len(form_code.encode("utf-8"))
            results.append((form_file, form_size))
            if not dry_run:
                form_file.write_text(form_code, encoding="utf-8")

        return results
