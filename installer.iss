[Setup]
AppName=Beatport Track Finder
AppVersion=1.0
DefaultDirName={pf}\Beatport Track Finder
DefaultGroupName=Beatport Track Finder
OutputBaseFilename=BeatportTrackFinderSetup
Compression=lzma
SolidCompression=yes
DisableDirPage=no
DisableProgramGroupPage=no
UninstallDisplayIcon={app}\BeatportTrackFinder.exe
OutputDir=installer_output

[Files]
; Main executable
Source: "dist\Beatport Track Finder\*"; DestDir: "{app}"; Flags: recursesubdirs

; Chrome WebDriver
Source: "chromedriver.exe"; DestDir: "{app}"

; Additional files
Source: "preferences.json"; DestDir: "{app}"; Flags: onlyifdoesntexist

[Icons]
Name: "{group}\Beatport Track Finder"; Filename: "{app}\Beatport Track Finder.exe"
Name: "{commondesktop}\Beatport Track Finder"; Filename: "{app}\Beatport Track Finder.exe"

[Run]
Filename: "{app}\Beatport Track Finder.exe"; Description: "Launch Beatport Track Finder"; Flags: postinstall nowait

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not RegKeyExists(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe') then
  begin
    MsgBox('Google Chrome is required but not installed. Please install Google Chrome before continuing.', mbInformation, MB_OK);
    Result := False;
  end;
end;