# Script to set YouTube API key
# Usage: .\set_youtube_api.ps1 "YOUR_API_KEY_HERE"

param(
    [Parameter(Mandatory=$false)]
    [string]$ApiKey
)

if (-not $ApiKey) {
    Write-Host "=" * 80
    Write-Host "YOUTUBE API KEY CONFIGURATION" -ForegroundColor Cyan
    Write-Host "=" * 80
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\set_youtube_api.ps1 `"YOUR_API_KEY_HERE`""
    Write-Host ""
    Write-Host "Steps to get API key:" -ForegroundColor Green
    Write-Host "  1. Go to https://console.cloud.google.com/"
    Write-Host "  2. Create new project (or select existing)"
    Write-Host "  3. Enable YouTube Data API v3"
    Write-Host "  4. Create Credentials > API Key"
    Write-Host "  5. Copy the API key"
    Write-Host ""
    Write-Host "Current API key status:" -ForegroundColor Yellow
    if ($env:YOUTUBE_API_KEY) {
        Write-Host "  [OK] API key is set: $($env:YOUTUBE_API_KEY.Substring(0, 10))..." -ForegroundColor Green
    } else {
        Write-Host "  [NOT SET] No API key configured" -ForegroundColor Red
    }
    Write-Host ""
    exit
}

# Set environment variable for current session
$env:YOUTUBE_API_KEY = $ApiKey

Write-Host ""
Write-Host "=" * 80
Write-Host "[OK] YouTube API Key Set Successfully!" -ForegroundColor Green
Write-Host "=" * 80
Write-Host ""
Write-Host "API Key: $($ApiKey.Substring(0, 10))...(hidden)" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now run:" -ForegroundColor Yellow
Write-Host "  python modules/youtube_scraper.py UCaxnllxL894OHbc_6VQcGmA --max-videos 100"
Write-Host ""
Write-Host "Note: This key is set for current PowerShell session only." -ForegroundColor Yellow
Write-Host "To make it permanent, add to your PowerShell profile or system environment variables."
Write-Host ""
