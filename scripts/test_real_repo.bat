@echo off
rem Stage 3: dependency graphs of real packages from Maven Central (needs the Internet)
rem Since stage 5 the graph is also saved as a PNG image (needs d2 in PATH)
cd /d "%~dp0.."

echo.
echo ===== 1. config.yaml: commons-text 1.12.0 (test dependencies are not in the graph)
call .\run.bat
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 2. spring-context 6.1.12: several levels of transitive dependencies
call .\run.bat --config examples/spring.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 3. guava 33.3.1-jre with filter "annotations"
call .\run.bat --config examples/real.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 4. jackson-databind 2.17.2
call .\run.bat --config examples/jackson.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 5. commons-codec 1.10: no dependencies in the graph
call .\run.bat --config examples/codec.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 6. the package does not exist (exit code 1)
call .\run.bat --config examples/repo_errors/package_not_found.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 7. the version does not exist (exit code 1)
call .\run.bat --config examples/repo_errors/version_not_found.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 8. the server does not exist (exit code 1)
call .\run.bat --config examples/repo_errors/bad_host.yaml
echo [exit code: %ERRORLEVEL%]

echo.
pause
