@echo off
color a
setlocal enabledelayedexpansion

REM Set the current directory to the script's location
pushd "%~dp0"

REM Activate the virtual environment only once
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

:main_menu
REM --- Main Menu ---
cls
echo --- CarbonIt Messenger Main Menu ---
echo [1] Start P2P Messenger Node
echo [2] Manage Contacts (Add, List, Change, Remove)
echo [3] Quit
echo.

choice /C:123 /M "Please select an option: "

if %ERRORLEVEL% == 3 goto :quit
if %ERRORLEVEL% == 2 goto :contacts_menu
if %ERRORLEVEL% == 1 goto :messenger
goto :main_menu

:messenger
REM --- 1. Start Messenger ---
cls
echo [] Starting P2P Messenger Node...
echo.
python p2p_node.py
echo.
echo [] Messenger closed. Press any key to return to the menu.
pause > nul
goto :main_menu

:contacts_menu
REM --- 2. Contact Management Menu ---
cls
echo --- Contact Manager Menu ---
echo [1] List All Contacts
echo [2] Add New Contact
echo [3] Remove Contact by ID
echo [4] Change Onion Address by ID
echo [5] Back to Main Menu
echo.

choice /C:12345 /M "Select a contact action: "

if %ERRORLEVEL% == 5 goto :main_menu
if %ERRORLEVEL% == 4 goto :contacts_change
if %ERRORLEVEL% == 3 goto :contacts_remove
if %ERRORLEVEL% == 2 goto :contacts_add
if %ERRORLEVEL% == 1 goto :contacts_list
goto :contacts_menu

:contacts_list
cls
echo --- Current Contacts ---
python contact.py list
echo.
echo Press any key to return to the Contact Menu.
pause > nul
goto :contacts_menu

:contacts_add
cls
echo --- Add New Contact (Interactive Mode) ---
REM contact.py 'add' runs interactively, asking for name and onion
python contact.py add
echo.
echo Press any key to return to the Contact Menu.
pause > nul
goto :contacts_menu

:contacts_remove
cls
echo --- Remove Contact ---
python contact.py list
echo.
set /p "CONTACT_ID=Enter the ID of the contact to REMOVE: "
echo.
if not defined CONTACT_ID (
echo [ERROR] No ID entered.
) else (
python contact.py remove %CONTACT_ID%
)
echo.
echo Press any key to return to the Contact Menu.
pause > nul
goto :contacts_menu

:contacts_change
cls
echo --- Change Contact Onion Address ---
python contact.py list
echo.
set /p "CONTACT_ID=Enter the ID of the contact to CHANGE: "
set /p "NEW_ONION=Enter the NEW Onion Address: "
echo.
if not defined CONTACT_ID (
echo [ERROR] Contact ID is required.
) else if not defined NEW_ONION (
echo [ERROR] New Onion Address is required.
) else (
python contact.py change %CONTACT_ID% %NEW_ONION%
)
echo.
echo Press any key to return to the Contact Menu.
pause > nul
goto :contacts_menu

:quit
REM --- 3. Quit ---
echo [] Deactivating virtual environment...
call venv\Scripts\deactivate.bat
popd
echo.
echo [] Goodbye.
pause
endlocal
