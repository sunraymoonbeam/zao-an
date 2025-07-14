#!/bin/bash
# Helper script to validate and set up GitHub secrets properly

set -e

echo "🔧 GitHub Secrets Setup Helper"
echo "================================"

# Function to validate JSON
validate_json() {
    local file=$1
    local name=$2
    
    if [ ! -f "$file" ]; then
        echo "❌ File $file not found"
        return 1
    fi
    
    if python -m json.tool "$file" > /dev/null 2>&1; then
        echo "✅ $name is valid JSON"
        return 0
    else
        echo "❌ $name is not valid JSON"
        echo "First 200 characters:"
        head -c 200 "$file"
        echo ""
        return 1
    fi
}

# Function to format JSON for GitHub secrets
format_for_github() {
    local file=$1
    local name=$2
    
    if validate_json "$file" "$name"; then
        echo ""
        echo "🚀 Setting GitHub secret: $name"
        echo "Use this command:"
        echo "gh secret set $name --body \"\$(cat $file)\""
        echo ""
        echo "Or copy this value to GitHub UI:"
        echo "================================"
        cat "$file"
        echo ""
        echo "================================"
        echo ""
    fi
}

echo "Checking local credential files..."

# Check credentials.json
if [ -f "credentials.json" ]; then
    format_for_github "credentials.json" "GMAIL_CREDENTIALS_JSON"
else
    echo "❌ credentials.json not found"
    echo "   1. Go to Google Cloud Console"
    echo "   2. Enable Gmail API"
    echo "   3. Create OAuth 2.0 credentials"
    echo "   4. Download as credentials.json"
    echo ""
fi

# Check token.json
if [ -f "token.json" ]; then
    format_for_github "token.json" "GMAIL_TOKEN_JSON"
else
    echo "❌ token.json not found"
    echo "   1. Run the script locally first: python main.py"
    echo "   2. Complete OAuth consent flow"
    echo "   3. token.json will be generated"
    echo ""
fi

# Check .env file
if [ -f ".env" ]; then
    echo "✅ .env file found"
    echo "Google Maps API Key from .env:"
    grep GOOGLE_MAPS_API_KEY .env || echo "GOOGLE_MAPS_API_KEY not found in .env"
    echo ""
    echo "🚀 Setting GitHub secret: GOOGLE_MAPS_API_KEY"
    GOOGLE_MAPS_KEY=$(grep GOOGLE_MAPS_API_KEY .env | cut -d'=' -f2-)
    echo "gh secret set GOOGLE_MAPS_API_KEY --body \"$GOOGLE_MAPS_KEY\""
    echo ""
else
    echo "❌ .env file not found"
    echo "   Create .env with: GOOGLE_MAPS_API_KEY=your_api_key_here"
    echo ""
fi

echo "🎯 Summary:"
echo "1. Validate all JSON files are properly formatted"
echo "2. Use the gh commands above to set secrets"
echo "3. Or copy the JSON content to GitHub UI manually"
echo ""
echo "💡 Tip: Ensure no extra whitespace or newlines in the JSON"