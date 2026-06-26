$ErrorActionPreference = "Stop"

$Python = "py"
$PythonVersion = "-3.7"
$InstallerScript = "installer.iss"

$PipOptions = @("--disable-pip-version-check", "--prefer-binary")

# & $Python $PythonVersion -m pip install @PipOptions --upgrade "pip<24.1" "setuptools<69" wheel
# & $Python $PythonVersion -m pip install @PipOptions --upgrade -r requirements-pack-win7.txt
# & $Python $PythonVersion -m pip install @PipOptions --upgrade "pyinstaller==5.13.2" "pyinstaller-hooks-contrib==2023.10"

foreach ($Path in @(
  "build",
  "dist",
  "dist-installer",
  "cishen-assistant-setup.exe"
)) {
  if (Test-Path -LiteralPath $Path) {
    Remove-Item -LiteralPath $Path -Recurse -Force
  }
}

$InstallerOutputPatterns = @(
  "cishen-assistant-setup-*.exe"
)
foreach ($Pattern in $InstallerOutputPatterns) {
  Get-ChildItem -Path "." -Filter $Pattern -File -ErrorAction SilentlyContinue | Remove-Item -Force
}

& $Python $PythonVersion -m PyInstaller `
  --noconfirm `
  --clean `
  cishen-assistant.spec

if (-not (Test-Path -LiteralPath $InstallerScript)) {
  throw "Installer script not found: $InstallerScript"
}

$InnoSetupCandidates = @(
  "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
  "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
  "ISCC.exe",
  "iscc"
)

$InnoSetupRegistryRoots = @(
  "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
  "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
  "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
)

foreach ($RegistryRoot in $InnoSetupRegistryRoots) {
  Get-ItemProperty $RegistryRoot -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -like "Inno Setup*" -and $_.InstallLocation } |
    ForEach-Object {
      $InnoSetupCandidates += (Join-Path $_.InstallLocation "ISCC.exe")
    }
}

$Iscc = $null
foreach ($Candidate in $InnoSetupCandidates) {
  if ($Candidate -match '[\\/]') {
    if (Test-Path -LiteralPath $Candidate) {
      $Iscc = $Candidate
      break
    }
    continue
  }

  $Command = Get-Command $Candidate -ErrorAction SilentlyContinue
  if ($Command) {
    $Iscc = $Command.Source
    break
  }
}

if (-not $Iscc) {
  throw "Inno Setup compiler ISCC was not found. Install Inno Setup 6 or add ISCC.exe to PATH."
}

& $Iscc $InstallerScript

Write-Host "Installer generated: dist-installer\cishen-assistant-setup-*.exe"
