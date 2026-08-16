param(
    [string]$Repository = "zk935217486-sys/minimax-h3-video-studio",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$files = @(
    ".gitignore",
    ".github/workflows/pages.yml",
    "README.md",
    "index.html",
    "styles.css",
    "app.js",
    "backend/__init__.py",
    "backend/config.py",
    "backend/errors.py",
    "backend/db.py",
    "backend/main.py",
    "backend/ai_prompt_matcher.py",
    "backend/video_engine.py",
    "backend/user_system.py",
    "backend/account_manager.py",
    "backend/proxy_manager.py",
    "backend/account_factory.py",
    "backend/requirements.txt",
    "config/config.yaml",
    "scripts/start.sh",
    "scripts/sync-github.ps1",
    "workflows/minimax_free.json",
    "tests/test_backend_foundation.py",
    "tests/test_ai_prompt_matcher.py",
    "tests/test_video_engine.py",
    "tests/test_user_and_accounts.py"
)

Set-Location $projectRoot

if ($DryRun) {
    foreach ($path in $files) {
        if (-not (Test-Path -LiteralPath $path)) {
            throw "Missing file: $path"
        }
        Write-Host "READY  $path" -ForegroundColor Cyan
    }
    Write-Host "Dry run passed: $($files.Count) files are ready." -ForegroundColor Green
    exit 0
}

& gh auth status
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: gh auth login"
}

foreach ($path in $files) {
    $remotePath = $path.Replace("\", "/")
    $endpoint = "repos/$Repository/contents/$remotePath"
    $content = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $path)))
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $sha = & gh api $endpoint --jq ".sha" 2>$null
    $lookupExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorAction

    if ($lookupExitCode -eq 0 -and $sha) {
        & gh api --method PUT $endpoint `
            -f message="update: $remotePath" `
            -f content=$content `
            -f sha=$sha `
            --jq ".content.path"
    } else {
        & gh api --method PUT $endpoint `
            -f message="add: $remotePath" `
            -f content=$content `
            --jq ".content.path"
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Upload failed: $remotePath"
    }
}

Write-Host "GitHub sync complete." -ForegroundColor Green
Write-Host "Repository: https://github.com/$Repository"
Write-Host "Website: https://zk935217486-sys.github.io/minimax-h3-video-studio/"
