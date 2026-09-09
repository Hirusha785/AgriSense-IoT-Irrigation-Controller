# ============================================================
#  com0com Virtual COM Port Setup Script
#  Run this AFTER installing com0com-3.0.0.0 installer
#  Right-click -> Run as Administrator
# ============================================================

Write-Host ""
Write-Host "========================================"
Write-Host "  IoT Irrigation - COM Port Setup"
Write-Host "========================================"
Write-Host ""

# Find com0com setup utility
$setupPaths = @(
    "C:\Program Files (x86)\com0com\setupc.exe",
    "C:\Program Files\com0com\setupc.exe",
    "$env:ProgramFiles\com0com\setupc.exe",
    "${env:ProgramFiles(x86)}\com0com\setupc.exe"
)

$setupc = $setupPaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $setupc) {
    Write-Host "ERROR: com0com is not installed yet!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install com0com first from:" -ForegroundColor Yellow
    Write-Host "  https://sourceforge.net/projects/com0com/files/com0com/3.0.0.0/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "After installing, run this script again." -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "Found com0com at: $setupc" -ForegroundColor Green

# List existing pairs
Write-Host ""
Write-Host "Existing virtual COM port pairs:"
& $setupc list 2>&1

# Check if COM5/COM6 pair already exists
$existing = & $setupc list 2>&1 | Out-String
if ($existing -match "COM5" -and $existing -match "COM6") {
    Write-Host ""
    Write-Host "COM5 <-> COM6 pair already exists!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Creating COM5 <-> COM6 virtual pair..."
    
    # Remove any default pair first (usually CNCA0/CNCB0)
    & $setupc remove 0 2>&1
    
    # Install pair with specific COM numbers
    & $setupc install PortName=COM5 PortName=COM6 2>&1
    
    Write-Host ""
    Write-Host "Pair created. Current pairs:"
    & $setupc list 2>&1
}

# Verify in Windows ports
Write-Host ""
Write-Host "Verifying COM ports in system..."
$ports = [System.IO.Ports.SerialPort]::GetPortNames()
Write-Host "Available COM ports: $($ports -join ', ')"

if ($ports -contains "COM5" -and $ports -contains "COM6") {
    Write-Host ""
    Write-Host "SUCCESS! COM5 and COM6 are ready." -ForegroundColor Green
    Write-Host ""
    Write-Host "Setup:"
    Write-Host "  Proteus COMPIM -> COM5"
    Write-Host "  Python bridge  -> COM6  (set in .env)"
} else {
    Write-Host ""
    Write-Host "WARNING: COM5/COM6 not yet visible. Try rebooting or check Device Manager." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================"
Write-Host "  Done! Now:"
Write-Host "  1. Open Proteus, set COMPIM port = COM5"
Write-Host "  2. Edit .env -> SERIAL_PORT=COM6"
Write-Host "  3. Run: python blynk_bridge.py"
Write-Host "========================================"
pause
