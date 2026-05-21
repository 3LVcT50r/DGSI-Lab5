@echo off
REM Wrapper for running the retailer-app CLI from the workspace root on Windows.
REM It changes into retailer-app and sets PYTHONPATH so python can locate src.

pushd "%~dp0retailer-app" >nul || exit /b 1
set PYTHONPATH=.
python -m src.cli %*
popd >nul
