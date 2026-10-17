# Generate local credentials without displaying secrets or overwriting an existing .env.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$envPath = Join-Path $projectRoot '.env'
if (Test-Path -LiteralPath $envPath) {
    throw '.env already exists. Nothing was changed. Review credentials manually.'
}
function New-SiprePassword {
    $buffer = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($buffer) } finally { $rng.Dispose() }
    return ([BitConverter]::ToString($buffer)).Replace('-', '').ToLowerInvariant()
}
$passwords = @{}
foreach ($key in @('POSTGRES_PASSWORD','SIPRE_MIGRATOR_PASSWORD','SIPRE_APP_PASSWORD',
                   'SIPRE_WORKER_PASSWORD','SIPRE_METABASE_READER_PASSWORD','METABASE_APP_PASSWORD',
                   'SIPRE_BOOTSTRAP_PASSWORD','SIPRE_DEMO_PASSWORD')) {
    $passwords[$key] = New-SiprePassword
}
$values = @{}
foreach ($key in $passwords.Keys) { $values[$key] = $passwords[$key] }
$values['SIPRE_DATABASE_URL'] = 'postgresql+psycopg://sipre_app:' + $passwords['SIPRE_APP_PASSWORD'] + '@db:5432/sipre'
$values['SIPRE_MIGRATION_DATABASE_URL'] = 'postgresql+psycopg://sipre_migrator:' + $passwords['SIPRE_MIGRATOR_PASSWORD'] + '@db:5432/sipre'
$values['SIPRE_WORKER_DATABASE_URL'] = 'postgresql+psycopg://sipre_worker:' + $passwords['SIPRE_WORKER_PASSWORD'] + '@db:5432/sipre'
$lockPath = Join-Path $projectRoot 'docker\images.lock.json'
if (-not (Test-Path -LiteralPath $lockPath)) { throw 'Missing image lock; run scripts/resolve-images.py first.' }
$imageLock = Get-Content -Raw -LiteralPath $lockPath | ConvertFrom-Json
foreach ($entry in $imageLock.images.PSObject.Properties) {
    $values[$entry.Name] = $entry.Value.reference
}
$lines = Get-Content -LiteralPath (Join-Path $projectRoot '.env.example')
$output = foreach ($line in $lines) {
    if ($line -match '^([A-Z_]+)=') {
        $key = $Matches[1]
        if ($values.ContainsKey($key)) { $key + '=' + $values[$key] } else { $line }
    } else { $line }
}
$bytes = [Text.UTF8Encoding]::new($false).GetBytes(($output -join "`n") + "`n")
$file = [IO.File]::Open($envPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try { $file.Write($bytes, 0, $bytes.Length) } finally { $file.Dispose() }
Write-Output '.env created with random passwords and pinned images. No secrets printed.'
