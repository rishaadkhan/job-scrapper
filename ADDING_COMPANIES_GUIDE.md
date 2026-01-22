# HOW TO ADD 1500+ COMPANIES - COMPLETE GUIDE

## 🎯 GOAL: Expand from 155 to 1500+ companies

---

## METHOD 1: Use expand_companies.py (EASIEST)

### Step 1: Edit expand_companies.py

Open the file and add companies to the `ADDITIONAL_COMPANIES` list:

```python
ADDITIONAL_COMPANIES = [
    {"name": "Company Name", "type": "Tier-1 GCC|Unicorn|Series B-D", "career_url": "https://..."},
    {"name": "Another Company", "type": "Unicorn", "career_url": "https://..."},
    # Add as many as you want
]
```

### Step 2: Run the script

```bash
python expand_companies.py
```

This automatically:
- Avoids duplicates
- Adds new companies to companies.json
- Shows count before/after

---

## METHOD 2: Direct JSON Editing (BULK ADD)

### Step 1: Open companies.json

```bash
nano companies.json
# or use any text editor
```

### Step 2: Add companies in JSON format

```json
[
  {
    "name": "Existing Company",
    "type": "Tier-1 GCC",
    "career_url": "https://..."
  },
  {
    "name": "New Company 1",
    "type": "Unicorn",
    "career_url": "https://newcompany1.com/careers"
  },
  {
    "name": "New Company 2",
    "type": "Series B-D",
    "career_url": "https://newcompany2.com/jobs"
  }
]
```

### Step 3: Validate JSON

```bash
python -c "import json; json.load(open('companies.json')); print('✓ Valid JSON')"
```

---

## METHOD 3: CSV Import (RECOMMENDED FOR BULK)

### Step 1: Create a CSV file

Create `new_companies.csv`:

```csv
name,type,career_url
Stripe India,Tier-1 GCC,https://stripe.com/jobs/search?location=India
Notion India,Tier-1 GCC,https://www.notion.so/careers?location=India
Canva India,Unicorn,https://www.canva.com/careers/jobs/?location=India
```

### Step 2: Use the import script

I'll create this for you below.

---

## METHOD 4: Automated Company Discovery

I'll create a script that helps you find companies automatically.

---

## 📋 COMPANY CATEGORIES TO ADD (1500+ TARGET)

### Tier-1 GCCs (Target: 200+)
Currently: 32 | Need: 168 more

**US Tech Giants:**
- Stripe, Shopify, Slack, Zoom, Dropbox, Box, Twilio, Okta
- Databricks, Snowflake, Confluent, MongoDB, Elastic, Redis
- HashiCorp, GitLab, Atlassian, Splunk, ServiceNow
- Workday, Zendesk, HubSpot, Mailchimp, SurveyMonkey

**European Tech:**
- Spotify, Klarna, Revolut, N26, TransferWise (Wise)
- Delivery Hero, Zalando, Booking.com, Trivago

**Asian Tech:**
- Grab, Gojek, Sea Group (Shopee), Tokopedia, Bukalapak
- Line, Kakao, Naver, Rakuten, Mercari

**Financial Services:**
- Visa, Mastercard, American Express, Capital One
- Fidelity, Charles Schwab, TD Ameritrade, E*TRADE

**Enterprise Software:**
- ServiceNow, Workday, Splunk, New Relic, Datadog
- PagerDuty, Auth0, Segment, Amplitude

### Indian Unicorns (Target: 150+)
Currently: 73 | Need: 77 more

**Fintech:**
- Cred, BharatPe, Slice, Jupiter, Niyo, Jar, Fi Money
- Khatabook, OkCredit, BankBazaar, Paisabazaar
- Scripbox, Smallcase, Upstox, Angel One, 5paisa

**E-commerce:**
- Meesho, Dealshare, Shopsy, Glowroad, Shop101
- FirstCry, BabyChakra, Hopscotch, Bewakoof, Snitch

**Edtech:**
- BYJU'S, Unacademy, Vedantu, upGrad, Eruditus
- Simplilearn, Toppr, Doubtnut, Classplus, Teachmint
- Scaler, InterviewBit, Coding Ninjas, Newton School

**Healthtech:**
- PharmEasy, 1mg, Practo, Cure.fit, HealthifyMe
- Pristyn Care, Lybrate, DocsApp, mfine

**Logistics:**
- Delhivery, Shadowfax, Ecom Express, Xpressbees
- Porter, LetsTransport, Rivigo, BlackBuck

**Food & Grocery:**
- Swiggy, Zomato, Dunzo, Zepto, Blinkit (Grofers)
- Licious, FreshToHome, Country Delight, Milkbasket

**Social & Content:**
- ShareChat, Moj, Josh, Chingari, Roposo
- Dailyhunt, InMobi, Glance, Hike

**Gaming:**
- Dream11, MPL, Games24x7, Paytm First Games
- WinZO, Zupee, GetMega, Ace2Three

**SaaS:**
- Freshworks, Postman, Chargebee, Zoho, CleverTap
- WebEngage, MoEngage, Exotel, Knowlarity
- Darwinbox, Keka, GreytHR, SumHR

### Series B-D Startups (Target: 800+)
Currently: 50 | Need: 750 more

**Fintech (100+):**
- Simpl, LazyPay, ZestMoney, KreditBee, MoneyTap
- EarlySalary, PaySense, CASHe, Stashfin, FlexiLoans
- Lendingkart, Capital Float, NeoGrowth, Indifi
- Razorpay Capital, Cashfree Payments, Instamojo

**E-commerce (100+):**
- Snapdeal, ShopClues, Pepperfry, Urban Ladder
- Myntra, Ajio, Tata CLiQ, Flipkart Fashion
- Nykaa Fashion, Purplle, MyGlamm, Sugar Cosmetics
- Boat, Noise, boAt Lifestyle, Mamaearth

**Proptech (50+):**
- NoBroker, Housing.com, 99acres, MagicBricks
- Nestaway, Zolo, OYO Life, Colive
- Stanza Living, Your Space, Settl, Housr

**Mobility (50+):**
- Ola, Uber, Rapido, Bounce, Vogo
- Yulu, Mobycy, Spinny, Cars24, CarDekho
- Droom, CarTrade, OLX Autos, Truebil

**Travel & Hospitality (50+):**
- OYO, Treebo, FabHotels, Zostel, Hostelworld
- MakeMyTrip, Goibibo, Cleartrip, Yatra, ixigo
- EaseMyTrip, TravelTriangle, Thrillophilia

**B2B Commerce (100+):**
- Udaan, Moglix, Infra.Market, OfBusiness
- Zetwerk, Bijnis, ShopKirana, Jumbotail
- Ninjacart, WayCool, Crofarm, DeHaat

**HR Tech (50+):**
- Darwinbox, Keka, GreytHR, SumHR, Zimyo
- Pocket HRMS, Qandle, Beehive, Kredily
- Razorpay Payroll, Zoho People, BambooHR India

**Marketing Tech (50+):**
- CleverTap, WebEngage, MoEngage, Netcore Cloud
- Insider, Wigzo, Vizury, Vserv, InMobi
- AdPushup, Taboola India, Outbrain India

**Developer Tools (50+):**
- Postman, BrowserStack, LambdaTest, Testsigma
- Hevo Data, Atlan, Hasura, Appsmith
- Dyte, 100ms, Agora India, Twilio India

**Cybersecurity (30+):**
- Securin, CloudSEK, Lucideus, Quick Heal
- K7 Computing, Sequretek, Paladion, Aujas

**AI/ML Startups (50+):**
- Haptik, Yellow.ai, Verloop.io, Gupshup
- Observe.AI, Uniphore, Skit.ai, Vernacular.ai
- Mad Street Den, SigTuple, Niramai, Qure.ai

**Agritech (30+):**
- DeHaat, Ninjacart, WayCool, Crofarm
- AgroStar, BigHaat, Gramophone, Agrowave
- Ergos, Stellapps, Intello Labs

**Cleantech (30+):**
- Ather Energy, Ola Electric, Revolt Motors
- Sun Mobility, Lithion Power, Log9 Materials
- ReNew Power, CleanMax Solar, Fourth Partner Energy

**Insurtech (30+):**
- Acko, Digit Insurance, Go Digit, Turtlemint
- RenewBuy, Coverfox, InsuranceDekho, PolicyBazaar

**Wealthtech (30+):**
- Groww, Zerodha, Upstox, Angel One, 5paisa
- Smallcase, Scripbox, ET Money, Paytm Money
- INDmoney, Jar, Fi Money, Jupiter

**Regtech/Legaltech (20+):**
- Signzy, IDfy, Digio, Leegality, SpotDraft
- LegalKart, Vakilsearch, LawRato, MyAdvo

**Supply Chain (30+):**
- Locus, FarEye, LogiNext, Shipsy, Shiprocket
- Delhivery, Shadowfax, Ecom Express, Xpressbees

### Service Companies (Target: 350+)

**IT Services:**
- TCS, Infosys, Wipro, HCL, Tech Mahindra
- LTI, Mindtree, Mphasis, Hexaware, Cyient
- Persistent, KPIT, Zensar, Mastek, Sonata

**Product Engineering:**
- Thoughtworks, Hashedin, Incedo, Sigmoid
- Talentica, Robosoft, Qburst, Trigent

**Consulting:**
- McKinsey Digital, BCG Digital Ventures, Bain
- EY GDS, KPMG India, PwC India, Deloitte USI

---

## 🚀 READY-TO-USE EXPANSION SCRIPT

I'll create a comprehensive script below that adds 500+ companies at once.

---

## 📝 TIPS FOR FINDING COMPANIES

### 1. Use These Resources:

**Startup Databases:**
- Crunchbase (filter: India, Active, Tech)
- AngelList (India startups)
- Inc42 (Indian startup database)
- YourStory (startup directory)
- Tracxn (startup tracker)

**Funding News:**
- VCCircle, Inc42, YourStory, Entrackr
- Filter for Series B+ funding rounds

**Job Boards (for company discovery only):**
- LinkedIn (company pages)
- AngelList Jobs
- Instahyre, Cutshort (company lists)

### 2. Career Page URL Patterns:

Most companies use:
- `/careers`
- `/jobs`
- `/careers/jobs`
- `/company/careers`
- `jobs.companyname.com`
- `careers.companyname.com`

### 3. Verify Career Pages:

```bash
python validate_urls.py
```

This checks if URLs are accessible.

---

## 🎯 NEXT: I'll create expansion scripts for you
