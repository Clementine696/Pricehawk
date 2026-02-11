@echo off
REM Set UTF-8 encoding for Python
set PYTHONIOENCODING=utf-8
chcp 65001 >nul

echo ========================================
echo Testing GlobalHouse Location Scraping
echo ========================================
echo.

REM Test Location 1: นครปฐม (Nakhon Pathom)
echo [1/3] Testing location: นครปฐม
python ./scraper-url/adws/adw_ecommerce_product_scraper.py --urls-file test_urls.txt --gbh-location "นครปฐม" --timeout 120 --output-file location_nakhon_pathom.json
echo.

REM Test Location 2: ขอนแก่น (Khon Kaen)
echo [2/3] Testing location: ขอนแก่น
python ./scraper-url/adws/adw_ecommerce_product_scraper.py --urls-file test_urls.txt --gbh-location "ขอนแก่น" --timeout 120 --output-file location_khon_kaen.json
echo.

REM Test Location 3: เชียงใหม่ (Chiang Mai)
echo [3/3] Testing location: เชียงใหม่
python ./scraper-url/adws/adw_ecommerce_product_scraper.py --urls-file test_urls.txt --gbh-location "เทพ" --timeout 120 --output-file location_chiang_mai.json
echo.

echo ========================================
echo All tests complete!
echo Check the agents folder for results
echo ========================================
pause
