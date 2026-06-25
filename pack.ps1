$ErrorActionPreference = "Stop"

$Python = "py"
$PythonVersion = "-3.7"

$PipOptions = @("--disable-pip-version-check", "--prefer-binary")

# & $Python $PythonVersion -m pip install @PipOptions --upgrade "pip<24.1" "setuptools<69" wheel
# & $Python $PythonVersion -m pip install @PipOptions --upgrade -r requirements-pack-win7.txt
# & $Python $PythonVersion -m pip install @PipOptions --upgrade "pyinstaller==5.13.2" "pyinstaller-hooks-contrib==2023.10"

foreach ($Path in @("build", "dist", "CISHEN.zip", "CISHEN-Assistant.zip", "CiShen Assistant.zip", "cishen assistant.zip", "次神助手.zip")) {
  if (Test-Path -LiteralPath $Path) {
    Remove-Item -LiteralPath $Path -Recurse -Force
  }
}

& $Python $PythonVersion -m PyInstaller `
  --noconfirm `
  --clean `
  --onedir `
  --windowed `
  --name "cishen assistant" `
  --add-data "config.json;." `
  --add-data "NOTICE.txt;." `
  cishen_clicker\gui.py

Compress-Archive -Path "dist\cishen assistant\*" -DestinationPath "cishen assistant.zip" -Force
