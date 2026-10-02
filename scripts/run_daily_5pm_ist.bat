@echo off
REM South East Bengaluru Real Estate Radar & Rental Discovery Platform - Automated 5 PM IST Local Trigger
cd /d "%~dp0\.."
echo =================================================================
echo Running Daily 5 PM IST South East Bengaluru Radar Snapshot...
echo =================================================================
python scripts\daily_tracker.py --force
echo Done! Saved top 10 purchase, top 5 rental, and historical prices.
pause
