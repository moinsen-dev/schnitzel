# CI/CD Status Badges

Add these badges to your README.md to show build status.

## Tests Badge

Replace `OWNER/REPO` with your GitHub username and repository name:

```markdown
![Tests](https://github.com/OWNER/REPO/actions/workflows/test.yml/badge.svg)
```

## Tests Badge (Specific Branch)

To show status for a specific branch (e.g., `main`):

```markdown
![Tests](https://github.com/OWNER/REPO/actions/workflows/test.yml/badge.svg?branch=main)
```

## Coverage Badge

If you're using Codecov:

```markdown
![Coverage](https://codecov.io/gh/OWNER/REPO/branch/main/graph/badge.svg)
```

## Example README Header

```markdown
# Schnitzel CLI

![Tests](https://github.com/OWNER/REPO/actions/workflows/test.yml/badge.svg)
![Coverage](https://codecov.io/gh/OWNER/REPO/branch/main/graph/badge.svg)

Schema-driven full-stack code generator for Flutter and FastAPI.
```

## All Available Badges

```markdown
<!-- Build Status -->
![Tests](https://github.com/OWNER/REPO/actions/workflows/test.yml/badge.svg)

<!-- Code Coverage -->
![Coverage](https://codecov.io/gh/OWNER/REPO/branch/main/graph/badge.svg)

<!-- Python Version -->
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)

<!-- License -->
![License](https://img.shields.io/badge/license-MIT-green)
```
