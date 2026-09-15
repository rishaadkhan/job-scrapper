# Job Filtering Specifications & Rules Engine

## 🎯 Filtering Principles

The **Enterprise Job Scraper** employs a strict, multi-stage business logic filter (`filters.py`) designed to extract high-conversion backend engineering opportunities for early-career developers (0–3 years experience in India).

---

## 🔍 Core Filtering Criteria

### 1. ✅ Positive Backend Role Requirement (`is_backend_role`)
- Every job title or description **must positively match** at least one backend engineering keyword from `BACKEND_KEYWORDS` (e.g. `Backend`, `Server`, `Platform`, `Distributed Systems`, `Microservices`, `Python`, `Java`, `Go`, `Golang`, `FastAPI`, `Spring Boot`, `PostgreSQL`, `REST API`).
- Generic software engineering titles without backend signals are disqualified.

### 2. ❌ Excluded Seniority & Non-Engineering Disciplines (`is_excluded_title`)
Automatically rejects titles matching:
- **Seniority & Management**: `Senior`, `Staff`, `Principal`, `Lead`, `Manager`, `Director`, `VP`, `Architect`, `Head of`.
- **Internships**: `Intern`, `Internship`, `Trainee`, `Apprentice`.
- **Non-Engineering / Other Specialties**: `QA`, `Quality Assurance`, `Test Engineer`, `SDET`, `Frontend`, `UI`, `UX`, `Designer`, `DevOps`, `SRE`, `Product Manager`, `Scrum Master`.

### 3. 📍 India Location Validation (`is_valid_location`)
- Validates the scraped location against canonical India tech hubs: `Bengaluru`, `Bangalore`, `Hyderabad`, `Pune`, `Gurgaon`, `Gurugram`, `Noida`, `Delhi NCR`, `Mumbai`, `Chennai`, or `Remote (India)`.
- Rejects postings with foreign or overseas locations (e.g. `London`, `San Francisco`, `Singapore`, `Berlin`, `Toronto`).

### 4. ⏳ Experience Range Parsing (`extract_experience_years`)
- Parses natural language experience requirements in job descriptions (e.g., `"0-2 years"`, `"1-3 yrs"`, `"freshers welcome"`).
- Automatically disqualifies roles requiring `> 3 years` of prior professional experience.

---

## ⚙️ Dynamic Filter Configuration (No Code Redeployment)

Filters can now be tuned dynamically via two interfaces:

### 1. Web Dashboard
Visit [http://localhost:5173/filters](http://localhost:5173/filters) to adjust backend keywords, excluded keywords, experience thresholds, and allowed locations with immediate database persistence.

### 2. FastAPI REST API
```bash
# Update filters dynamically via PUT /filters
curl -X PUT http://localhost:8000/filters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "min_experience": 0,
    "max_experience": 3,
    "backend_keywords": ["backend", "server", "python", "golang", "java", "spring boot", "fastapi"],
    "exclude_keywords": ["senior", "lead", "staff", "principal", "manager", "intern"],
    "allowed_locations": ["bengaluru", "hyderabad", "pune", "gurgaon", "noida", "remote"]
  }'
```
