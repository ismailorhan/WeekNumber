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
#define MyRelease        "1.1.0"
; The release is typed once, here and in version.py, and stamp_version.py
; fails the build if the two disagree. What the installer *shows* is the
; release plus the build number, which only exists at build time -- version.py
; is restored before ISCC runs, so the number is handed over in a file.
#if FileExists("installer-version.txt")
  #define VersionFile    FileOpen("installer-version.txt")
  #define MyAppVersion   Trim(FileRead(VersionFile))
  #expr FileClose(VersionFile)
#else
  ; A clean checkout compiled without building first. Honest rather than
  ; fatal: the release is right and only the build number is missing.
  #define MyAppVersion   MyRelease
#endif
#define MyAppPublisher   "ismailorhan"
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
english.DesktopIconTask=Create a &desktop shortcut
turkish.DesktopIconTask=&Masaüstü kısayolu oluştur

[Tasks]
; No auto-start task. It used to write a shortcut into {userstartup}, and this
; installer runs as administrator -- so on a machine where a standard user
; starts the install and types an administrator's password, the shortcut
; landed in a Startup folder that person never signs into. The app writes it
; while running as whoever ticked it, from the tray menu, which is the only
; context in which "the user's Startup folder" means anything.
Name: "desktopicon"; Description: "{cm:DesktopIconTask}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\WeekNumber.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.ico";        DestDir: "{app}"; Flags: ignoreversion
Source: "README.md";           DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}";            Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}";  Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}";    Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

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
