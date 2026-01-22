# 🚀 QUICK SETUP: Excel Download Options

## 📥 CURRENT SETUP (Default)

**Method:** GitHub Actions Artifacts

**How to download:**
1. Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`
2. Click latest "Daily Job Scraper" run
3. Scroll to "Artifacts" section
4. Download ZIP file
5. Extract to get Excel

**Retention:** 30 days

---

## ✅ EASIEST OPTION: Commit to Repository

### Setup (2 minutes):

1. **Replace `.github/workflows/scraper.yml` with:**
```bash
cp .github/workflows/scraper_with_options.yml .github/workflows/scraper.yml
```

2. **Edit `.github/workflows/scraper.yml`:**
   - Uncomment lines 30-37 (Commit to Repository section)
   - Comment out lines 22-27 (Artifact section)

3. **Commit and push:**
```bash
git add .github/workflows/scraper.yml
git commit -m "Enable Excel commit to repo"
git push
```

### Download:
1. Go to repository
2. Click `output/` folder
3. Click Excel file
4. Click "Download" button

**Pros:** Zero configuration, easy access
**Cons:** Increases repo size over time

---

## 📧 RECOMMENDED: Email Delivery

### Setup (5 minutes):

1. **Get Gmail App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Generate app password
   - Copy the 16-character password

2. **Add GitHub Secrets:**
   - Go to: Repository → Settings → Secrets → Actions
   - Click "New repository secret"
   - Add these 3 secrets:
     - `EMAIL_TO`: your-email@gmail.com
     - `EMAIL_FROM`: sender-email@gmail.com
     - `EMAIL_PASSWORD`: (16-char app password)

3. **Update workflow:**
   - Edit `.github/workflows/scraper.yml`
   - Uncomment lines 47-54 (Email section)

4. **Commit and push:**
```bash
git add .github/workflows/scraper.yml
git commit -m "Enable email delivery"
git push
```

### Download:
- Check your email inbox
- Download attachment

**Pros:** Delivered automatically, no manual download
**Cons:** Requires Gmail setup

---

## ☁️ BEST FOR TEAMS: Google Drive

### Setup (10 minutes):

1. **Create Google Cloud Project:**
   - Go to: https://console.cloud.google.com
   - Create new project
   - Enable Google Drive API

2. **Create Service Account:**
   - Go to: IAM & Admin → Service Accounts
   - Create service account
   - Download JSON key file

3. **Create Google Drive Folder:**
   - Create folder in Google Drive
   - Share with service account email
   - Copy folder ID from URL

4. **Add GitHub Secrets:**
   - `GDRIVE_CREDENTIALS`: (paste entire JSON content)
   - `GDRIVE_FOLDER_ID`: (folder ID from URL)

5. **Update workflow:**
   - Uncomment lines 39-45 (Google Drive section)

6. **Commit and push**

### Download:
- Open Google Drive folder
- Download Excel file

**Pros:** Team access, no expiration, organized
**Cons:** Requires Google Cloud setup

---

## 💰 PRODUCTION: AWS S3

### Setup (10 minutes):

1. **Create S3 Bucket:**
   - Go to AWS Console → S3
   - Create bucket (e.g., `my-job-scraper`)
   - Note bucket name

2. **Create IAM User:**
   - Go to IAM → Users → Add user
   - Enable programmatic access
   - Attach policy: `AmazonS3FullAccess`
   - Save access key and secret key

3. **Add GitHub Secrets:**
   - `AWS_ACCESS_KEY_ID`: (your access key)
   - `AWS_SECRET_ACCESS_KEY`: (your secret key)
   - `AWS_BUCKET_NAME`: (your bucket name)

4. **Update workflow:**
   - Uncomment lines 56-63 (AWS S3 section)

5. **Commit and push**

### Download:
- Access S3 bucket
- Download file
- Or use pre-signed URL from logs

**Pros:** Scalable, cheap, reliable
**Cons:** Requires AWS account

---

## 📊 COMPARISON

| Option | Setup Time | Cost | Best For |
|--------|------------|------|----------|
| **Artifacts** (current) | 0 min | Free | Testing |
| **Commit to Repo** | 2 min | Free | Personal |
| **Email** | 5 min | Free | Daily delivery |
| **Google Drive** | 10 min | Free | Teams |
| **AWS S3** | 10 min | ~$0.01/month | Production |

---

## 🎯 RECOMMENDATION

### For You (Personal Use):
**Option 1: Commit to Repository**
- Easiest setup (2 minutes)
- Direct download from GitHub
- No external services needed

### For Team:
**Option 2: Google Drive**
- Easy sharing
- Organized storage
- No expiration

### For Production:
**Option 3: AWS S3 + Email**
- Scalable
- Reliable
- Automated delivery

---

## 🔧 QUICK COMMANDS

### Enable Commit to Repo:
```bash
# Edit workflow file
nano .github/workflows/scraper.yml

# Uncomment lines 30-37
# Comment lines 22-27

# Commit
git add .github/workflows/scraper.yml
git commit -m "Enable Excel commit"
git push
```

### Check Current Setup:
```bash
cat .github/workflows/scraper.yml | grep -A 5 "Upload Excel"
```

### Test Locally:
```bash
python main.py
ls -lh output/
```

---

## 📝 NOTES

1. **Multiple Options:** You can enable multiple options simultaneously
2. **Artifacts Always Work:** Keep artifacts as backup
3. **State File:** Always committed automatically
4. **File Size:** Excel files are typically 10-50 KB

---

## 🆘 TROUBLESHOOTING

**Q: Where are artifacts?**
A: GitHub repo → Actions → Click run → Scroll to Artifacts

**Q: How long are artifacts kept?**
A: 30 days (configurable in workflow)

**Q: Can I download without GitHub login?**
A: No, artifacts require GitHub login. Use commit/email/S3 for public access

**Q: Excel not generated?**
A: Check Actions logs for errors

---

## ✅ NEXT STEPS

1. Choose your preferred option
2. Follow setup instructions above
3. Test by running workflow manually
4. Check download location

**Current:** Artifacts (30 days)
**Recommended:** Commit to Repo (easiest) or Email (automated)
