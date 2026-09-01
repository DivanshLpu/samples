@echo off
:prompt
echo.
set "msg="
set /p "msg=Enter commit message: "

if not defined msg echo Error: Commit message cannot be empty. && goto prompt

echo.
echo Staging files...
git.exe add .

echo Committing changes...
git.exe commit -m "%msg%"

echo getting for push...
git.exe push origin main

echo.
echo Done!
pause
