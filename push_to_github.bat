@echo off
echo ========================================
echo   ThreatSense - Auto Push to GitHub
echo ========================================

git add -A
git commit -m "Update: %date% %time%"
git push

echo ========================================
echo   Done! Check GitHub to confirm.
echo ========================================
pause
