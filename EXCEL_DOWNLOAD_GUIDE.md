# 📥 WHERE TO DOWNLOAD EXCEL FILES FROM GITHUB

## 🎯 CURRENT SETUP: GitHub Actions Artifacts

When you run the scraper on GitHub Actions, Excel files are uploaded as **Artifacts**.

---

## 📍 HOW TO DOWNLOAD EXCEL FILES

### Method 1: GitHub Actions Artifacts (Current Setup)

**Step 1: Go to your GitHub repository**
```
https://github.com/YOUR_USERNAME/YOUR_REPO
```

**Step 2: Click on "Actions" tab**

**Step 3: Click on the latest workflow run**
- You'll see "Daily Job Scraper" runs listed
- Click on the most recent one

**Step 4: Scroll down to "Artifacts" section**
- You'll see: `job-leads-123` (number varies)
- Click to download ZIP file

**Step 5: Extract ZIP**
- Contains: `High_Conversion_Job_Leads_YYYY-MM-DD.xlsx`

**Retention:** Files kept for 30 days

---

## 🚀 BETTER OPTIONS FOR PRODUCTION

### Option 1: Commit Excel to Repository (EASIEST)

**Pros:**
- ✓ Easy to access
- ✓ Version history
- ✓ No expiration

**Cons:**
- ✗ Increases repo size
- ✗ Not ideal for daily files

**Setup:**
Update `.github/workflows/scraper.yml`:

```yaml
- name: Commit Excel output
  run: |
    git config --local user.email "action@github.com"
    git config --local user.name "GitHub Action"
    git add output/*.xlsx
    git add scraper_state.json
    git commit -m "Add job leads $(date +%Y-%m-%d) [skip ci]"
    git push
```

**Download:**
- Go to repository
- Navigate to `output/` folder
- Click on Excel file
- Click "Download" button

---

### Option 2: Upload to Google Drive (RECOMMENDED)

**Pros:**
- ✓ Automatic backup
- ✓ Easy sharing
- ✓ No repo bloat
- ✓ Accessible from anywhere

**Setup:**

1. **Create Google Drive API credentials**
   - Go to: https://console.cloud.google.com
   - Create project
   - Enable Google Drive API
   - Create Service Account
   - Download JSON key

2. **Add to GitHub Secrets**
   - Go to: Settings → Secrets → Actions
   - Add secret: `GDRIVE_CREDENTIALS` (paste JSON content)
   - Add secret: `GDRIVE_FOLDER_ID` (your folder ID)

3. **Update workflow:**

```yaml
- name: Upload to Google Drive
  env:
    GDRIVE_CREDENTIALS: ${{ secrets.GDRIVE_CREDENTIALS }}
    GDRIVE_FOLDER_ID: ${{ secrets.GDRIVE_FOLDER_ID }}
  run: |
    pip install pydrive2
    python upload_to_gdrive.py
```

4. **Create upload script** (I'll create this below)

**Download:**
- Open Google Drive
- Go to your folder
- Download Excel file

---

### Option 3: Email Excel File

**Pros:**
- ✓ Delivered to inbox
- ✓ No manual download
- ✓ Can email to multiple people

**Setup:**

1. **Add email secrets to GitHub**
   - `EMAIL_TO`: recipient@example.com
   - `EMAIL_FROM`: sender@gmail.com
   - `EMAIL_PASSWORD`: app password

2. **Update workflow:**

```yaml
- name: Email Excel file
  env:
    EMAIL_TO: ${{ secrets.EMAIL_TO }}
    EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
    EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
  run: |
    python email_excel.py
```

3. **Create email script** (I'll create this below)

**Download:**
- Check your email
- Download attachment

---

### Option 4: Upload to AWS S3

**Pros:**
- ✓ Scalable
- ✓ Cheap storage
- ✓ Can generate public URLs

**Setup:**

1. **Add AWS secrets to GitHub**
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_BUCKET_NAME`

2. **Update workflow:**

```yaml
- name: Upload to S3
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    AWS_BUCKET_NAME: ${{ secrets.AWS_BUCKET_NAME }}
  run: |
    pip install boto3
    python upload_to_s3.py
```

3. **Create S3 upload script** (I'll create this below)

**Download:**
- Access S3 bucket
- Download file
- Or use pre-signed URL

---

### Option 5: Slack/Discord Notification with Link

**Pros:**
- ✓ Team notification
- ✓ Instant alerts
- ✓ Can include summary

**Setup:**

1. **Add webhook URL to GitHub secrets**
   - `SLACK_WEBHOOK_URL` or `DISCORD_WEBHOOK_URL`

2. **Update workflow:**

```yaml
- name: Notify Slack
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
  run: |
    python notify_slack.py
```

---

## 📊 COMPARISON TABLE

| Method | Ease | Cost | Access | Best For |
|--------|------|------|--------|----------|
| GitHub Artifacts | Easy | Free | 30 days | Testing |
| Commit to Repo | Easy | Free | Forever | Small files |
| Google Drive | Medium | Free | Forever | Personal use |
| Email | Medium | Free | Forever | Daily delivery |
| AWS S3 | Medium | Cheap | Forever | Production |
| Slack/Discord | Medium | Free | N/A | Team alerts |

---

## 🎯 RECOMMENDED SETUP

### For Personal Use:
**Google Drive** - Easy access, no expiration

### For Team Use:
**AWS S3 + Slack** - Scalable + notifications

### For Simple Setup:
**Commit to Repo** - Zero configuration

---

## 📝 CURRENT WORKFLOW EXPLANATION

Your current `.github/workflows/scraper.yml`:

```yaml
- name: Upload Excel output
  uses: actions/upload-artifact@v3
  with:
    name: job-leads-${{ github.run_number }}
    path: output/*.xlsx
    retention-days: 30
```

**What this does:**
1. Runs scraper
2. Generates Excel in `output/` folder
3. Uploads as artifact
4. Keeps for 30 days
5. Auto-deletes after 30 days

**To download:**
1. GitHub repo → Actions tab
2. Click latest run
3. Scroll to Artifacts
4. Download ZIP

---

## 🚀 NEXT: I'll create scripts for each option
