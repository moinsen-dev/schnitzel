# ../examples/my-blog

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
   cd packages/app
   # Get dependencies
   flutter pub get
   # Run the app
   flutter run
   ```

## Project Structure

```
../examples/my-blog/
├── schema.schnitzel.yaml   # Your data model definitions
├── docker-compose.yaml      # Docker services configuration
├── backend/                 # FastAPI backend
│   └── app/
│       └── models.py        # Generated Pydantic models
└── packages/                # Flutter frontend
    └── app/
        └── lib/
            └── models/      # Generated Dart models
                └── models.dart
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
