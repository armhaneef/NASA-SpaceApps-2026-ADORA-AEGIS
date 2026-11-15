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

    & git -C $moduleRoot check-ignore --quiet -- .env *> $null
    if ($LASTEXITCODE -ne 0) {
        throw 'ai-assistant/.env is not ignored by Git.'
    }

    $secureInput = Read-Host -Prompt 'Paste your Gemini API key (input is hidden)' -AsSecureString
    if ($null -eq $secureInput -or $secureInput.Length -eq 0) {
        throw 'No key was entered.'
    }

    $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureInput)
    $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
    if ([string]::IsNullOrWhiteSpace($plainKey) -or $plainKey.Contains("`r") -or $plainKey.Contains("`n")) {
        throw 'The entered value is empty or invalid.'
    }

    $updatedLines = [System.Collections.Generic.List[string]]::new()
    $keyWritten = $false
    foreach ($line in [System.IO.File]::ReadAllLines($envPath)) {
        if ($line -match '^\s*GEMINI_API_KEY\s*=') {
            if (-not $keyWritten) {
                $updatedLines.Add('GEMINI_API_KEY=' + $plainKey)
                $keyWritten = $true
            }
            continue
        }
        $updatedLines.Add($line)
    }
    if (-not $keyWritten) {
        $updatedLines.Add('GEMINI_API_KEY=' + $plainKey)
    }

    $tempPath = $envPath + '.' + [guid]::NewGuid().ToString('N') + '.tmp'
    [System.IO.File]::WriteAllLines($tempPath, $updatedLines, [System.Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tempPath -Destination $envPath -Force

    $keyLines = @([System.IO.File]::ReadAllLines($envPath) | Where-Object { $_ -match '^\s*GEMINI_API_KEY\s*=' })
    if ($keyLines.Count -ne 1 -or [string]::IsNullOrWhiteSpace(($keyLines[0] -replace '^\s*GEMINI_API_KEY\s*=\s*', ''))) {
        throw 'The key entry could not be verified.'
    }

    Push-Location $moduleRoot
    try {
        $check = & python -c "from app.core.config import settings; print('GEMINI KEY: ' + ('YES' if settings.gemini_api_key else 'NO'))" 2>$null
        if ($LASTEXITCODE -ne 0 -or $check -notcontains 'GEMINI KEY: YES') {
            throw 'The Python settings loader did not detect the key.'
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
    [Console]::WriteLine("GEMINI KEY CONFIGURED: $status")
}
