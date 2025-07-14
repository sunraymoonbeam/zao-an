#!/usr/bin/env python3
"""
Test script to validate that your local credentials work before setting up GitHub secrets.
"""

import json
import os
import sys


def test_credentials_file():
    """Test that credentials.json is valid"""
    print("🔍 Testing credentials.json...")

    if not os.path.exists("credentials.json"):
        print("❌ credentials.json not found")
        return False

    try:
        with open("credentials.json", "r") as f:
            creds = json.load(f)

        # Check required fields
        if "installed" in creds:
            inner_required = ["client_id", "client_secret", "auth_uri", "token_uri"]
            for field in inner_required:
                if field not in creds["installed"]:
                    print(f"❌ Missing field in credentials: installed.{field}")
                    return False

        print("✅ credentials.json is valid")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ credentials.json is not valid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials.json: {e}")
        return False


def test_token_file():
    """Test that token.json is valid"""
    print("🔍 Testing token.json...")

    if not os.path.exists("token.json"):
        print("❌ token.json not found - run script locally first to generate it")
        return False

    try:
        with open("token.json", "r") as f:
            token = json.load(f)

        # Check required fields
        required_fields = ["token", "refresh_token", "token_uri"]
        for field in required_fields:
            if field not in token:
                print(f"❌ Missing field in token: {field}")
                return False

        print("✅ token.json is valid")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ token.json is not valid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading token.json: {e}")
        return False


def test_env_file():
    """Test that .env file has API key"""
    print("🔍 Testing .env file...")

    if not os.path.exists(".env"):
        print("❌ .env file not found")
        return False

    with open(".env", "r") as f:
        content = f.read()

    if "GOOGLE_MAPS_API_KEY=" not in content:
        print("❌ GOOGLE_MAPS_API_KEY not found in .env")
        return False

    # Extract API key
    for line in content.strip().split("\n"):
        if line.startswith("GOOGLE_MAPS_API_KEY="):
            api_key = line.split("=", 1)[1]
            if len(api_key) < 10:
                print("❌ GOOGLE_MAPS_API_KEY appears to be too short")
                return False
            print("✅ .env file is valid")
            return True

    return False


def format_for_github_secrets():
    """Output the proper format for GitHub secrets"""
    print("\n🚀 GitHub Secrets Setup:")
    print("=" * 50)

    if os.path.exists("credentials.json"):
        with open("credentials.json", "r") as f:
            creds_content = f.read().strip()
        print("GMAIL_CREDENTIALS_JSON:")
        print(creds_content)
        print()

    if os.path.exists("token.json"):
        with open("token.json", "r") as f:
            token_content = f.read().strip()
        print("GMAIL_TOKEN_JSON:")
        print(token_content)
        print()

    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.strip().startswith("GOOGLE_MAPS_API_KEY="):
                    api_key = line.strip().split("=", 1)[1]
                    print("GOOGLE_MAPS_API_KEY:")
                    print(api_key)
                    print()


def main():
    """Run all validation tests"""
    print("🧪 Local Credentials Validation")
    print("=" * 40)

    tests = [test_credentials_file, test_token_file, test_env_file]

    results = []
    for test in tests:
        try:
            results.append(test())
            print()
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
            print()

    print(f"📊 Test Results: {sum(results)}/{len(results)} passed")

    if all(results):
        format_for_github_secrets()
        print("💡 Copy the values above to your GitHub repository secrets")
        print("💡 Make sure to copy the exact JSON (no extra spaces/newlines)")
        return 0
    else:
        print("⚠️  Fix the issues above before setting up GitHub secrets")
        return 1


if __name__ == "__main__":
    sys.exit(main())
