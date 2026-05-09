# Test script for SHL Assessment Recommender API
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
    Write-Host "  Health check passed" -ForegroundColor Green
} catch {
    Write-Host "  Health check failed: $_" -ForegroundColor Red
    Write-Host "  Make sure the API is running (python run.py)" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test 2: Simple Chat Request
Write-Host "Test 2: Simple Chat Request" -ForegroundColor Yellow
$body = @{
    messages = @(
        @{
            role = "user"
            content = "I need to hire a Java developer"
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/chat" -Method Post -Body $body -ContentType "application/json"
    Write-Host "  Reply: $($response.reply.Substring(0, [Math]::Min(100, $response.reply.Length)))..." -ForegroundColor Green
    Write-Host "  Recommendations: $($response.recommendations.Count)" -ForegroundColor Green
    Write-Host "  End of conversation: $($response.end_of_conversation)" -ForegroundColor Green
    Write-Host "  Chat request passed" -ForegroundColor Green
} catch {
    Write-Host "  Chat request failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 3: Multi-turn Conversation
Write-Host "Test 3: Multi-turn Conversation" -ForegroundColor Yellow
$body = @{
    messages = @(
        @{
            role = "user"
            content = "I need a developer"
        },
        @{
            role = "assistant"
            content = "What programming language or technology stack are you looking for?"
        },
        @{
            role = "user"
            content = "Python, mid-level"
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/chat" -Method Post -Body $body -ContentType "application/json"
    Write-Host "  Reply: $($response.reply.Substring(0, [Math]::Min(100, $response.reply.Length)))..." -ForegroundColor Green
    Write-Host "  Recommendations: $($response.recommendations.Count)" -ForegroundColor Green
    
    if ($response.recommendations.Count -gt 0) {
        Write-Host "  Sample recommendation: $($response.recommendations[0].name)" -ForegroundColor Green
    }
    
    Write-Host "  Multi-turn conversation passed" -ForegroundColor Green
} catch {
    Write-Host "  Multi-turn conversation failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 4: Off-topic Request
Write-Host "Test 4: Off-topic Request (should refuse)" -ForegroundColor Yellow
$body = @{
    messages = @(
        @{
            role = "user"
            content = "What is the weather today"
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/chat" -Method Post -Body $body -ContentType "application/json"
    
    if ($response.recommendations.Count -eq 0 -and $response.end_of_conversation -eq $true) {
        Write-Host "  Correctly refused off-topic request" -ForegroundColor Green
        Write-Host "  Reply: $($response.reply.Substring(0, [Math]::Min(100, $response.reply.Length)))..." -ForegroundColor Green
    } else {
        Write-Host "  Did not refuse off-topic request properly" -ForegroundColor Red
    }
} catch {
    Write-Host "  Off-topic test failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
