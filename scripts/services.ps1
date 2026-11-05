Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:ProjectRoot = Split-Path $PSScriptRoot -Parent
$script:Python = Join-Path $script:ProjectRoot '.venv/Scripts/python.exe'
$script:StateFile = Join-Path $script:ProjectRoot 'rendu/processus.json'
function Assert-PortsLibres {
    foreach ($port in 5000,8100,8101) {
        $test = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback,$port)
        $test.Server.ExclusiveAddressUse = $true
        try { $test.Start() }
        catch { throw "Port $port indisponible : ne pas arreter un processus etranger au TP." }
        finally { $test.Stop() }
    }
}
function Start-TPService([string]$Nom, [string[]]$Arguments, [string]$Url) {
    $out = Join-Path $script:ProjectRoot "reports/preuves/$Nom.stdout.log"
    $err = Join-Path $script:ProjectRoot "reports/preuves/$Nom.stderr.log"
    $proc = Start-Process -FilePath $script:Python -ArgumentList $Arguments `
        -WorkingDirectory $script:ProjectRoot -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
    $state = @()
    if (Test-Path $script:StateFile) { $state = @(Get-Content $script:StateFile -Raw | ConvertFrom-Json) }
    $state += @{ nom=$Nom; pid=$proc.Id; debut=$proc.StartTime.ToUniversalTime().ToString('o') }
    ConvertTo-Json -InputObject $state | Set-Content $script:StateFile -Encoding UTF8
    $deadline = (Get-Date).AddSeconds(180)
    do {
        if ($proc.HasExited) { throw "Service $Nom termine : consulter $err" }
        try {
            $r = Invoke-WebRequest $Url -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) {
                "$Nom : HTTP 200 $Url" | Tee-Object -FilePath "reports/preuves/$Nom.sante.txt"
                return
            }
        } catch { }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    throw "Delai depasse pour $Nom : consulter les journaux."
}
function Invoke-TPPython([string]$Preuve, [string[]]$Arguments) {
    # PowerShell 5.1 transforme stderr natif en ErrorRecord : redirection vers un fichier.
    $ancien = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $script:Python @Arguments *> "reports/preuves/$Preuve"
    $code = $LASTEXITCODE
    $ErrorActionPreference = $ancien
    Get-Content "reports/preuves/$Preuve"
    if ($code -ne 0) { throw "Echec Python ($code) : $Preuve" }
}
