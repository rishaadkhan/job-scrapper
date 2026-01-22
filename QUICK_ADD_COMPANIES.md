# 🚀 QUICK START: Adding 1500+ Companies

## ✅ CURRENT STATUS
- **Starting:** 155 companies
- **After import:** 351 companies
- **Added:** 196 companies
- **Target:** 1500+ companies
- **Remaining:** 1149 companies to add

---

## 📊 WHAT WAS JUST ADDED

### Tier-1 GCCs (40 new):
- Stripe, Shopify, Slack, Zoom, Dropbox, Box
- Databricks, Snowflake, Confluent, MongoDB, Elastic, Redis
- HashiCorp, GitLab, Splunk, ServiceNow, Workday
- Zendesk, HubSpot, Twilio, Okta, Datadog, PagerDuty
- Cloudflare, Palo Alto Networks, CrowdStrike, Zscaler
- Spotify, Klarna, Revolut, Booking.com, Expedia

### Indian Startups (156 new):
- Gaming: Dream11, MPL, WinZO, Zupee
- Social: Hike, Glance, InMobi, Koo, Josh, Moj, Chingari
- Edtech: BYJU'S, upGrad, Eruditus, Scaler, Coding Ninjas
- Healthtech: PharmEasy, 1mg, Practo, Cure.fit, HealthifyMe
- Logistics: Shadowfax, Ecom Express, Xpressbees, Porter
- E-commerce: Snapdeal, Pepperfry, Myntra, Ajio, Nykaa Fashion
- Proptech: Housing.com, 99acres, MagicBricks, Nestaway, Stanza Living
- Mobility: Rapido, Bounce, Yulu, Spinny, CarDekho, Droom
- Travel: OYO, Treebo, MakeMyTrip, Goibibo, Cleartrip, ixigo
- B2B: OfBusiness, Jumbotail, Ninjacart, WayCool, DeHaat
- HR Tech: Keka, GreytHR, SumHR, Darwinbox, Zimyo
- Marketing: CleverTap, WebEngage, MoEngage, Netcore
- Dev Tools: LambdaTest, Testsigma, Hevo Data, Atlan, Hasura
- AI/ML: Haptik, Yellow.ai, Verloop.io, Uniphore, Skit.ai
- Cleantech: Ather Energy, Ola Electric, ReNew Power
- Fintech: Digit Insurance, Upstox, Angel One, Smallcase, ET Money

---

## 🎯 HOW TO ADD MORE COMPANIES

### METHOD 1: Create Your Own CSV (EASIEST)

1. **Create a CSV file** (e.g., `my_companies.csv`):
```csv
name,type,career_url
Company Name,Tier-1 GCC,https://company.com/careers
Another Company,Unicorn,https://another.com/jobs
```

2. **Import it:**
```bash
python import_csv.py my_companies.csv
```

### METHOD 2: Edit expand_companies.py

1. **Open expand_companies.py**
2. **Add to ADDITIONAL_COMPANIES list:**
```python
ADDITIONAL_COMPANIES = [
    {"name": "New Company", "type": "Unicorn", "career_url": "https://..."},
    # Add more here
]
```
3. **Run:**
```bash
python expand_companies.py
```

### METHOD 3: Direct JSON Edit

1. **Open companies.json**
2. **Add entries:**
```json
{
  "name": "Company Name",
  "type": "Tier-1 GCC",
  "career_url": "https://..."
}
```
3. **Validate:**
```bash
python -c "import json; json.load(open('companies.json')); print('✓ Valid')"
```

---

## 📋 WHERE TO FIND 1149 MORE COMPANIES

### 1. IT Services Companies (200+)
- TCS, Infosys, Wipro, HCL, Tech Mahindra
- LTI, Mindtree, Mphasis, Hexaware, Cyient
- Persistent, KPIT, Zensar, Mastek, Sonata
- Thoughtworks, Hashedin, Incedo, Sigmoid
- Search: "IT services companies India"

### 2. More Tier-1 GCCs (100+)
- Visa, Mastercard, American Express, Capital One
- Fidelity, Charles Schwab, TD Ameritrade
- Grab, Gojek, Sea Group, Tokopedia
- Line, Kakao, Naver, Rakuten
- Search: "Global Capability Centers India"

### 3. Series A-B Startups (400+)
- Check Crunchbase: Filter India, Series A-B, Active
- Check AngelList: India startups
- Check Inc42, YourStory databases

### 4. Regional Startups (200+)
- Bangalore startups
- Hyderabad startups
- Pune startups
- NCR startups

### 5. Sector-Specific (249+)
- Fintech (100): Payment, lending, wealth, insurance
- E-commerce (50): Fashion, grocery, electronics
- SaaS (50): HR, marketing, sales, dev tools
- Healthtech (30): Telemedicine, pharmacy, fitness
- Agritech (19): Farm-to-fork, agri-inputs

---

## 🔍 TOOLS TO FIND COMPANIES

### Startup Databases:
1. **Crunchbase** (crunchbase.com)
   - Filter: Location=India, Status=Active, Category=Tech
   - Export company list

2. **AngelList** (angel.co)
   - Browse India startups
   - Filter by stage, sector

3. **Inc42** (inc42.com)
   - Indian startup database
   - Funding news

4. **YourStory** (yourstory.com)
   - Startup directory
   - Company profiles

5. **Tracxn** (tracxn.com)
   - Startup tracker
   - Sector reports

### Career Page Patterns:
Most companies use:
- `company.com/careers`
- `company.com/jobs`
- `jobs.company.com`
- `careers.company.com`

---

## ✅ VERIFY COMPANIES

After adding, validate URLs:
```bash
python validate_urls.py
```

This checks if career pages are accessible.

---

## 📈 CURRENT PROGRESS

```
[████████░░░░░░░░░░░░] 23% (351/1500)

✓ Tier-1 GCCs: 72/200
✓ Unicorns: 133/150
✓ Series B-D: 146/800
✓ IT Services: 0/350

Total: 351/1500
Remaining: 1149
```

---

## 🎯 NEXT STEPS TO REACH 1500+

### Week 1: Add 300 companies
- Focus: IT Services (TCS, Infosys, Wipro, etc.)
- Focus: More GCCs (Visa, Mastercard, etc.)

### Week 2: Add 400 companies
- Focus: Series A-B startups
- Use Crunchbase/AngelList

### Week 3: Add 449 companies
- Focus: Regional startups
- Focus: Sector-specific companies

---

## 💡 PRO TIPS

1. **Batch Import**: Create CSV with 50-100 companies, import at once
2. **Validate URLs**: Always run `validate_urls.py` after adding
3. **Check Duplicates**: Script automatically skips duplicates
4. **Career Page Format**: Most use `/careers` or `/jobs`
5. **Company Types**: Use "Tier-1 GCC", "Unicorn", or "Series B-D"

---

## 🚀 READY-TO-USE COMMANDS

```bash
# Check current count
python -c "import json; print(f'{len(json.load(open(\"companies.json\")))} companies')"

# Import CSV
python import_csv.py your_file.csv

# Import all expansion files
python import_all.py

# Validate URLs
python validate_urls.py

# Run scraper
python main.py
```

---

## 📞 NEED MORE HELP?

See: `ADDING_COMPANIES_GUIDE.md` for detailed instructions

**Current Status:** 351 companies ✓
**Target:** 1500+ companies
**Progress:** 23%
