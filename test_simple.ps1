# Simple API Test Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing SHL Assessment Recommender API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Write-Host "  Status: $($response.status)" -ForegroundColor Green
    Write-Host "  ✓ Health check passed" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Health check failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Java Developer Request
Write-Host "Test 2: Java Developer Request" -ForegroundColor Yellow
$body = @{
    messages = @(
        @{
            role = "user"
            content = "I need to hire a senior Java developer"
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/chat" -Method Post -Body $body -ContentType "application/json"
    Write-Host "  Reply: $($response.reply.Substring(0, [Math]::Min(150, $response.reply.Length)))..." -ForegroundColor Green
    Write-Host "  Recommendations: $($response.recommendations.Count)" -ForegroundColor Green
    
    if ($response.recommendations.Count -gt 0) {
        Write-Host "  Sample: $($response.recommendations[0].name)" -ForegroundColor Green
        Write-Host "  URL: $($response.recommendations[0].url)" -ForegroundColor Green
        Write-Host "  Type: $($response.recommendations[0].test_type)" -ForegroundColor Green
    }
    
    Write-Host "  ✓ Java developer request passed" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 3: Python Developer Request
Write-Host "Test 3: Python Developer Request" -ForegroundColor Yellow
$body = @{
    messages = @(
        @{
            role = "user"
            content = "I need Python assessments for mid-level developers"
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/chat" -Method Post -Body $body -ContentType "application/json"
    Write-Host "  Reply: $($response.reply.Substring(0, [Math]::Min(150, $response.reply.Length)))..." -ForegroundColor Green
    Write-Host "  Recommendations: $($response.recommendations.Count)" -ForegroundColor Green
    Write-Host "  ✓ Python developer request passed" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 4: Multi-turn Conversation
Write-Host "Test 4: Multi-turn Conversation" -ForegroundColor Yellow
$body = @{
    messages = @(
        @{
            role = "user"
            content = "I need a developer"
        },
        @{
            role = "assistant"
            content = "What programming language or technology are you looking for?"
        },
        @{
            role = "user"
            content = "JavaScript and React"
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/chat" -Method Post -Body $body -ContentType "application/json"
    Write-Host "  Reply: $($response.reply.Substring(0, [Math]::Min(150, $response.reply.Length)))..." -ForegroundColor Green
    Write-Host "  Recommendations: $($response.recommendations.Count)" -ForegroundColor Green
    Write-Host "  ✓ Multi-turn conversation passed" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your API is working! Try it in your browser:" -ForegroundColor Yellow
Write-Host "  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
