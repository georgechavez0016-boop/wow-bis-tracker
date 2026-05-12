@echo off
echo Scraping BiS data...
python scraper.py
if errorlevel 1 (
    echo Scraper failed. Aborting.
    pause
    exit /b 1
)

echo Generating viewer...
python generate_viewer.py
if errorlevel 1 (
    echo Viewer generation failed. Aborting.
    pause
    exit /b 1
)

echo Pushing to GitHub...
git add index.html bis_data.json
git commit -m "Update BiS data"
git push

echo Done! Site will update in ~30 seconds.
pause
