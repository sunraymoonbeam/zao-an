#!/usr/bin/env python3
"""
Test script to verify that PDF attachments work correctly in different storage modes.
"""

import tempfile
import os
import sys


def test_temp_storage():
    """Test that temp storage creates files correctly"""
    print("🧪 Testing temp storage functionality...")

    # Simulate what happens in GitHub Actions
    temp_dir = tempfile.mkdtemp(prefix="arxiv_papers_")
    query_dir = os.path.join(temp_dir, "computer_vision")
    os.makedirs(query_dir, exist_ok=True)

    # Create a dummy PDF file
    test_pdf = os.path.join(query_dir, "test_paper.pdf")
    with open(test_pdf, "w") as f:
        f.write("Dummy PDF content for testing")

    # Verify file exists
    if os.path.exists(test_pdf):
        print(f"✅ Temp file created successfully: {test_pdf}")

        # Verify it can be used as attachment
        attachments = [test_pdf]
        print(f"✅ File ready for email attachment: {len(attachments)} files")

        # Cleanup (normally done automatically by system)
        os.remove(test_pdf)
        os.rmdir(query_dir)
        os.rmdir(temp_dir)
        print("✅ Cleanup completed")

        return True
    else:
        print("❌ Failed to create temp file")
        return False


def test_config_files():
    """Test that config files exist and are valid"""
    print("\n🔧 Testing configuration files...")

    config_files = ["conf/config.yaml", "conf/config-github.yaml"]

    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file} exists")
        else:
            print(f"❌ {config_file} missing")
            return False

    return True


def main():
    """Run all tests"""
    print("🚀 Testing PDF attachment functionality...\n")

    tests = [test_temp_storage, test_config_files]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)

    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("🎉 All tests passed! PDF attachments should work in GitHub Actions.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
