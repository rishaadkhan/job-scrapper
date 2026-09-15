# ⚡ Quick Reference Card: Commands & Usage

## 🚀 Common Commands

### Local Setup & Verification
```bash
./setup.sh                                   # Full automated local setup
source venv/bin/activate                     # Activate Python virtualenv
python -m unittest discover tests            # Run complete 30-test suite
```

### Running Scraper & Pipeline
```bash
python main.py                               # Full async scrape pipeline
python demo.py                               # Interactive 3-company quick demo
python test_scraper.py                       # System health check & integration test
python validate_urls.py --limit 20           # Asynchronous URL health validator
```

### Running Web App & REST API
```bash
# FastAPI Backend Server (Port 8000)
uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload

# React Web Dashboard (Port 5173)
cd frontend && npm run dev
```

### Docker Commands
```bash
docker-compose up --build -d                 # Start full stack (API + Frontend)
docker-compose logs -f api                   # Follow API container logs
docker-compose run --rm scheduler            # Trigger scrape run inside container
docker-compose down                          # Stop all containers
```

### Adding & Managing Companies
```bash
python import_csv.py file.csv                # Import CSV with ATS detection
python expand_companies.py                   # Expand company target database
python import_all.py                         # Batch import all expansion CSVs
```

---

## 🔑 Default Credentials & URLs
- **Web Dashboard**: [http://localhost:5173](http://localhost:5173)
- **FastAPI OpenAPI Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Admin Email**: `admin@jobscraper.io`
- **Admin Password**: `admin123`
