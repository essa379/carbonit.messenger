@echo off
echo [*] Checking and installing PySocks library...
REM Attempt to install PySocks silently, only if not already installed
pip install PySocks

echo.
echo [*] Starting Tor Daemon (Node Host)...
echo.

REM Navigate to the 'tor' directory where tor.exe is located [cite: 1]
cd tor

REM Start tor.exe using the torrc configuration file [cite: 1]
.\tor.exe -f torrc

REM The window will remain open displaying Tor's bootstrap status. [cite: 1]
echo.
echo [*] Tor Daemon stopped.
pause
