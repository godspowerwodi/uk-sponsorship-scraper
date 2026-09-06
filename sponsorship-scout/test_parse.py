import unittest
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.abspath('src'))
from sponsorship_scout.ats.tracjobs import _parse_tracjobs_html

class TestTracJobs(unittest.TestCase):
    def test_parse_403_page(self):
        with open('apps_trac_jobs_403.html', 'r', encoding='utf-8') as f:
            html = f.read()
            
        jobs = _parse_tracjobs_html(html)
        self.assertEqual(len(jobs), 0)
        
    def test_parse_login_page(self):
        with open('trac_jobs_sample.html', 'r', encoding='utf-8') as f:
            html = f.read()
            
        jobs = _parse_tracjobs_html(html)
        self.assertEqual(len(jobs), 0)

if __name__ == '__main__':
    unittest.main()
