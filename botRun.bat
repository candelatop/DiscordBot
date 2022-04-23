@echo off

call %~dp0venv\Scripts\activate

cd %~dp0discBot

python discBot.py

pause