"""Core scraping engine with multi-portal support"""
import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from config import REQUEST_TIMEOUT, RATE_LIMIT_DELAY, USER_AGENT

class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
    
    def scrape_company(self, company):
        try:
            time.sleep(RATE_LIMIT_DELAY)
            response = self.session.get(company['career_url'], timeout=REQUEST_TIMEOUT)
            
            if response.status_code != 200:
                return []
            
            url = company['career_url']
            if 'greenhouse.io' in url or 'boards.greenhouse.io' in response.text:
                return self._scrape_greenhouse(response, company)
            elif 'lever.co' in url or 'jobs.lever.co' in response.text:
                return self._scrape_lever(response, company)
            elif 'myworkdayjobs.com' in url:
                return self._scrape_workday(response, company)
            else:
                return self._scrape_generic(response, company)
        
        except Exception as e:
            print(f"Error scraping {company['name']}: {str(e)}")
            return []
    
    def _scrape_greenhouse(self, response, company):
        jobs = []
        soup = BeautifulSoup(response.text, 'html.parser')
        
        job_elements = soup.find_all('div', class_='opening')
        for elem in job_elements:
            try:
                title_elem = elem.find('a')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                link = title_elem.get('href', '')
                if not link.startswith('http'):
                    link = f"https://boards.greenhouse.io{link}"
                
                location_elem = elem.find('span', class_='location')
                location = location_elem.text.strip() if location_elem else ''
                
                job_id = re.search(r'/(\d+)/?$', link)
                job_id = job_id.group(1) if job_id else link
                
                jobs.append({
                    'company': company['name'],
                    'company_type': company['type'],
                    'title': title,
                    'location': location,
                    'link': link,
                    'job_id': job_id,
                    'description': '',
                    'posted_date': '',
                    'portal_url': company['career_url']
                })
            except Exception:
                continue
        
        return jobs
    
    def _scrape_lever(self, response, company):
        jobs = []
        soup = BeautifulSoup(response.text, 'html.parser')
        
        job_elements = soup.find_all('div', class_='posting')
        for elem in job_elements:
            try:
                title_elem = elem.find('h5')
                link_elem = elem.find('a', class_='posting-title')
                
                if not title_elem or not link_elem:
                    continue
                
                title = title_elem.text.strip()
                link = link_elem.get('href', '')
                
                location_elem = elem.find('span', class_='sort-by-location')
                location = location_elem.text.strip() if location_elem else ''
                
                job_id = link.split('/')[-1] if link else title
                
                jobs.append({
                    'company': company['name'],
                    'company_type': company['type'],
                    'title': title,
                    'location': location,
                    'link': link,
                    'job_id': job_id,
                    'description': '',
                    'posted_date': '',
                    'portal_url': company['career_url']
                })
            except Exception:
                continue
        
        return jobs
    
    def _scrape_workday(self, response, company):
        jobs = []
        # Workday uses dynamic loading - basic extraction
        soup = BeautifulSoup(response.text, 'html.parser')
        
        job_elements = soup.find_all('li', class_='css-1q2dra3')
        for elem in job_elements:
            try:
                title_elem = elem.find('a')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                link = title_elem.get('href', '')
                
                job_id = re.search(r'Job_Req_ID=([^&]+)', link)
                job_id = job_id.group(1) if job_id else title
                
                jobs.append({
                    'company': company['name'],
                    'company_type': company['type'],
                    'title': title,
                    'location': 'India',
                    'link': link,
                    'job_id': job_id,
                    'description': '',
                    'posted_date': '',
                    'portal_url': company['career_url']
                })
            except Exception:
                continue
        
        return jobs
    
    def _scrape_generic(self, response, company):
        jobs = []
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Common patterns for job listings
        job_elements = (
            soup.find_all('div', class_=re.compile(r'job|position|opening|career', re.I)) +
            soup.find_all('li', class_=re.compile(r'job|position|opening', re.I)) +
            soup.find_all('a', href=re.compile(r'job|career|position', re.I))
        )
        
        # Filter words that indicate non-job links
        exclude_titles = [
            'cookie', 'privacy', 'policy', 'preferences', 'filter', 'clear',
            'talent community', 'join', 'sign in', 'login', 'register',
            'search', 'apply', 'view', 'home', 'about', 'contact'
        ]
        
        for elem in job_elements[:50]:
            try:
                link_elem = elem.find('a') if elem.name != 'a' else elem
                if not link_elem:
                    continue
                
                title = link_elem.text.strip()
                if len(title) < 5 or len(title) > 100:
                    continue
                
                # Skip non-job titles
                title_lower = title.lower()
                if any(word in title_lower for word in exclude_titles):
                    continue
                
                # Must contain job-related keywords
                job_keywords = ['engineer', 'developer', 'architect', 'analyst', 'designer', 'manager', 'lead']
                if not any(kw in title_lower for kw in job_keywords):
                    continue
                
                link = link_elem.get('href', '')
                if not link.startswith('http'):
                    base_url = '/'.join(company['career_url'].split('/')[:3])
                    link = f"{base_url}{link}" if link.startswith('/') else f"{base_url}/{link}"
                
                jobs.append({
                    'company': company['name'],
                    'company_type': company['type'],
                    'title': title,
                    'location': 'India',
                    'link': link,
                    'job_id': link,
                    'description': '',
                    'posted_date': '',
                    'portal_url': company['career_url']
                })
            except Exception:
                continue
        
        return jobs
    
    def fetch_job_description(self, job_url):
        try:
            time.sleep(RATE_LIMIT_DELAY)
            response = self.session.get(job_url, timeout=REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()
            
            # Try common description containers
            desc_elem = (
                soup.find('div', class_=re.compile(r'description|content|details', re.I)) or
                soup.find('div', id=re.compile(r'description|content|details', re.I)) or
                soup.find('section', class_=re.compile(r'description|content', re.I))
            )
            
            if desc_elem:
                return desc_elem.get_text(separator='\n', strip=True)[:5000]
            
            return soup.get_text(separator='\n', strip=True)[:5000]
        
        except Exception:
            return ''
