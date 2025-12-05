#!/bin/bash
# Test script for my-blog example
# This script tests the Schnitzel generators by recreating the my-blog project from scratch
#
# Usage:
#   ./scripts/test-my-blog.sh           # Quick mode (no Flutter, Python-only validation)
#   ./scripts/test-my-blog.sh --full    # Full mode (with Flutter, full Dart validation)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_NAME="my-blog"
SCHEMAS_DIR="$ROOT_DIR/examples/schemas"
GENERATED_DIR="$ROOT_DIR/examples/generated"
FULL_MODE=false

# Parse arguments
if [[ "$1" == "--full" ]]; then
    FULL_MODE=true
fi

echo "🧹 Cleaning up existing project..."
rm -rf "$GENERATED_DIR/$PROJECT_NAME"

echo "🚀 Initializing new project..."
cd "$GENERATED_DIR"
source "$ROOT_DIR/.venv/bin/activate"

if [[ "$FULL_MODE" == true ]]; then
    echo "   (Full mode: creating Flutter project)"
    schnitzel init "$PROJECT_NAME" --with-flutter --no-backend
else
    echo "   (Quick mode: skeleton only)"
    schnitzel init "$PROJECT_NAME" --no-flutter --no-backend
fi

echo "📋 Copying schema..."
cp "$SCHEMAS_DIR/my-blog.schnitzel.yaml" "$GENERATED_DIR/$PROJECT_NAME/schema.schnitzel.yaml"

echo "⚡ Generating code..."
if [[ "$FULL_MODE" == true ]]; then
    schnitzel generate -s "$GENERATED_DIR/$PROJECT_NAME/schema.schnitzel.yaml" -o "$GENERATED_DIR/$PROJECT_NAME" --setup
else
    schnitzel generate -s "$GENERATED_DIR/$PROJECT_NAME/schema.schnitzel.yaml" -o "$GENERATED_DIR/$PROJECT_NAME" --no-setup
fi

echo "✅ Validating Python routes..."
cd "$GENERATED_DIR/$PROJECT_NAME/backend"
python -c "from app.generated.routes import router; print(f'Routes: OK - router has {len(router.routes)} routes')"

if [[ "$FULL_MODE" == true ]]; then
    echo "✅ Validating Dart code..."
    cd "$GENERATED_DIR/$PROJECT_NAME/packages/app"
    dart analyze lib/
else
    echo "⏭️  Skipping Dart validation (use --full for complete validation)"
fi

echo ""
echo "🎉 All validations passed!"
echo ""
echo "Generated project: $GENERATED_DIR/$PROJECT_NAME"
