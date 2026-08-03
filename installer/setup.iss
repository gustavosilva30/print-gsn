[Setup]
AppName=GSN Print Service
AppVersion=0.1.0
DefaultDirName={pf}\GSN Print Service
DefaultGroupName=GSN Print Service
OutputBaseFilename=gsn-print-service-setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\gsn-print-service\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\GSN Print Service"; Filename: "{app}\gsn-print-service.exe"
