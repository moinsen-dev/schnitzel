# Contributing to Schnitzel

Thank you for your interest in contributing to Schnitzel! This document provides guidelines and instructions for contributing.

## Ways to Contribute

- **Report Bugs** - Open an issue describing the bug and how to reproduce it
- **Suggest Features** - Open an issue describing your idea
- **Submit Pull Requests** - Fix bugs or implement new features
- **Improve Documentation** - Help make the docs clearer and more complete
- **Share Feedback** - Tell us about your experience using Schnitzel

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [UV](https://github.com/astral-sh/uv) package manager
- Git

### Getting Started

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/schnitzel.git
   cd schnitzel
   ```

2. **Set up the development environment**

   ```bash
   cd schnitzel-cli
   uv sync --all-extras
   ```

3. **Run the tests**

   ```bash
   uv run pytest
   ```

4. **Run linting and type checks**

   ```bash
   uv run ruff check .
   uv run pyright
   ```

## Code Standards

### Python Style

- Follow PEP 8 guidelines
- Line length: 100 characters max
- Use type hints for all function signatures
- Run `ruff` for linting before committing

### Type Checking

We use Pyright in strict mode. All code must pass type checking:

```bash
uv run pyright
```

### Testing

- Write tests for all new functionality
- Maintain or improve code coverage
- Run the full test suite before submitting:

```bash
uv run pytest --cov
```

## Pull Request Process

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Keep commits focused and atomic
   - Write clear commit messages

3. **Ensure quality**
   - All tests pass
   - No linting errors
   - No type checking errors
   - Code is documented

4. **Submit the PR**
   - Fill out the PR template completely
   - Reference any related issues
   - Describe what the PR does and why

5. **Address feedback**
   - Respond to review comments
   - Make requested changes promptly

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
type(scope): short description

Longer explanation if needed.

Refs: #123
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

**Examples:**
- `feat(generator): add support for custom validators`
- `fix(parser): handle empty schema files gracefully`
- `docs: update installation instructions`

## Issue Guidelines

When opening an issue:

- **Bug reports** should include:
  - Schnitzel version
  - Python version
  - Operating system
  - Steps to reproduce
  - Expected vs actual behavior
  - Relevant schema or error messages

- **Feature requests** should include:
  - Use case description
  - Proposed solution
  - Alternatives considered

## Questions?

If you have questions about contributing, feel free to open a discussion or reach out to the maintainers.

---

Thank you for helping make Schnitzel better!
