$ErrorActionPreference = "Stop"

python -m pip install --upgrade pyinstaller pyinstaller-hooks-contrib

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onedir `
  --windowed `
  --contents-directory . `
  --name CISHEN `
  --add-data "config.json;." `
  --add-data "NOTICE.txt;." `
  cishen_clicker\gui.py

Compress-Archive -Path dist\CISHEN\* -DestinationPath CISHEN.zip -Force
