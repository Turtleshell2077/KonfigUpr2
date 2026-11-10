@echo off
rem Stage 4: reverse dependencies (packages that depend on the given package)
rem in test repository files (examples/test_repos/, configs in examples/reverse/)
cd /d "%~dp0.."

echo.
echo ===== 1. who depends on D: B and C directly, A through them
type examples\test_repos\simple.txt
call .\run.bat --config examples/reverse/simple.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 2. nobody depends on A (the top of the graph)
call .\run.bat --config examples/reverse/nobody.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 3. who depends on D with filter "B": A is found only through C
call .\run.bat --config examples/reverse/filter.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 4. A is in the cycle A -^> B -^> C -^> A
type examples\test_repos\cycle.txt
call .\run.bat --config examples/reverse/cycle.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 5. A depends on itself
type examples\test_repos\self_loop.txt
call .\run.bat --config examples/reverse/self_loop.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 6. who depends on F: H is not reachable from A, but H depends on F
type examples\test_repos\complex.txt
call .\run.bat --config examples/reverse/complex.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 7. the same with filter "D": B depends on F only through D
call .\run.bat --config examples/reverse/complex_filter.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 8. X is not described in the file, but A depends on it
type examples\test_repos\missing.txt
call .\run.bat --config examples/reverse/not_described.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 9. package Z is not in the file (exit code 1)
call .\run.bat --config examples/reverse/no_package.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 10. reverse mode with a real Maven repository (exit code 1)
call .\run.bat --config examples/errors/reverse_real.yaml
echo [exit code: %ERRORLEVEL%]

echo.
pause
