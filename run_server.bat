rem Bypass "Terminate Batch Job" prompt.
if "%~1"=="-FIXED_CTRL_C" (
   REM Remove the -FIXED_CTRL_C parameter
   SHIFT
) ELSE (
   REM Run the batch with <NUL and -FIXED_CTRL_C
   CALL <NUL %0 -FIXED_CTRL_C %*
   GOTO :EOF
)

@echo off
cls

echo Checking for Virtual Environment Initialization...
IF EXIST env GOTO env_exists
:env_not_exists
echo Virtual Environment Not Initialized.
echo Initializing Virtual Environment...
py -m virtualenv env
call env\Scripts\activate.bat
echo Recursively Installing Dependencies...
py -m pip install -r requirements.txt

:env_exists
echo Virtual Environment Initialized!

IF (%VIRTUAL_ENV%=="%VIRTUAL_ENV%") GOTO :env_started
:env_not_started
echo Starting Virtual Environment...
call env\Scripts\activate

:env_started
echo Virtual Environment Started!

echo Installing Required Dependencies...
py -m pip install -r requirements.txt

echo Starting Flask Server...
call flask run -h 0.0.0.0 -p 5000

echo Terminating Batch Job...
echo Stopping Virutal Environment...
call deactivate