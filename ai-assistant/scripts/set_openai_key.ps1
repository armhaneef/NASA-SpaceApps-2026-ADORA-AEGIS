$ErrorActionPreference = 'Stop'

$secureInput = $null
$plainKey = $null
$keyPointer = [IntPtr]::Zero
$status = 'NO'

try {
    $moduleRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    $envPath = Join-Path $moduleRoot '.env'
    if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) {
        throw 'ai-assistant/.env does not exist.'
    }

    # Refuse to write a credential unless Git ignores this exact local file.
    & git -C $moduleRoot check-ignore --quiet -- .env *> $null
    if ($LASTEXITCODE -ne 0) {
        throw 'ai-assistant/.env is not ignored by Git.'
    }

    $secureInput = Read-Host -Prompt 'Paste your OpenAI API key (input is hidden)' -AsSecureString
    if ($null -eq $secureInput -or $secureInput.Length -eq 0) {
        throw 'No key was entered.'
    }

    $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureInput)
    $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
    if ([string]::IsNullOrWhiteSpace($plainKey) -or $plainKey.Contains("`r") -or $plainKey.Contains("`n")) {
        throw 'The entered value is empty or invalid.'
    }

    # Preserve every other setting and replace all canonical key entries with one.
    $updatedLines = [System.Collections.Generic.List[string]]::new()
    foreach ($line in [System.IO.File]::ReadAllLines($envPath)) {
        if ($line -notmatch '^\s*OPENAI_API_KEY\s*=') {
            $updatedLines.Add($line)
        }
    }
    $updatedLines.Add('OPENAI_API_KEY=' + $plainKey)

    # UTF-8 without BOM is compatible with python-dotenv. Replace atomically.
    $tempPath = $envPath + '.tmp'
    [System.IO.File]::WriteAllLines($tempPath, $updatedLines, [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::Move($tempPath, $envPath, $true)

    $keyLines = @([System.IO.File]::ReadAllLines($envPath) | Where-Object { $_ -match '^\s*OPENAI_API_KEY\s*=' })
    if ($keyLines.Count -ne 1 -or [string]::IsNullOrWhiteSpace(($keyLines[0] -replace '^\s*OPENAI_API_KEY\s*=\s*', ''))) {
        throw 'The saved key entry could not be verified.'
    }

    # Confirm the application's real dotenv-backed settings loader sees a nonempty key.
    Push-Location $moduleRoot
    try {
        $pythonCheck = & python -c "from app.core.config import settings; print('KEY CONFIGURED: ' + ('YES' if settings.openai_api_key else 'NO'))" 2>$null
        if ($LASTEXITCODE -ne 0 -or $pythonCheck -notcontains 'KEY CONFIGURED: YES') {
            throw 'The Python settings loader did not load a configured key.'
        }
    }
    finally {
        Pop-Location
    }

    $status = 'YES'
}
catch {
    $status = 'NO'
}
finally {
    if ($keyPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
    }
    if ($null -ne $secureInput) {
        $secureInput.Dispose()
    }
    $plainKey = $null
    [Console]::WriteLine("KEY CONFIGURED: $status")
}
