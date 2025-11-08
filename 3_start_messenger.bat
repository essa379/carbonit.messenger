@echo off
echo [*] Starting P2P Messenger Node...
echo.

REM Set the current directory to the script's location
pushd "%~dp0"

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Run the main Python script
python p2p_node.py

REM Deactivate the virtual environment when the script closes
call venv\Scripts\deactivate.bat

popd
echo.
echo [*] Messenger closed.
pause