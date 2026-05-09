# PowerShell script to convert approach.md to PDF

Write-Host "Converting approach.md to PDF..." -ForegroundColor Cyan
Write-Host ""

# Check if pandoc is installed
$pandocInstalled = Get-Command pandoc -ErrorAction SilentlyContinue

if ($pandocInstalled) {
    Write-Host "Using Pandoc to convert..." -ForegroundColor Green
    pandoc docs/approach.md -o approach.pdf --pdf-engine=wkhtmltopdf
    
    if (Test-Path "approach.pdf") {
        Write-Host "✓ PDF created successfully: approach.pdf" -ForegroundColor Green
    } else {
        Write-Host "✗ PDF creation failed" -ForegroundColor Red
    }
} else {
    Write-Host "Pandoc not found. Alternative options:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option 1: Install Pandoc" -ForegroundColor White
    Write-Host "  Visit: https://pandoc.org/installing.html" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Option 2: Use VS Code" -ForegroundColor White
    Write-Host "  1. Install 'Markdown PDF' extension" -ForegroundColor Gray
    Write-Host "  2. Open docs/approach.md" -ForegroundColor Gray
    Write-Host "  3. Right-click → 'Markdown PDF: Export (pdf)'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Option 3: Use Online Converter" -ForegroundColor White
    Write-Host "  Visit: https://www.markdowntopdf.com/" -ForegroundColor Gray
    Write-Host "  Upload: docs/approach.md" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Option 4: Print to PDF from Browser" -ForegroundColor White
    Write-Host "  1. Open docs/approach.md in VS Code" -ForegroundColor Gray
    Write-Host "  2. Press Ctrl+Shift+V (Markdown Preview)" -ForegroundColor Gray
    Write-Host "  3. Right-click → 'Open Preview to the Side'" -ForegroundColor Gray
    Write-Host "  4. In preview, press Ctrl+P → 'Save as PDF'" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
