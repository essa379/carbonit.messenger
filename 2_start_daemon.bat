@echo off
echo [*] Starting Tor Daemon (Node Host)...
echo.

REM Navigate to the 'tor' directory where tor.exe is located
cd tor

REM Start tor.exe using the torrc configuration file
.\tor.exe -f torrc

REM The window will remain open displaying Tor's bootstrap status.
echo.
echo [*] Tor Daemon stopped.
pause