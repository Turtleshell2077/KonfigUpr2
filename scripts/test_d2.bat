@echo off
rem Stage 5: D2 text and PNG images of the dependency graphs of three packages
rem (needs the d2 program in PATH and the Internet)
cd /d "%~dp0.."

echo.
echo ===== 1. spring-context 6.1.12: some packages are used by several others
call .\run.bat --config examples/spring.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 2. okhttp 4.12.0: two versions of kotlin-stdlib come by different paths
call .\run.bat --config examples/okhttp.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 3. guava 33.3.1-jre with filter "annotations"
call .\run.bat --config examples/real.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo Images: spring.png, okhttp.png, examples\guava.png
pause
