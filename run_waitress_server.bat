rem stop echoing command executions to terminal window
@echo off

rem Bypass "Terminate Batch Job" prompt upon pressing CTRL-C to stop Flask server
if "%~1"=="-FIXED_CTRL_C" (
   rem Remove the -FIXED_CTRL_C parameter
   SHIFT
) ELSE (
   rem Run the batch with <NUL and -FIXED_CTRL_C
   CALL <NUL %0 -FIXED_CTRL_C %*
   GOTO :EOF
)

rem clear screen
cls

rem check if a Python Virtual Environment already exists
echo Checking for Virtual Environment Initialization...
IF EXIST env GOTO env_exists
rem initialize, activate, and install dependencies if it doesn't exist
:env_not_exists
echo Virtual Environment Not Initialized.
echo Initializing Virtual Environment...
py -m virtualenv env
call env\Scripts\activate.bat

rem once the Python Virtual Environment is initialized, proceed
:env_exists
echo Virtual Environment Initialized!

rem check if the Virtual Environment is running (VIRTUAL_ENV is set)
IF (%VIRTUAL_ENV%=="%VIRTUAL_ENV%") GOTO :env_started
:env_not_started
echo Starting Virtual Environment...
call env\Scripts\activate

rem once the Python Virtual Environment is started, proceed
:env_started
echo Virtual Environment Started!

rem install and upgrade dependencies recursively
echo Installing and Upgrading Required Dependencies...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
pip-upgrade requirements.txt -p all

rem set the Flask App's port
set "FLASK_PORT=8080"

rem start the Flask server
cls
echo ========================================================
echo Starting Flask Server (Production Mode)...

rem save the IP address of the hosting computer into the NetworkIP environment variable
for /f "delims=[] tokens=2" %%a in ('ping -4 -n 1 %ComputerName% ^| findstr [') do set NetworkIP=%%a

rem save the network SSID of the hosting computer into the NetworkSSID environment variable
for /f "tokens=3" %%i in ('netsh wlan show interface ^| findstr /i "SSID"') do set "NetworkSSID=%%i" & goto next
:next
echo Network SSID: %NetworkSSID%

rem serve using waitress
call waitress-serve --host %NetworkIP% --port %FLASK_PORT% --call "app:create_app"

rem terminate the Flask server and deactivate the Virtual Environment
echo Terminating Batch Job...
echo Stopping Virutal Environment...
call deactivate