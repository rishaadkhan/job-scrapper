"""Excel export functionality"""
import os
from datetime import datetime
from openpyxl import Workbook
from config import OUTPUT_DIR, EXCEL_FILENAME_TEMPLATE, EXCEL_COLUMNS
from filters import JobFilter

class ExcelExporter:
    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    def export_jobs(self, jobs):
        if not jobs:
            print("No jobs to export")
            return None
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Job Leads"
        
        # Write headers
        ws.append(EXCEL_COLUMNS)
        
        # Write data rows
        for job in jobs:
            ws.append([
                job['company'],
                job['company_type'],
                job['title'],
                JobFilter.extract_experience(job['title'], job['description']),
                job['location'],
                job['job_id'],
                job['posted_date'],
                job['link'],
                job['portal_url'],
                job['description'],
                job['scraped_at']
            ])
        
        filename = EXCEL_FILENAME_TEMPLATE.format(date=datetime.now().strftime('%Y-%m-%d'))
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        wb.save(filepath)
        print(f"Exported {len(jobs)} jobs to {filepath}")
        
        return filepath
