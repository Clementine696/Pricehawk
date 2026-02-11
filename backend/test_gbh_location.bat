@echo off
REM Set UTF-8 encoding for Python
set PYTHONIOENCODING=utf-8
chcp 65001 >nul

REM Run the scraper with location parameter
python ./scraper-url/adws/adw_ecommerce_product_scraper.py --urls-file test_urls.txt --gbh-location "นครปฐม" --timeout 120

pause
