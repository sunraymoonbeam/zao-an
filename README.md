# Zao An 早安 - Daily Newsletter Service

A automated daily newsletter service that aggregates content from various APIs and sends personalized emails using GitHub Actions.

## Features

- 📧 **Gmail Integration**: Sends HTML/text emails via Gmail API
- 🔬 **ArXiv Papers**: Daily research papers with PDF downloads
- 🌅 **Solar Schedule**: Sunrise/sunset times for your location
- 💭 **Daily Quotes**: Zen and Stoic quotes for inspiration
- 🍳 **Recipe of the Day**: Random recipes with images
- 📍 **Local Places**: Restaurant recommendations based on the daily recipe
- 🌟 **Horoscope**: Daily horoscope predictions
- 📚 **Word of the Day**: Vocabulary enrichment
- 🎭 **Poem of the Day**: Daily poetry
- 🐱 **Cat GIFs**: Because everyone needs more cats
- ⏰ **Automated Scheduling**: Runs daily via GitHub Actions

## GitHub Actions Setup

This project includes automated email sending via GitHub Actions that runs daily at 8:00 AM Singapore time.

### Required GitHub Secrets

You need to set up the following secrets in your GitHub repository:

1. **Go to Settings → Secrets and variables → Actions**
2. **Add the following Repository secrets:**

   - `GOOGLE_MAPS_API_KEY`: Your Google Maps API key for place recommendations
   - `GMAIL_CREDENTIALS_JSON`: Your Gmail API credentials (entire JSON file content)
   - `GMAIL_TOKEN_JSON`: Your Gmail API token (entire JSON file content)

### Workflow Files

- **`send-email.yml`**: Main workflow that runs daily at 8:00 AM SGT
- **`test-newsletter.yml`**: Manual testing workflow for validation

### Quick GitHub Setup

Use the helper script to set up GitHub secrets easily:

```bash
# Make the script executable (if not already)
chmod +x scripts/setup-github-secrets.sh

# Run the setup helper
./scripts/setup-github-secrets.sh
```

Or set secrets manually using GitHub CLI:

```bash
# Install GitHub CLI: https://cli.github.com/
gh auth login

# Set your secrets
gh secret set GOOGLE_MAPS_API_KEY --body "your-api-key-here"
gh secret set GMAIL_CREDENTIALS_JSON --body "$(cat credentials.json)"
gh secret set GMAIL_TOKEN_JSON --body "$(cat token.json)"
```

### Workflow Monitoring

- **Daily Health Check**: Runs at 7:30 AM SGT to verify API endpoints
- **Failure Notifications**: Automatically creates GitHub issues when workflows fail
- **Manual Testing**: Use "Test Newsletter (Manual)" workflow for validation

## Setup

### Local Development

1. **Install Python 3.12+** and [uv](https://docs.astral.sh/uv/getting-started/installation/)

2. **Clone and install dependencies:**
   ```bash
   git clone <your-repo-url>
   cd zao-an
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

3. **Set up Gmail API credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Gmail API
   - Create credentials (OAuth 2.0 Client ID)
   - Download `credentials.json` and place it in the project root
   - Run the script once locally to generate `token.json`

4. **Configure environment variables:**
   ```bash
   # Create .env file
   echo "GOOGLE_MAPS_API_KEY=your_google_maps_api_key" > .env
   ```

5. **Update configuration:**
   - Edit `conf/config.yaml` to set your email addresses and preferences

6. **Run locally:**
   ```bash
   python main.py
   ```

### GitHub Actions Setup (Automated Scheduling)

This service can run automatically every day at 8:00 AM Singapore time using GitHub Actions.

#### Required Secrets

Configure these secrets in your GitHub repository (`Settings > Secrets and variables > Actions`):

1. **`GOOGLE_MAPS_API_KEY`**
   - Get from [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Places API and Text Search API

2. **`GMAIL_CREDENTIALS_JSON`**
   - Contents of your `credentials.json` file (as a JSON string)
   - Example: `{"installed":{"client_id":"...","client_secret":"...","auth_uri":"..."}}`

3. **`GMAIL_TOKEN_JSON`**
   - Contents of your `token.json` file (as a JSON string)
   - Generated after first local run with OAuth consent
   - Example: `{"token":"...","refresh_token":"...","token_uri":"..."}`

#### Setting Up Secrets

1. **Get Gmail API Credentials:**
   ```bash
   # Run locally first to generate token.json
   python main.py
   
   # Copy the contents for GitHub secrets
   cat credentials.json  # Copy this to GMAIL_CREDENTIALS_JSON
   cat token.json       # Copy this to GMAIL_TOKEN_JSON
   ```

2. **Add to GitHub:**
   - Go to your repository > Settings > Secrets and variables > Actions
   - Click "New repository secret"
   - Add each secret with the exact names above

#### Workflows

- **`send-email.yml`**: Runs daily at 8:00 AM SGT (midnight UTC)
- **`test-newsletter.yml`**: Manual testing workflow with dry-run option

#### Manual Trigger

You can manually trigger the newsletter or run tests:

1. Go to Actions tab in your GitHub repository
2. Select "Send Daily Newsletter" or "Test Newsletter (Manual)"
3. Click "Run workflow"

## Configuration

### Email Settings (`conf/config.yaml`)

```yaml
email:
  recipients:
    - "recipient1@example.com"
    - "recipient2@example.com"
  sender: "your-email@gmail.com"
  format: "html"  # or "plain"
```

### API Settings

```yaml
api:
  location: "Singapore"
  country_code: "SG"
  horoscope_sign: "scorpio"
```

### ArXiv Papers

```yaml
arxiv:
  query: "Computer Vision"
  max_results: 100
  random_k: 3
  download_papers: true
  storage_type: "local"  # or "s3"
```

## 📚 PDF Attachments & Storage

Your newsletter can include arXiv research papers as PDF attachments. The system supports three storage modes:

### Storage Types

1. **`local`** - Permanent storage on local filesystem
   - ✅ Good for: Development, personal use
   - ❌ Not suitable for: GitHub Actions (files get deleted)

2. **`s3`** - Cloud storage on AWS S3
   - ✅ Good for: Long-term storage, backup
   - ❌ Not suitable for: Email attachments (files are remote)

3. **`temp`** - Temporary storage (perfect for GitHub Actions)
   - ✅ Good for: GitHub Actions, one-time email sending
   - ✅ Files exist during script execution, then cleaned up
   - ✅ Perfect for email attachments

### Configuration

The system automatically uses the right storage type:
- **Local development**: Uses `storage_type: local` from `conf/config.yaml`
- **GitHub Actions**: Uses `storage_type: temp` from `conf/config-github.yaml`

### How It Works in GitHub Actions

1. 📥 Downloads arXiv PDFs to temporary directory (`/tmp/arxiv_papers_*`)
2. 📧 Attaches PDFs to email and sends immediately  
3. 🧹 Temporary files are automatically cleaned up when workflow ends
4. ✅ No storage costs, no file management needed!

## 🔧 Configuration Files

- **`conf/config.yaml`** - Default configuration for local development
- **`conf/config-github.yaml`** - Optimized for GitHub Actions with temp storage

---

## 🎯 Summary

Your newsletter service is now production-ready with GitHub Actions! The workflows will handle everything automatically once you set up the secrets, and PDF attachments will work seamlessly in both local and GitHub Actions environments.

## Project Structure

```
zao-an/
├── main.py                 # Main application script
├── pyproject.toml         # Dependencies and project config
├── conf/
│   ├── config.yaml        # Main configuration
│   └── logging.yaml       # Logging configuration
├── src/
│   ├── api_clients.py     # External API integrations
│   ├── api_google_places.py # Google Places API
│   ├── gmail_service.py   # Gmail API wrapper
│   └── utils.py           # Utility functions
├── templates/
│   ├── newsletter.html    # HTML email template
│   └── newsletter.txt     # Plain text email template
├── .github/workflows/
│   ├── send-email.yml     # Daily automation
│   └── test-newsletter.yml # Testing workflow
└── data/                  # Downloaded PDFs and data
```

## Troubleshooting

### 🚨 GitHub Actions Issues

#### JSON Decode Error in Secrets
If you see `JSONDecodeError: Expecting value: line 2 column 1`, your GitHub secrets are not properly formatted:

```bash
# Step 1: Validate your local files
python scripts/validate-credentials.py

# Step 2: Use the debug helper
chmod +x scripts/debug-secrets.sh
./scripts/debug-secrets.sh
```

#### Cache Issues
- ✅ Fixed: Now uses `uv` cache instead of pip
- Clear GitHub Actions cache: Settings → Actions → Caches → Delete

#### Secret Formatting Rules
- ❌ **Wrong**: Extra spaces or newlines in JSON
- ❌ **Wrong**: Copying from terminal with line breaks
- ✅ **Right**: Exact JSON content from files (use `cat credentials.json`)

### 🔧 Common Issues

1. **Gmail Authentication Errors:**
   - Ensure OAuth consent screen is configured
   - Check that Gmail API is enabled
   - Verify credentials.json and token.json are valid

2. **GitHub Actions Failures:**
   - Check that all secrets are properly configured
   - Verify secret names match exactly
   - Check workflow logs for specific error messages

3. **API Rate Limits:**
   - Some APIs have rate limits
   - The workflow includes retries and error handling

### 🧪 Testing

```bash
# Validate local credentials before GitHub setup
python scripts/validate-credentials.py

# Test API connections
python -c "from src.api_clients import get_zen_quote; print(get_zen_quote())"

# Test Gmail service (requires credentials)
python -c "from src.gmail_service import GmailService; print('Gmail service imported successfully')"

# Test in GitHub Actions with dry run
# Go to Actions → "Test Newsletter (Manual)" → Run with dry_run=true
```

### 📋 GitHub Secrets Checklist

Before setting up GitHub Actions, ensure:

- [ ] `credentials.json` is valid JSON (test with `python -m json.tool credentials.json`)
- [ ] `token.json` is valid JSON (test with `python -m json.tool token.json`)
- [ ] Google Maps API key is set in `.env`
- [ ] All three secrets are set in GitHub: `GMAIL_CREDENTIALS_JSON`, `GMAIL_TOKEN_JSON`, `GOOGLE_MAPS_API_KEY`
- [ ] Environment `zao-an` is created in GitHub repository settings

## Troubleshooting

### Common Issues

1. **Gmail Authentication Errors:**
   - Ensure OAuth consent screen is configured
   - Check that Gmail API is enabled
   - Verify credentials.json and token.json are valid

2. **GitHub Actions Failures:**
   - Check that all secrets are properly configured
   - Verify secret names match exactly
   - Check workflow logs for specific error messages

3. **API Rate Limits:**
   - Some APIs have rate limits
   - The workflow includes retries and error handling

### Testing

```bash
# Test API connections
python -c "from src.api_clients import get_zen_quote; print(get_zen_quote())"

# Test Gmail service (requires credentials)
python -c "from src.gmail_service import GmailService; print('Gmail service imported successfully')"

# Run dry-run via GitHub Actions
# Use "Test Newsletter (Manual)" workflow with dry_run=true
```

### Logs

- Local logs: `logs/` directory and `main.log`
- GitHub Actions: Available in the Actions tab, also uploaded as artifacts on failure

## License

This project is for personal use. Please respect API terms of service and rate limits.

## Contributing

Feel free to open issues or submit pull requests for improvements!
