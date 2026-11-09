@echo off
rem Stage 1: correct configs, all parameters are printed as "key: value"
cd /d "%~dp0.."

echo.
echo ===== 1. without --config (config.yaml is used)
call .\run.bat
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 2. real repository with a filter
call .\run.bat --config examples/real.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 3. version 1.10 without quotes, empty filter
call .\run.bat --config examples/codec.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 4. test repository mode
call .\run.bat -c examples/test_mode.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 5. --help
call .\run.bat --help
echo [exit code: %ERRORLEVEL%]

echo.
pause
