@echo off
REM Wrapper for running the provider-app CLI from the workspace root on Windows.
REM It changes into provider-app and sets PYTHONPATH so python can locate src.

pushd "%~dp0provider-app" >nul || exit /b 1
set PYTHONPATH=.
python -m src.cli %*
popd >nul
