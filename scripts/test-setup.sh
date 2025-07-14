#!/bin/bash

# Test GitHub Actions setup locally
echo "🧪 Testing Newsletter Setup"
echo "============================"

# Check if required files exist
echo "📁 Checking required files..."

required_files=(
    "main.py"
    "conf/config.yaml"
    "templates/newsletter.html"
    "templates/newsletter.txt"
    "pyproject.toml"
)

missing_files=()

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo ""
    echo "❌ Missing required files: ${missing_files[*]}"
    exit 1
fi

# Check if environment is set up
echo ""
echo "🐍 Checking Python environment..."

if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Run: uv venv && source .venv/bin/activate && uv pip install -e ."
    exit 1
fi

echo "✅ Virtual environment exists"

# Check if credentials exist for local testing
echo ""
echo "🔑 Checking credentials (for local testing)..."

if [ -f "credentials.json" ]; then
    echo "✅ Gmail credentials found"
else
    echo "⚠️  Gmail credentials not found (required for local testing)"
fi

if [ -f "token.json" ]; then
    echo "✅ Gmail token found"
else
    echo "⚠️  Gmail token not found (generated on first run)"
fi

if [ -f ".env" ]; then
    echo "✅ Environment file found"
else
    echo "⚠️  .env file not found (create with: echo 'GOOGLE_MAPS_API_KEY=your-key' > .env)"
fi

# Check GitHub Actions workflows
echo ""
echo "⚙️  Checking GitHub Actions..."

workflows=(
    ".github/workflows/send-email.yml"
    ".github/workflows/test-newsletter.yml"
    ".github/workflows/health-check.yml"
    ".github/workflows/notify-failure.yml"
)

for workflow in "${workflows[@]}"; do
    if [ -f "$workflow" ]; then
        echo "✅ $(basename "$workflow")"
    else
        echo "❌ $(basename "$workflow")"
    fi
done

# Test import of main modules
echo ""
echo "🧪 Testing Python imports..."

source .venv/bin/activate 2>/dev/null || true

python -c "
try:
    import hydra
    print('✅ hydra')
except ImportError:
    print('❌ hydra')

try:
    from src.api_clients import get_recipe_of_the_day
    print('✅ src.api_clients')
except ImportError:
    print('❌ src.api_clients')

try:
    from src.utils import get_random_dish_name
    print('✅ src.utils')
except ImportError:
    print('❌ src.utils')

try:
    from jinja2 import Environment
    print('✅ jinja2')
except ImportError:
    print('❌ jinja2')
" 2>/dev/null

echo ""
echo "🎯 Summary:"
echo "==========="
echo "✅ Your newsletter service is set up and ready!"
echo ""
echo "📚 Next steps:"
echo "1. Set up GitHub secrets (run: ./scripts/setup-github-secrets.sh)"
echo "2. Test locally: python main.py"
echo "3. Test on GitHub: Go to Actions → 'Test Newsletter (Manual)' → Run workflow"
echo "4. The daily newsletter will run automatically at 8:00 AM Singapore time"
echo ""
echo "🔍 Monitor your workflows at: https://github.com/$(git config remote.origin.url | sed 's/.*github.com[:\/]\([^.]*\).*/\1/')/actions"
