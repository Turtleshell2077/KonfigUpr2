@echo off
rem Stage 3: dependency graph from test repository files (examples/test_repos/)
cd /d "%~dp0.."

echo.
echo ===== 1. diamond: B and C both depend on D, D is visited once
type examples\test_repos\simple.txt
call .\run.bat --config examples/test_mode/simple.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 2. the same graph with filter "D": package D is not analysed
call .\run.bat --config examples/test_mode/filter.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 3. cycle A -^> B -^> C -^> A
type examples\test_repos\cycle.txt
call .\run.bat --config examples/test_mode/cycle.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 4. the same cycle with filter "C": the cycle is broken
call .\run.bat --config examples/test_mode/cycle_filter.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 5. package A depends on itself
type examples\test_repos\self_loop.txt
call .\run.bat --config examples/test_mode/self_loop.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 6. two cycles, shared packages, H is not reachable from A
type examples\test_repos\complex.txt
call .\run.bat --config examples/test_mode/complex.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 7. the same graph, the analysis starts from D
call .\run.bat --config examples/test_mode/complex_from_d.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 8. package X is not described: a warning, the graph is still built
type examples\test_repos\missing.txt
call .\run.bat --config examples/test_mode/missing.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 9. package Z is not in the file (exit code 1)
call .\run.bat --config examples/test_mode/no_root.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 10. wrong package name in the file (exit code 1)
type examples\test_repos\bad_name.txt
call .\run.bat --config examples/test_mode/bad_name.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== 11. a line without a colon in the file (exit code 1)
type examples\test_repos\bad_line.txt
call .\run.bat --config examples/test_mode/bad_line.yaml
echo [exit code: %ERRORLEVEL%]

echo.
pause
