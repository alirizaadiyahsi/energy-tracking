#!/usr/bin/env pwsh
# Generate placeholder images for screenshots

Write-Host "🖼️ Creating placeholder images for screenshots..." -ForegroundColor Cyan

$screenshotsDir = "./screenshots"
$placeholders = @{
    "dashboard.png" = @{
        "title" = "Dashboard Screenshot"
        "url" = "http://localhost:3000/dashboard"
        "description" = "Real-time energy monitoring dashboard"
    }
    "analytics.png" = @{
        "title" = "Analytics Screenshot" 
        "url" = "http://localhost:3000/analytics"
        "description" = "Analytics portal with data visualization"
    }
    "devices.png" = @{
        "title" = "Devices Screenshot"
        "url" = "http://localhost:3000/devices" 
        "description" = "IoT device management interface"
    }
    "login.png" = @{
        "title" = "Login Screenshot"
        "url" = "http://localhost:3000/login"
        "description" = "Authentication system interface"
    }
    "api-docs.png" = @{
        "title" = "API Documentation Screenshot"
        "url" = "http://localhost:8000/docs"
        "description" = "Interactive API documentation (Swagger)"
    }
    "grafana.png" = @{
        "title" = "Grafana Screenshot"
        "url" = "http://localhost:3001"
        "description" = "System monitoring dashboards"
    }
}

foreach ($file in $placeholders.Keys) {
    $info = $placeholders[$file]
    $svgContent = @"
<svg width="800" height="450" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="800" height="450" fill="url(#grad1)"/>
  <rect x="50" y="50" width="700" height="350" fill="none" stroke="#ffffff" stroke-width="2" stroke-dasharray="10,5"/>
  
  <!-- Camera Icon -->
  <g transform="translate(375, 180)">
    <rect x="-30" y="-15" width="60" height="40" rx="5" fill="#ffffff" opacity="0.8"/>
    <circle cx="0" cy="0" r="12" fill="none" stroke="#ffffff" stroke-width="2"/>
    <circle cx="0" cy="0" r="6" fill="#ffffff"/>
    <rect x="-40" y="-20" width="15" height="8" rx="3" fill="#ffffff" opacity="0.8"/>
  </g>
  
  <!-- Title -->
  <text x="400" y="280" font-family="Arial, sans-serif" font-size="24" font-weight="bold" 
        text-anchor="middle" fill="#ffffff">$($info.title)</text>
  
  <!-- Description -->
  <text x="400" y="310" font-family="Arial, sans-serif" font-size="16" 
        text-anchor="middle" fill="#ffffff" opacity="0.9">$($info.description)</text>
  
  <!-- URL -->
  <text x="400" y="340" font-family="Arial, sans-serif" font-size="14" 
        text-anchor="middle" fill="#ffffff" opacity="0.8">$($info.url)</text>
        
  <!-- Placeholder Notice -->
  <text x="400" y="380" font-family="Arial, sans-serif" font-size="12" 
        text-anchor="middle" fill="#ffffff" opacity="0.7">📷 Placeholder - Replace with actual screenshot</text>
</svg>
"@

    $svgPath = Join-Path $screenshotsDir ($file -replace "\.png$", ".svg")
    $svgContent | Out-File -FilePath $svgPath -Encoding UTF8
    Write-Host "✅ Created placeholder: $svgPath" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Navigate to each URL while the system is running" -ForegroundColor White
Write-Host "2. Capture actual screenshots with the exact filenames" -ForegroundColor White  
Write-Host "3. Replace the SVG files with PNG screenshots" -ForegroundColor White
Write-Host "4. Commit and push the changes" -ForegroundColor White
Write-Host ""
Write-Host "💡 The SVG placeholders will show properly on GitHub until replaced" -ForegroundColor Gray
