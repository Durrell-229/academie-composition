"""
Verify cloud storage configuration.
Run this to test if cloud storage is properly configured.

Usage:
    python verify_cloud_storage.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

from django.conf import settings

print("☁️  Cloud Storage Configuration Check")
print("=" * 50)

# Check which storage backend is active
using_s3 = os.environ.get('USE_S3_STORAGE', 'False').lower() == 'true'
using_cloudinary = os.environ.get('USE_CLOUDINARY_STORAGE', 'False').lower() == 'true'

if using_cloudinary:
    print("\n✅ Cloudinary storage is ENABLED")
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
    api_key = os.environ.get('CLOUDINARY_API_KEY', '')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET', '')

    if cloud_name and api_key and api_secret:
        print(f"   Cloud Name: {cloud_name}")
        print(f"   API Key: {api_key[:4]}...{api_key[-4:] if len(api_key) > 8 else '****'}")
        print("   API Secret: [CONFIGURED]")
        print("\n✅ All Cloudinary credentials are set!")
        print(f"   Files will be stored at: https://res.cloudinary.com/{cloud_name}/")
    else:
        print("\n❌ Missing Cloudinary credentials!")
        if not cloud_name:
            print("   - CLOUDINARY_CLOUD_NAME is not set")
        if not api_key:
            print("   - CLOUDINARY_API_KEY is not set")
        if not api_secret:
            print("   - CLOUDINARY_API_SECRET is not set")
        print("\n   Please add these environment variables in Render.")
        sys.exit(1)

elif using_s3:
    print("\n✅ AWS S3 storage is ENABLED")
    bucket = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
    region = os.environ.get('AWS_S3_REGION_NAME', '')
    access_key = os.environ.get('AWS_ACCESS_KEY_ID', '')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '')

    if bucket and region and access_key and secret_key:
        print(f"   Bucket: {bucket}")
        print(f"   Region: {region}")
        print(f"   Access Key: {access_key[:8]}...")
        print("   Secret Key: [CONFIGURED]")
        print("\n✅ All S3 credentials are set!")
        print(f"   Files will be stored at: https://{bucket}.s3.{region}.amazonaws.com/")
    else:
        print("\n❌ Missing S3 credentials!")
        if not bucket:
            print("   - AWS_STORAGE_BUCKET_NAME is not set")
        if not region:
            print("   - AWS_S3_REGION_NAME is not set")
        if not access_key:
            print("   - AWS_ACCESS_KEY_ID is not set")
        if not secret_key:
            print("   - AWS_SECRET_ACCESS_KEY is not set")
        print("\n   Please add these environment variables in Render.")
        sys.exit(1)
else:
    print("\n⚠️  Cloud storage is NOT enabled!")
    print("   Files are being stored locally (will be deleted on deployment).")
    print("\n   To enable cloud storage:")
    print("   1. Sign up for Cloudinary (free): https://cloudinary.com/users/register/free")
    print("   2. Add environment variables in Render:")
    print("      - USE_CLOUDINARY_STORAGE=true")
    print("      - CLOUDINARY_CLOUD_NAME=your_cloud_name")
    print("      - CLOUDINARY_API_KEY=your_api_key")
    print("      - CLOUDINARY_API_SECRET=your_api_secret")
    print("\n   See docs/CLOUD_STORAGE_SETUP.md for full instructions.")

print("\n" + "=" * 50)
print("Current Media Settings:")
print(f"  MEDIA_URL: {settings.MEDIA_URL}")
print(f"  MEDIA_ROOT: {settings.MEDIA_ROOT}")
if hasattr(settings, 'DEFAULT_FILE_STORAGE'):
    print(f"  DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")
else:
    print(f"  DEFAULT_FILE_STORAGE: [Using default Django storage]")
