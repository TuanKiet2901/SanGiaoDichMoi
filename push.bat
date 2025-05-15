@echo off
setlocal enabledelayedexpansion

echo Nhap commit message (tieng Viet):
set /p commit_message=

git add .
git commit -m "%commit_message%"
git push

echo.
echo Da push code thanh cong!
pause 