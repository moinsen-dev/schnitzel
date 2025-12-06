# my-blog

A Schnitzel project with full-stack code generation for Flutter and FastAPI.

## Getting Started

### Prerequisites

- [Flutter](https://flutter.dev/docs/get-started/install) (for mobile/web development)
- [Python 3.11+](https://www.python.org/downloads/)
- [Docker](https://docs.docker.com/get-docker/) (for running PostgreSQL)
- [Schnitzel CLI](https://github.com/your-org/schnitzel)

### Quick Start

1. **Edit your schema**
   ```bash
   # Edit the schema definition
   nano schema.schnitzel.yaml
   ```

2. **Generate code**
   ```bash
   # Generate backend and frontend models
   schnitzel generate
   ```

3. **Start the database**
   ```bash
   # Start PostgreSQL with Docker Compose
   docker-compose up -d db
   ```

4. **Run the backend**
   ```bash
   cd backend/app
   # Install dependencies
   pip install -e .
   # Run migrations (if applicable)
   # alembic upgrade head
   # Start the server
   uvicorn main:app --reload
   ```

5. **Run the Flutter app**
   ```bash
   cd apps/my_blog
   # Get dependencies
   flutter pub get
   # Run the app
   flutter run
   ```

## Project Structure

```
my-blog/
├── schema.schnitzel.yaml    # Your data model definitions
├── docker-compose.yaml      # Docker services configuration
├── pubspec.yaml             # Flutter workspace configuration
├── apps/                    # Flutter applications
│   └── my_blog/ # Main Flutter app (with Android/iOS)
│       └── lib/
│           └── main.dart    # App entry point
├── packages/                # Shared Flutter packages
│   └── shared/              # Shared models and API client
│       └── lib/
│           └── generated/   # Generated Dart models
└── backend/                 # FastAPI backend
    └── app/
        └── generated/       # Generated Python models
```

## Next Steps

- Define your models in `schema.schnitzel.yaml`
- Run `schnitzel generate` to create backend and frontend code
- Customize the generated code as needed
- Build your application logic

## Documentation

- [Schnitzel Documentation](https://github.com/your-org/schnitzel/wiki)
- [Schema Reference](https://github.com/your-org/schnitzel/wiki/Schema-Reference)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Flutter Documentation](https://flutter.dev/docs)

## License

This project was generated with Schnitzel CLI.
