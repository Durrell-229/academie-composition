# Quick Start: Enable Cloud Storage (5 minutes)

## The Problem
Right now, files uploaded to Render are **lost** every time you deploy:
- ❌ Epreuves (exam PDFs)
- ❌ Corrigés (answer keys)
- ❌ Student copies
- ❌ Bulletins (report cards)

## The Solution
Enable **Cloudinary** cloud storage (FREE, no credit card needed):

### Step 1: Create Cloudinary Account (2 min)

1. Go to: **https://cloudinary.com/users/register/free**
2. Fill in:
   - Email
   - Password
   - Check "I agree to terms"
3. Click **"Sign Up"**
4. Check your email and click verification link

### Step 2: Copy Credentials (1 min)

After logging in to [Cloudinary Dashboard](https://console.cloudinary.com/):

At the top of the page, you'll see:
```
Cloud Name: dxxxxxxx
API Key: 123456789012345
API Secret: abcdefghijklmnopqrst
```

**Copy all 3 values!**

### Step 3: Add to Render (2 min)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click your service: **academie-composition**
3. Go to **Environment** tab
4. Click **Edit** on Environment Variables
5. Add these 4 new variables:

| Key | Value |
|-----|-------|
| `USE_CLOUDINARY_STORAGE` | `true` |
| `CLOUDINARY_CLOUD_NAME` | (your cloud name from step 2) |
| `CLOUDINARY_API_KEY` | (your API key from step 2) |
| `CLOUDINARY_API_SECRET` | (your API secret from step 2) |

6. Click **Save**

### Step 4: Deploy (1 min)

1. Push this code to GitHub:
   ```bash
   git push origin main
   ```

2. Render will automatically deploy
3. Wait 2-3 minutes for deployment to complete

### Step 5: Test (30 sec)

1. Go to your app: https://academie-composition.onrender.com
2. Login as admin
3. Go to "Validation Épreuves"
4. Upload a test epreuve
5. Click "Voir l'épreuve"
6. ✅ It should work!

**Bonus:** Deploy again - the file will STILL be there! 🎉

---

## What Gets Stored in Cloud?

Once enabled, these files are saved forever:

- 📄 **Epreuves** - Exam PDFs uploaded by professors
- 📝 **Corrigés Types** - Answer keys
- 📋 **Student Copies** - Uploaded exam answers
- 📊 **Bulletins** - Report cards with digital stamps
- 🎓 **Certificates** - Achievement certificates

## Free Tier Limits

Cloudinary FREE tier includes:
- ✅ **25 GB** storage
- ✅ **25 GB** bandwidth/month
- ✅ Enough for **~1000 students**

After that, paid plans start at $99/month.

## Need Help?

See full documentation: `docs/CLOUD_STORAGE_SETUP.md`

Run verification script:
```bash
python verify_cloud_storage.py
```
