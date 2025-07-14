#!/bin/bash

# GitHub Secrets Setup Helper Script
# This script helps you set up the required GitHub secrets for the newsletter service

echo "🔧 GitHub Secrets Setup Helper"
echo "================================="
echo ""
echo "This script will help you set up the required GitHub secrets for the newsletter service."
echo "You'll need to run the actual 'gh secret set' commands manually."
echo ""

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo "   Please install it from: https://cli.github.com/"
    echo "   Then run: gh auth login"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ You're not authenticated with GitHub CLI."
    echo "   Please run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI is installed and authenticated."
echo ""

echo "📋 Required Secrets:"
echo "==================="
echo ""

echo "1. GOOGLE_MAPS_API_KEY"
echo "   - Get from: https://console.cloud.google.com/apis/credentials"
echo "   - Enable: Places API, Geocoding API"
echo "   - Example command:"
echo "   gh secret set GOOGLE_MAPS_API_KEY --body \"your-api-key-here\""
echo ""

echo "2. GMAIL_CREDENTIALS_JSON"
echo "   - Download credentials.json from Google Cloud Console"
echo "   - Gmail API must be enabled"
echo "   - Example command:"
echo "   gh secret set GMAIL_CREDENTIALS_JSON --body \"\$(cat credentials.json)\""
echo ""

echo "3. GMAIL_TOKEN_JSON"
echo "   - Generate by running the newsletter locally first"
echo "   - This file is created after OAuth authentication"
echo "   - Example command:"
echo "   gh secret set GMAIL_TOKEN_JSON --body \"\$(cat token.json)\""
echo ""

echo "🚀 Quick Setup Commands:"
echo "========================"
echo ""
echo "If you have the files ready, run these commands:"
echo ""
echo "# Set Google Maps API Key (replace with your actual key)"
echo "read -s -p \"Enter your Google Maps API Key: \" MAPS_KEY"
echo "gh secret set GOOGLE_MAPS_API_KEY --body \"\$MAPS_KEY\""
echo ""
echo "# Set Gmail credentials (make sure credentials.json exists)"
echo "gh secret set GMAIL_CREDENTIALS_JSON --body \"\$(cat credentials.json)\""
echo ""
echo "# Set Gmail token (make sure token.json exists)"
echo "gh secret set GMAIL_TOKEN_JSON --body \"\$(cat token.json)\""
echo ""

echo "📖 Next Steps:"
echo "=============="
echo "1. Set up the above secrets"
echo "2. Test with: gh workflow run \"Test Newsletter (Manual)\" --ref main"
echo "3. Check logs in the Actions tab of your repository"
echo "4. The daily newsletter will run automatically at 8:00 AM SGT"
echo ""

echo "🔍 Verify secrets are set:"
echo "gh secret list"
echo ""

echo "✨ Done! Your newsletter service should be ready to run automatically."
