"""State management for tracking scraping history and job deduplication"""
import json
import os
from datetime import datetime, timedelta
from config import STATE_FILE, ROTATION_DAYS, COMPANIES_PER_RUN


class StateManager:
    def __init__(self, state_file=STATE_FILE):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {"companies": {}, "seen_jobs": {}}
        return {"companies": {}, "seen_jobs": {}}

    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_companies_to_scrape(self, all_companies):
        # Return all companies (no rotation limit)
        return all_companies

    def mark_company_scraped(self, company_name, job_count):
        self.state['companies'][company_name] = {
            'last_scraped': datetime.now().isoformat(),
            'job_count': job_count
        }

    def is_job_seen(self, job_id):
        return job_id in self.state['seen_jobs']

    def mark_job_seen(self, job_id, company_name):
        self.state['seen_jobs'][job_id] = {
            'company': company_name,
            'first_seen': datetime.now().isoformat()
        }

    def cleanup_old_jobs(self, days=30):
        cutoff = datetime.now() - timedelta(days=days)
        self.state['seen_jobs'] = {
            jid: data for jid, data in self.state['seen_jobs'].items()
            if datetime.fromisoformat(data['first_seen']) > cutoff
        }
