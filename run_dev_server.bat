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

rem install dependencies
echo Installing and Upgrading Dependencies...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
pip-upgrade requirements.txt -p all

rem start the Flask server
cls 
echo ========================================================
echo Starting Flask Server (Developer Mode)...
echo:
call flask run -h 0.0.0.0 -p 8080 --debug

rem terminate the Flask server and deactivate the Virtual Environment
echo Terminating Batch Job...
echo Stopping Virutal Environment...
call deactivate