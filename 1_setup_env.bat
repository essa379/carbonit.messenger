@echo off
echo [*] Setting up Python Virtual Environment and dependencies...

REM Create the virtual environment in the 'venv' folder
python -m venv venv

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Install required Python libraries
pip install PySocks

echo [*] Setup complete. Virtual environment is ready.
echo.
pause