@echo off
rem Errors in the config file, one case for every parameter (exit code 1)
cd /d "%~dp0.."

echo.
echo ===== the config file does not exist
call .\run.bat --config examples/no_such_config.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== not valid YAML (bad_syntax.yaml)
call .\run.bat --config examples/errors/bad_syntax.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== a list instead of key: value pairs (not_pairs.yaml)
call .\run.bat --config examples/errors/not_pairs.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== unknown key, package is missing (unknown_key.yaml)
call .\run.bat --config examples/errors/unknown_key.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== five parameters are missing (missing_keys.yaml)
call .\run.bat --config examples/errors/missing_keys.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== package without groupId (bad_package.yaml)
call .\run.bat --config examples/errors/bad_package.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== package in test mode is not capital letters (bad_package_test.yaml)
call .\run.bat --config examples/errors/bad_package_test.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== repository is not an http(s) URL (bad_url.yaml)
call .\run.bat --config examples/errors/bad_url.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== test repository file not found (no_test_repo.yaml)
call .\run.bat --config examples/errors/no_test_repo.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== test_mode is not true or false (bad_test_mode.yaml)
call .\run.bat --config examples/errors/bad_test_mode.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== reverse_mode is not true or false (bad_reverse_mode.yaml)
call .\run.bat --config examples/errors/bad_reverse_mode.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== reverse_mode with a real repository (reverse_real.yaml)
call .\run.bat --config examples/errors/reverse_real.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== version is empty (no_version.yaml)
call .\run.bat --config examples/errors/no_version.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== version contains a space (bad_version.yaml)
call .\run.bat --config examples/errors/bad_version.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== folder for output does not exist (bad_output_dir.yaml)
call .\run.bat --config examples/errors/bad_output_dir.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== output is a folder (output_is_folder.yaml)
call .\run.bat --config examples/errors/output_is_folder.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== filter is a list (bad_filter.yaml)
call .\run.bat --config examples/errors/bad_filter.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== several errors at once (many_errors.yaml)
call .\run.bat --config examples/errors/many_errors.yaml
echo [exit code: %ERRORLEVEL%]

echo.
echo ===== unknown command line option (exit code 2)
call .\run.bat --unknown
echo [exit code: %ERRORLEVEL%]

echo.
pause
