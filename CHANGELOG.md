# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Open source repository files (README, LICENSE, CONTRIBUTING, etc.)

## [0.1.0] - 2025-12-04

### Added
- **Module 0: Foundation** - Core schema parsing and code generation
- YAML schema parser with Pydantic v2 validation
- Schema validator with advanced constraints (F016-F020)
- Python model generator (F021-F025)
- Dart model generator with Freezed support
- Docker Compose generator
- CLI commands: `init` and `generate`
- Rich terminal output with progress indicators
- Comprehensive test suite

### Infrastructure
- Python 3.11+ with UV package manager
- Typer CLI framework
- Jinja2 templating engine
- Ruff linting and Pyright type checking

[Unreleased]: https://github.com/moinsen-dev/schnitzel/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/moinsen-dev/schnitzel/releases/tag/v0.1.0
