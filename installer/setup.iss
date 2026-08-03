; GSN Print Service - Inno Setup script
; Compile with Inno Setup 6+ after running release.bat

#define MyAppName "GSN Print Service"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "GSN"
#define MyAppExeName "gsn-print-service.exe"
#define MyAppId "{{A7C3E2B1-4F8D-4A91-9C2E-1B6D5E8F0A12}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\GSN Print Service
DefaultGroupName=GSN Print Service
OutputDir=..\dist\installer
OutputBaseFilename=gsn-print-service-setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=no
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked
Name: "installservice"; Description: "Instalar como Serviço Windows (recomendado)"; GroupDescription: "Serviço:"; Flags: checkedonce
Name: "starttray"; Description: "Iniciar com ícone na bandeja após a instalação"; GroupDescription: "Serviço:"; Flags: unchecked

[Files]
; Main PyInstaller output (one-folder build)
Source: "..\dist\gsn-print-service\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Ensure writable data dirs exist as placeholders
Source: "..\app\config\config.json"; DestDir: "{app}\app\config"; Flags: ignoreversion onlyifdoesntexist

[Dirs]
Name: "{app}\app\logs"; Permissions: users-modify
Name: "{app}\app\database"; Permissions: users-modify
Name: "{app}\app\config"; Permissions: users-modify

[Icons]
Name: "{group}\GSN Print Service"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--tray"
Name: "{group}\GSN Print Service (Headless)"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--headless"
Name: "{group}\Desinstalar"; Filename: "{uninstallexe}"
Name: "{autodesktop}\GSN Print Service"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--tray"; Tasks: desktopicon

[Run]
; Optional: register Windows service using the installed executable host
Filename: "{app}\{#MyAppExeName}"; Parameters: "--install-service"; StatusMsg: "Registrando serviço Windows..."; Tasks: installservice; Flags: runhidden waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Parameters: "--start-service"; StatusMsg: "Iniciando serviço..."; Tasks: installservice; Flags: runhidden waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Parameters: "--tray"; Description: "Abrir GSN Print Service na bandeja"; Flags: nowait postinstall skipifsilent; Tasks: starttray

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--stop-service"; Flags: runhidden waituntilterminated; RunOnceId: "StopGSNService"
Filename: "{app}\{#MyAppExeName}"; Parameters: "--uninstall-service"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveGSNService"

[Code]
function InitializeWizard: Boolean;
begin
  Result := True;
end;
