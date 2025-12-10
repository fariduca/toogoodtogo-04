# Database Backup Script
# Usage: .\scripts\backup_db.ps1

param(
    [string]$BackupDir = ".\backups",
    [int]$RetentionDays = 7
)

# Load environment variables
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, [EnvironmentVariableTarget]::Process)
        }
    }
}

$DatabaseUrl = $env:DATABASE_URL

if (-not $DatabaseUrl) {
    Write-Host "❌ DATABASE_URL environment variable not set" -ForegroundColor Red
    Write-Host "   Please configure DATABASE_URL in .env file" -ForegroundColor Yellow
    exit 1
}

# Parse DATABASE_URL
# Format: postgresql://user:password@host:port/dbname
if ($DatabaseUrl -match 'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)') {
    $DbUser = $matches[1]
    $DbPassword = $matches[2]
    $DbHost = $matches[3]
    $DbPort = $matches[4]
    $DbName = $matches[5]
} else {
    Write-Host "❌ Invalid DATABASE_URL format" -ForegroundColor Red
    Write-Host "   Expected: postgresql://user:password@host:port/dbname" -ForegroundColor Yellow
    exit 1
}

# Create backup directory if it doesn't exist
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
    Write-Host "✅ Created backup directory: $BackupDir" -ForegroundColor Green
}

# Generate backup filename with timestamp
$Timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$BackupFile = Join-Path $BackupDir "backup_$Timestamp.sql"

Write-Host "🔄 Starting database backup..." -ForegroundColor Cyan
Write-Host "   Database: $DbName"
Write-Host "   Host: $DbHost:$DbPort"
Write-Host "   Backup file: $BackupFile"

# Set PostgreSQL password environment variable
$env:PGPASSWORD = $DbPassword

try {
    # Run pg_dump
    $pgDumpArgs = @(
        "-h", $DbHost,
        "-p", $DbPort,
        "-U", $DbUser,
        "-d", $DbName,
        "-F", "p",  # Plain text format
        "-f", $BackupFile,
        "--no-owner",
        "--no-acl"
    )

    $process = Start-Process -FilePath "pg_dump" -ArgumentList $pgDumpArgs -NoNewWindow -Wait -PassThru

    if ($process.ExitCode -eq 0) {
        $BackupSize = (Get-Item $BackupFile).Length / 1MB
        Write-Host "✅ Backup completed successfully!" -ForegroundColor Green
        Write-Host "   Size: $([math]::Round($BackupSize, 2)) MB"
        Write-Host "   Location: $BackupFile"
    } else {
        Write-Host "❌ Backup failed with exit code: $($process.ExitCode)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Backup failed: $_" -ForegroundColor Red
    exit 1
} finally {
    # Clear password from environment
    $env:PGPASSWORD = $null
}

# Clean up old backups
Write-Host "`n🧹 Cleaning up old backups (retention: $RetentionDays days)..." -ForegroundColor Cyan

$CutoffDate = (Get-Date).AddDays(-$RetentionDays)
$OldBackups = Get-ChildItem -Path $BackupDir -Filter "backup_*.sql" | 
              Where-Object { $_.LastWriteTime -lt $CutoffDate }

if ($OldBackups) {
    foreach ($OldBackup in $OldBackups) {
        Remove-Item $OldBackup.FullName -Force
        Write-Host "   Removed: $($OldBackup.Name)" -ForegroundColor Yellow
    }
    Write-Host "✅ Removed $($OldBackups.Count) old backup(s)" -ForegroundColor Green
} else {
    Write-Host "   No old backups to remove" -ForegroundColor Gray
}

# List current backups
Write-Host "`n📁 Current backups:" -ForegroundColor Cyan
$CurrentBackups = Get-ChildItem -Path $BackupDir -Filter "backup_*.sql" | Sort-Object LastWriteTime -Descending
foreach ($Backup in $CurrentBackups) {
    $Size = $Backup.Length / 1MB
    Write-Host "   $($Backup.Name) - $([math]::Round($Size, 2)) MB - $($Backup.LastWriteTime)" -ForegroundColor Gray
}

Write-Host "`n✨ Backup process complete!" -ForegroundColor Green
