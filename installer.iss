; -----------------------------------------------------------------------------
; WeekNumber - Inno Setup script
;
; Build:
;   1. Run build.bat to produce dist\WeekNumber.exe
;   2. Open this file in Inno Setup Compiler (or run iscc.exe installer.iss)
;
; Output: dist\WeekNumberSetup.exe
; -----------------------------------------------------------------------------

#define MyAppName        "WeekNumber"
#define MyAppVersion     "1.0.0"
#define MyAppPublisher   "WeekNumber"
#define MyAppExeName     "WeekNumber.exe"
#define MyAppId          "{{C3E4A5B6-7D8F-49A1-B2C3-D4E5F6A7B8C9}}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=WeekNumberSetup
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[CustomMessages]
english.AutoStartTask=Start &WeekNumber automatically when Windows starts
english.DesktopIconTask=Create a &desktop shortcut
turkish.AutoStartTask=Windows ba&şladığında WeekNumber'ı otomatik başlat
turkish.DesktopIconTask=&Masaüstü kısayolu oluştur

[Tasks]
Name: "autostart";   Description: "{cm:AutoStartTask}";  GroupDescription: "{cm:AdditionalIcons}"
Name: "desktopicon"; Description: "{cm:DesktopIconTask}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\WeekNumber.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.ico";        DestDir: "{app}"; Flags: ignoreversion
Source: "README.md";           DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}";            Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}";  Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}";    Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}";      Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: shellexec nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{userstartup}\{#MyAppName}.lnk"
Type: files; Name: "{userappdata}\Microsoft\Windows\Start Menu\Programs\Startup\WeekNumber.lnk"

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Exec('taskkill.exe', '/F /IM WeekNumber.exe', '', SW_HIDE,
       ewWaitUntilTerminated, ResultCode);
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
    Exec('taskkill.exe', '/F /IM WeekNumber.exe', '', SW_HIDE,
         ewWaitUntilTerminated, ResultCode);
end;
