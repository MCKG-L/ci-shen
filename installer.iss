#define AppVersion "1.0.0"

[Setup]
AppId={{E833F903-D7D0-4DF7-9A88-6EBA1738B14B}
AppName=次神助手
AppVersion={#AppVersion}
AppPublisher=太虚殿
AppPublisherURL=https://github.com/MCKG-L/ci-shen
AppSupportURL=https://github.com/MCKG-L/ci-shen/issues
AppUpdatesURL=https://github.com/MCKG-L/ci-shen/releases
DefaultDirName={localappdata}\Programs\cishen-assistant
DefaultGroupName=次神助手
DisableDirPage=no
DisableProgramGroupPage=yes
OutputDir=dist-installer
OutputBaseFilename=cishen-assistant-setup-{#AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
SetupIconFile=resources\avatar.ico
UninstallDisplayIcon={app}\cishen-assistant.exe
InfoBeforeFile=NOTICE.txt

[Languages]
Name: "chinesesimp"; MessagesFile: ".\installer\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\cishen-assistant\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\次神助手"; Filename: "{app}\cishen-assistant.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\次神助手"; Filename: "{app}\cishen-assistant.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\cishen-assistant.exe"; Description: "{cm:LaunchProgram,次神助手}"; Flags: nowait postinstall skipifsilent
