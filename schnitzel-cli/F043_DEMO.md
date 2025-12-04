# Feature F043 Demo - Flutter Create Integration

## Quick Demo: Two Modes of Init Command

### Mode 1: Standard Init (Without Flutter)

```bash
$ schnitzel init my-basic-project

Creating project: my-basic-project
✓ Project created successfully!

  Project structure:
    my-basic-project/
    ├── schema.schnitzel.yaml
    ├── packages/
    │   └── app/              # Empty directory with README.md
    ├── backend/
    │   └── app/
    └── docker-compose.yaml

  Next steps:
    1. cd my-basic-project
    2. Edit schema.schnitzel.yaml
    3. Run: schnitzel validate schema.schnitzel.yaml
```

**packages/app/ contents:**
```
packages/app/
└── README.md
```

---

### Mode 2: Init with Flutter Scaffolding

```bash
$ schnitzel init my-flutter-project --with-flutter

Creating project: my-flutter-project
Creating Flutter app...
✓ Flutter app created successfully
✓ Project created successfully!

  Project structure:
    my-flutter-project/
    ├── schema.schnitzel.yaml
    ├── packages/
    │   └── app/              # Full Flutter application!
    ├── backend/
    │   └── app/
    └── docker-compose.yaml

  Next steps:
    1. cd my-flutter-project
    2. Edit schema.schnitzel.yaml
    3. Run: schnitzel validate schema.schnitzel.yaml
```

**packages/app/ contents (Full Flutter App):**
```
packages/app/
├── .dart_tool/
├── .gitignore
├── .idea/
├── .metadata
├── analysis_options.yaml
├── android/              # Android platform
├── ios/                  # iOS platform
├── lib/                  # Dart source code
│   └── main.dart
├── macos/                # macOS platform
├── pubspec.lock
├── pubspec.yaml          # Dependencies & config
├── README.md             # Flutter's README
├── test/                 # Test directory
└── web/                  # Web platform
```

---

## Dart Package Name Sanitization Examples

The CLI automatically sanitizes project names to be valid Dart package names:

| Input Name | Sanitized Package Name |
|-----------|------------------------|
| `my-app` | `my_app_app` |
| `test-flutter-demo` | `test_flutter_demo_app` |
| `My Project!` | `my_project_app` |
| `123project` | `app_123project_app` |
| `hello-world-2024` | `hello_world_2024_app` |

**Verification:**
```bash
$ grep "^name:" my-flutter-project/packages/app/pubspec.yaml
name: my_flutter_project_app
```

---

## Error Handling Demo

### Scenario 1: Flutter Not Installed

```bash
$ schnitzel init test-project --with-flutter

Creating project: test-project
Warning: Flutter is not installed or not in PATH
Continuing without Flutter app creation...
✓ Project created successfully!
```

**Result:** Empty packages/app/ directory created as fallback

---

### Scenario 2: Flutter Create Fails

```bash
$ schnitzel init test-project --with-flutter

Creating project: test-project
Creating Flutter app...
Warning: Flutter create failed: [error details]
Creating empty packages/app directory instead...
✓ Project created successfully!
```

**Result:** Command succeeds, empty directory created

---

## Combining with Other Options

### With Full Template

```bash
$ schnitzel init blog-app --with-flutter --template full

Creating project: blog-app
Using full template with example models
Creating Flutter app...
✓ Flutter app created successfully
✓ Project created successfully!
```

**Result:**
- ✅ Full Flutter app in packages/app/
- ✅ schema.schnitzel.yaml with User, Post, Comment models
- ✅ docker-compose.yaml with backend and db services
- ✅ Ready for full-stack development!

---

## Real-World Usage Example

```bash
# Create a new e-commerce project with Flutter frontend
$ schnitzel init ecommerce-app --with-flutter --template full

# Navigate to project
$ cd ecommerce-app

# Verify Flutter app
$ cd packages/app
$ flutter doctor
$ flutter run

# Meanwhile, customize your schema
$ cd ../..
$ vim schema.schnitzel.yaml

# Generate code (future feature)
$ schnitzel generate
```

---

## Performance Notes

- **Version check:** < 1 second
- **Flutter create:** 10-30 seconds (varies by system)
- **Timeout protection:** 120 seconds maximum
- **No Flutter required:** Command works fine without Flutter installed

---

## Testing Commands

```bash
# Run all F043 tests
pytest tests/integration/test_cli_flutter_create_f043.py -v

# Run regression tests
pytest tests/integration/test_cli_init_f040.py -v

# Run all init-related tests
pytest tests/integration/test_cli_init* -v
```

---

## CLI Help

```bash
$ schnitzel init --help

Usage: schnitzel init [OPTIONS] PROJECT_NAME

  Initialize a new Schnitzel project with directory structure.

Options:
  --with-flutter          Create Flutter app in packages/app using
                         flutter create
  --template -t TEXT     Template to use for schema.schnitzel.yaml
                         (choices: minimal, full)
                         [default: minimal]
  --help                 Show this message and exit.
```

---

## Common Use Cases

### 1. Quick Prototype (No Flutter)
```bash
schnitzel init quick-prototype
```
Fast! Empty directory, add Flutter manually later if needed.

### 2. Full-Stack App with Flutter
```bash
schnitzel init fullstack-app --with-flutter --template full
```
Complete setup with Flutter frontend and example data models.

### 3. Mobile-First Project
```bash
schnitzel init mobile-app --with-flutter
cd mobile-app/packages/app
flutter run -d ios
```
Jump straight into Flutter development.

### 4. API-First Development
```bash
schnitzel init api-project --template full
# Skip Flutter, focus on backend first
# Add Flutter later: cd packages/app && flutter create .
```

---

## Next Steps After Init

After running `schnitzel init my-project --with-flutter`:

1. **Verify Flutter app:**
   ```bash
   cd my-project/packages/app
   flutter doctor
   flutter pub get
   flutter test
   flutter run
   ```

2. **Customize schema:**
   ```bash
   cd ../..
   vim schema.schnitzel.yaml
   schnitzel validate schema.schnitzel.yaml
   ```

3. **Start development:**
   - Edit Flutter app in `packages/app/lib/main.dart`
   - Define data models in `schema.schnitzel.yaml`
   - Set up backend in `backend/app/`
   - Use `docker-compose up` for database

---

## Tips & Tricks

### Tip 1: Name Matters
Choose project names carefully - they'll be used throughout:
- Directory name: `my-project`
- Dart package: `my_project_app`
- Flutter app: `packages/app/`

### Tip 2: Check Flutter First
Before using `--with-flutter`, verify Flutter is installed:
```bash
flutter --version
flutter doctor
```

### Tip 3: Template Choice
- **minimal:** Quick start, empty models
- **full:** Example models (User, Post, Comment)

### Tip 4: Fallback is OK
If Flutter fails, don't worry! The project is created with an empty directory.
You can always run `flutter create` manually later:
```bash
cd packages/app
flutter create .
```

---

## Troubleshooting

**Problem:** Flutter create times out
**Solution:** Check internet connection (Flutter downloads dependencies), increase timeout is acceptable

**Problem:** Invalid Dart package name error
**Solution:** Don't worry! Names are auto-sanitized. Check pubspec.yaml for actual name used

**Problem:** Flutter not in PATH
**Solution:** Install Flutter or add to PATH: https://flutter.dev/docs/get-started/install

**Problem:** Want to retry Flutter create
**Solution:** Delete packages/app/ and run init again, or manually run flutter create

---

## Summary

Feature F043 adds seamless Flutter integration to Schnitzel's init command:
- ✅ Optional `--with-flutter` flag
- ✅ Automatic project name sanitization
- ✅ Robust error handling
- ✅ Graceful fallbacks
- ✅ No breaking changes
- ✅ Production-ready

Happy coding! 🚀
