@echo off
setlocal

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
  echo Please install Python 3 first: https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --windowed --name "SongListApp" --icon "assets\SongListApp.ico" --add-data "data\nocopyright_list.csv;data" app.py

echo.
echo Done. EXE path:
echo %cd%\dist\SongListApp\SongListApp.exe
pause
