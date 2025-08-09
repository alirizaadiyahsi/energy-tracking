$workflowFiles = Get-ChildItem -Path ".github\workflows" -Filter "*.yml"

foreach ($file in $workflowFiles) {
    Write-Host "Updating $($file.Name)..."
    
    $content = Get-Content $file.FullName -Raw
    
    # Update deprecated actions
    $content = $content -replace 'actions/upload-artifact@v3', 'actions/upload-artifact@v4'
    $content = $content -replace 'actions/download-artifact@v3', 'actions/download-artifact@v4'
    $content = $content -replace 'actions/checkout@v3', 'actions/checkout@v4'
    $content = $content -replace 'actions/setup-python@v4', 'actions/setup-python@v5'
    $content = $content -replace 'actions/setup-node@v3', 'actions/setup-node@v4'
    $content = $content -replace 'actions/cache@v3', 'actions/cache@v4'
    $content = $content -replace 'actions/create-release@v1', 'softprops/action-gh-release@v1'
    
    # Write back to file
    Set-Content -Path $file.FullName -Value $content -NoNewline
    
    Write-Host "Updated $($file.Name)"
}

Write-Host "All workflow files have been updated!"
