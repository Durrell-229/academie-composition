# Cloud Storage Setup Guide

## Why Cloud Storage?

Render uses an **ephemeral filesystem** - files uploaded between deployments are **deleted** after each new deployment. To persist files permanently (epreuves, copies, bulletins, certificates), you need cloud storage.

## Options Available

### Option 1: Cloudinary (Recommended - Easiest, FREE, No Credit Card)

**Best for**: Quick setup, free tier, no payment info needed

1. **Create Account**
   - Go to https://cloudinary.com/users/register/free
   - Sign up with email (no credit card required)
   - Verify email

2. **Get Credentials**
   - Login to Cloudinary Dashboard
   - Copy these values from the top:
     - `Cloud Name` (e.g., `dxxxxx`)
     - `API Key` (number)
     - `API Secret` (click "Reveal" to see)

3. **Add to Render Environment Variables**
   - Go to Render Dashboard → Your Service → Environment
   - Add these 3 variables:
     ```
     USE_CLOUDINARY_STORAGE=true
     CLOUDINARY_CLOUD_NAME=your_cloud_name_here
     CLOUDINARY_API_KEY=your_api_key_here
     CLOUDINARY_API_SECRET=your_api_secret_here
     ```

4. **Deploy**
   - Push new commit to GitHub
   - Render will automatically install dependencies
   - Files will now be stored in Cloudinary forever!

### Option 2: AWS S3 / DigitalOcean Spaces (More Control)

**Best for**: Full control, enterprise use, already have AWS account

#### AWS S3:

1. **Create S3 Bucket**
   - Go to AWS Console → S3
   - Create bucket (e.g., `academie-composition-media`)
   - Set region (e.g., `us-east-1`)

2. **Create IAM User**
   - Go to IAM → Users → Create User
   - Attach policy: `AmazonS3FullAccess`
   - Copy `Access Key ID` and `Secret Access Key`

3. **Add to Render Environment Variables**
   ```
   USE_S3_STORAGE=true
   AWS_STORAGE_BUCKET_NAME=your_bucket_name
   AWS_S3_REGION_NAME=your_region
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   ```

#### DigitalOcean Spaces (S3-compatible, cheaper):

1. **Create Space**
   - Go to DigitalOcean → Spaces
   - Create Space (e.g., `academie-media`)
   - Copy endpoint URL

2. **Generate API Keys**
   - Go to API → Keys
   - Generate new key pair

3. **Add to Render Environment Variables**
   ```
   USE_S3_STORAGE=true
   AWS_STORAGE_BUCKET_NAME=your_space_name
   AWS_S3_REGION_NAME=nyc3 (or your region)
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   AWS_S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
   ```

## What Files Will Be Stored?

Once cloud storage is enabled, these files will be persisted:

- ✅ **Epreuves** (`devoirs/epreuves/`) - PDF files uploaded by professors
- ✅ **Corrigés Types** (`devoirs/corriges/`) - Answer keys
- ✅ **Student Copies** (tracked in database) - Uploaded exam copies
- ✅ **Bulletins** (`bulletins_devoirs/`) - Report cards with digital stamps
- ✅ **Certificates** (`certificats/`) - Achievement certificates

## Testing Locally

To test cloud storage locally:

1. Create `.env` file in project root:
   ```env
   USE_CLOUDINARY_STORAGE=true
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   ```

2. Run:
   ```bash
   pip install django-cloudinary-storage cloudinary
   python manage.py runserver
   ```

3. Upload a test file - it should appear in your Cloudinary dashboard

## Verification

After deploying with cloud storage enabled:

1. Go to admin validation page
2. Click "Voir l'épreuve"
3. File should load from `https://res.cloudinary.com/...` (Cloudinary)
4. Deploy again - file should STILL be accessible!

## Cost Estimates

- **Cloudinary Free Tier**: 25 GB storage, 25 GB bandwidth/month (enough for ~1000 students)
- **AWS S3**: ~$0.023/GB/month (pennies for small usage)
- **DigitalOcean Spaces**: $5/month for 250 GB

## Migration Note

Existing files on Render's local filesystem **cannot be recovered** after deployment. They need to be re-uploaded:
- Professors will need to resubmit epreuves/corrigés
- This is a one-time migration

## Troubleshooting

**Error: "ModuleNotFoundError: No module named 'cloudinary'"**
- Make sure `django-cloudinary-storage` and `cloudinary` are in `requirements.txt`
- Check Render build logs

**Files still 404 after enabling cloud storage**
- Verify environment variables are set correctly in Render
- Check Render logs for storage backend errors
- Ensure `USE_CLOUDINARY_STORAGE=true` (case-sensitive)

**Cloudinary dashboard shows no uploads**
- Files are being uploaded to wrong folder
- Check `upload_to` parameter in model FileField definitions
