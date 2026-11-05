[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$stateFile = Join-Path $root 'rendu/processus.json'
function Stop-Arbre([int]$ProcessId) {
    $enfants = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId" -ErrorAction SilentlyContinue)
    # Arrêter le superviseur avant ses enfants pour empêcher leur redémarrage.
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    foreach ($enfant in $enfants) { Stop-Arbre ([int]$enfant.ProcessId) }
}
if (Test-Path $stateFile) {
    $state = @(Get-Content $stateFile -Raw | ConvertFrom-Json)
    [array]::Reverse($state)
    foreach ($entry in $state) {
        $proc = Get-Process -Id $entry.pid -ErrorAction SilentlyContinue
        # ConvertFrom-Json peut convertir les dates ISO en DateTime sous PowerShell 7.
        # Comparer les ticks UTC évite une comparaison chaîne/date dépendante de version.
        if ($proc -and $proc.StartTime.ToUniversalTime().Ticks -eq ([datetime]$entry.debut).ToUniversalTime().Ticks) {
            Stop-Arbre ([int]$entry.pid)
        }
    }
}
Start-Sleep -Seconds 1
$resultat = foreach ($port in 5000,8100,8101) {
    $listen = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
    if ($listen.Count) { throw "Port $port encore occupe : intervention necessaire." }
    $test = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback,$port)
    $test.Server.ExclusiveAddressUse = $true
    try { $test.Start() }
    catch { throw "Port $port non disponible au test de liaison TCP." }
    finally { $test.Stop() }
    "Port $port libre (aucune ecoute TCP, liaison exclusive reussie)"
}
$resultat | Tee-Object -FilePath (Join-Path $root 'reports/preuves/arret_ports.txt')
if (Test-Path $stateFile) { Remove-Item -LiteralPath $stateFile }
