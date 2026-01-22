# Quick Reference Guide

## 🚀 Getting Started (3 Steps)

```bash
# Step 1: Setup
./setup.sh

# Step 2: Activate environment
source venv/bin/activate

# Step 3: Run scraper
python main.py
```

**Output:** `output/High_Conversion_Job_Leads_YYYY-MM-DD.xlsx`

---

## 📋 Common Commands

| Task | Command |
|------|---------|
| Run scraper | `python main.py` |
| Test setup | `python test_scraper.py` |
| Add companies | `python expand_companies.py` |
| Validate URLs | `python validate_urls.py` |
| Check company count | `python -c "import json; print(len(json.load(open('companies.json'))))"` |

---

## 🎯 What Gets Scraped

### ✅ INCLUDED
- Backend Engineer
- Software Engineer (SDE I/II)
- Platform Engineer
- Full Stack (backend-heavy)
- 0-3 years experience
- India locations only
- Java/Spring/Microservices stack

### ❌ EXCLUDED
- Senior/Staff/Principal roles
- Internships
- Frontend-only roles
- QA/DevOps-only roles
- >3 years experience
- Non-India locations
- Job boards (LinkedIn, Indeed, etc.)

---

## 📊 Current Stats

| Metric | Value |
|--------|-------|
| Total Companies | 155+ |
| Tier-1 GCCs | 35+ |
| Unicorns | 60+ |
| Series B-D | 60+ |
| Companies/Run | ~120 |
| Rotation Cycle | 8 days |
| Expected Jobs/Day | 20-50 |

---

## 🔧 Quick Customization

### Change scraping volume
**File:** `config.py`
```python
COMPANIES_PER_RUN = 120  # Change this number
```

### Add more locations
**File:** `config.py`
```python
TARGET_LOCATIONS = [
    "bangalore", "hyderabad", "pune",
    "your_city_here"  # Add here
]
```

### Adjust experience range
**File:** `filters.py` → `is_valid_experience()` function

### Add tech keywords
**File:** `config.py`
```python
TECH_STACK_KEYWORDS = [
    "java", "spring boot",
    "your_tech_here"  # Add here
]
```

---

## 🤖 Automation Setup

### GitHub Actions (Easiest)
1. Push code to GitHub
2. Done! Runs daily at 8:30 AM IST

### Cron (Local)
```bash
crontab -e
# Add this line:
0 9 * * * cd /Users/rishaadkhan/Documents/jobscrap && /Users/rishaadkhan/Documents/jobscrap/venv/bin/python main.py
```

---

## 📁 Output Format

**File:** `High_Conversion_Job_Leads_2024-01-15.xlsx`

| Column | Example |
|--------|---------|
| Company Name | Google India |
| Company Type | Tier-1 GCC |
| Job Title | Software Engineer - Backend |
| Experience Range | 0-2 years |
| Location | Bangalore, India |
| Job ID | 12345 |
| Posted Date | 2024-01-10 |
| Official Apply Link | https://... |
| Career Portal URL | https://... |
| Full Job Description | Looking for... |
| Scraped Timestamp | 2024-01-15 09:30:00 |

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| No jobs found | Check internet connection, validate URLs |
| Import errors | Run `pip install -r requirements.txt` |
| Permission denied | Run `chmod +x setup.sh` |
| Too many duplicates | Delete `scraper_state.json` and restart |
| Script too slow | Reduce `COMPANIES_PER_RUN` in config.py |

---

## 📈 Scaling to 1000+ Companies

**Current:** 155 companies
**Target:** 1000+ companies

### How to add more:
1. Edit `expand_companies.py`
2. Add companies to `ADDITIONAL_COMPANIES` list:
```python
{"name": "Company", "type": "Tier-1 GCC", "career_url": "https://..."}
```
3. Run: `python expand_companies.py`

### Company sources:
- Tier-1 GCCs: Tech giants with India offices
- Unicorns: $1B+ valuation startups
- Series B-D: Well-funded startups

---

## 🎯 Quality Checklist

Before running in production:

- [ ] Tested with `python test_scraper.py`
- [ ] Validated URLs with `python validate_urls.py`
- [ ] Reviewed sample output Excel file
- [ ] Adjusted filters if needed
- [ ] Set up automation (GitHub Actions or cron)
- [ ] Verified state file is being saved

---

## 📞 Quick Help

**File not found?**
→ Make sure you're in `/Users/rishaadkhan/Documents/jobscrap`

**Module not found?**
→ Activate venv: `source venv/bin/activate`

**No output generated?**
→ Check if any companies were scraped successfully

**Want more jobs?**
→ Add more companies or relax filters

---

## 🎓 File Purposes

| File | Purpose |
|------|---------|
| `main.py` | Runs everything |
| `scraper.py` | Fetches jobs from websites |
| `filters.py` | Decides which jobs to keep |
| `state_manager.py` | Tracks what's been scraped |
| `exporter.py` | Creates Excel file |
| `config.py` | All settings in one place |
| `companies.json` | List of companies to scrape |

---

## ⚡ Pro Tips

1. **Start small:** Test with 10-20 companies first
2. **Monitor output:** Check first few Excel files for quality
3. **Adjust filters:** Based on what you see in output
4. **Expand gradually:** Add 50-100 companies at a time
5. **Validate URLs:** Run `validate_urls.py` after adding companies
6. **Backup state:** Keep `scraper_state.json` backed up

---

## 🎉 Success Indicators

You'll know it's working when:
- ✓ Excel file appears in `output/` folder
- ✓ File has 20-50 jobs (with 155 companies)
- ✓ Jobs are backend-focused
- ✓ Experience is 0-3 years
- ✓ Locations are in India
- ✓ No duplicates across runs

---

**Need more help?** Check `DOCUMENTATION.md` for detailed guide.
