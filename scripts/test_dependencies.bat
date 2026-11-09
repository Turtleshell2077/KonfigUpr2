@echo off
rem Stage 2: direct dependencies of real packages from Maven Central (needs the Internet)
cd /d "%~dp0.."

echo.
echo ===== 1. config.yaml: commons-text 1.12.0 (compile and test dependencies)
call .\run.bat
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 2. guava 33.3.1-jre: some versions come from the parent POM
call .\run.bat --config examples/real.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 3. jackson-databind 2.17.2: versions from properties and an imported BOM
call .\run.bat --config examples/jackson.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 4. commons-codec 1.10: only one dependency
call .\run.bat --config examples/codec.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 5. the package does not exist (exit code 1)
call .\run.bat --config examples/repo_errors/package_not_found.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 6. the version does not exist (exit code 1)
call .\run.bat --config examples/repo_errors/version_not_found.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 7. the server does not exist (exit code 1)
call .\run.bat --config examples/repo_errors/bad_host.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 8. the test repository mode is not supported yet (exit code 1)
call .\run.bat --config examples/test_mode.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 9. --help
call .\run.bat --help
echo [exit code: %ERRORLEVEL%]

echo.
pause
