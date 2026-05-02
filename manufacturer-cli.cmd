@echo off
REM Wrapper for running the factory-app CLI from the workspace root on Windows.
REM It changes into factory-app and sets PYTHONPATH so python can locate src.

pushd "%~dp0factory-app" >nul || exit /b 1
set PYTHONPATH=.
python -m src.cli %*
popd >nul
