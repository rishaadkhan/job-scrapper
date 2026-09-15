# 🚀 Quick Reference: Adding & Managing Target Companies

## 📊 Current Status
- **Total Tracked Companies:** 590+
- **Direct Public ATS Support:** Greenhouse, Lever, Ashby, SmartRecruiters, Workday CXS
- **Data Safety:** Zero third-party scraping (No LinkedIn, Indeed, or Naukri)
- **Persistence:** Synchronized in both `companies.json` and SQLite database (`jobscraper.db`)

---

## ⚡ Quick Add Commands

### 1. Web Dashboard UI
Visit [http://localhost:5173/companies](http://localhost:5173/companies) and click **+ Add Company**.

### 2. Import CSV File
```bash
python import_csv.py my_companies.csv
```

### 3. Run Batch Expansion
```bash
python expand_companies.py
# Or process all expansion files:
python import_all.py
```

### 4. Validate All Company URLs & ATS Endpoints
```bash
python validate_urls.py --limit 25
```

---

## 📋 CSV Format Example
```csv
name,type,career_url,ats,ats_token
Databricks,Tier-1 GCC,https://boards.greenhouse.io/databricks,greenhouse,databricks
Postman,Unicorn,https://jobs.lever.co/postman,lever,postman
Linear,Unicorn,https://jobs.ashbyhq.com/linear,ashby,linear
```

---

## 📖 Complete Documentation
For detailed schema fields, REST API endpoints, and ATS token extraction guides, see:
[`ADDING_COMPANIES_GUIDE.md`](file:///Users/rishaadkhan/DevelopmentCoding/jobscrap/ADDING_COMPANIES_GUIDE.md)
