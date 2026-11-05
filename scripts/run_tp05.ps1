[CmdletBinding()]
param([string]$PythonExe = 'python', [switch]$SansInstallation)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
New-Item -ItemType Directory -Force data,src,models,reports,reports/preuves,rendu | Out-Null
. "$PSScriptRoot/services.ps1"
Assert-PortsLibres
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    & $PythonExe -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Creation du venv impossible.' }
}
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$(Join-Path (Get-Location) '.venv/Scripts');$env:PATH"
$env:MLFLOW_TRACKING_URI = 'http://127.0.0.1:5000'
if (-not $SansInstallation) {
    & $script:Python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw 'Mise a jour pip impossible.' }
    & $script:Python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Installation impossible ; consulter le plan B du README.' }
}
try {
    Invoke-TPPython 'donnees.txt' @('donnees.py')
    Invoke-TPPython 'machine_versions.txt' @('scripts/preuves.py','machine')
    Start-TPService 'mlflow' @('-m','mlflow','server','--host','127.0.0.1','--port','5000','--backend-store-uri','sqlite:///mlflow.db','--default-artifact-root','./mlartifacts') 'http://127.0.0.1:5000/health'
    $automl = 'src/automl_deploy.py'
    if (-not (Select-String -Path requirements.txt -Pattern '^flaml' -Quiet)) { $automl = 'src/automl_deploy_sklearn.py' }
    Invoke-TPPython 'automl.txt' @($automl)
    Invoke-TPPython 'inspection_automl.txt' @('scripts/preuves.py','inspecter','fraude-automl')
    Invoke-TPPython 'manuel.txt' @('src/modele_manuel.py')
    Invoke-TPPython 'inspection_manuel.txt' @('scripts/preuves.py','inspecter','fraude-manuel')
    Invoke-TPPython 'promotion_automl.txt' @('src/promouvoir.py','fraude-automl')
    Invoke-TPPython 'promotion_manuel.txt' @('src/promouvoir.py','fraude-manuel')
    Start-TPService 'service_8100' @('-m','mlflow','models','serve','-m','models:/fraude-automl@production','-p','8100','--env-manager','local') 'http://127.0.0.1:8100/ping'
    Start-TPService 'service_8101' @('-m','mlflow','models','serve','-m','models:/fraude-manuel@production','-p','8101','--env-manager','local') 'http://127.0.0.1:8101/ping'
    # Pas de travail parallele pendant ces quatre mesures.
    $index = 0
    foreach ($port in 8100,8101,8100,8101) {
        $index++
        Invoke-TPPython "client_${index}_${port}.txt" @('src/client.py',"$port")
    }
    Invoke-TPPython 'requetes_invalides.txt' @('scripts/preuves.py','invalide')
    Invoke-TPPython 'comparaison_execution.txt' @('scripts/preuves.py','comparer')
} finally {
    try { & "$PSScriptRoot/stop_services.ps1" }
    finally { if (Test-Path $script:Python) { & $script:Python scripts/preuves.py anonymiser } }
}
