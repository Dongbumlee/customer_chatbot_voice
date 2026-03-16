$ErrorActionPreference = "Stop"

# 1. Get Cosmos DB connection string
Write-Host "=== Step 1: Getting Cosmos DB connection string ==="
$cosmosConnStr = az cosmosdb keys list --name cosmos-otbmznhzumuxi --resource-group rg-chatbot-voice --type connection-strings --query "connectionStrings[0].connectionString" -o tsv
Write-Host "Got connection string (length: $($cosmosConnStr.Length))"

# 2. Get API Container App principal ID for RBAC
Write-Host "`n=== Step 2: Getting Container App managed identity ==="
$apiPrincipalId = az containerapp show --name ca-api-otbmznhzumuxi --resource-group rg-chatbot-voice --query "identity.principalId" -o tsv
Write-Host "API Principal ID: $apiPrincipalId"

# 3. Assign RBAC roles
Write-Host "`n=== Step 3: Assigning RBAC roles ==="

# Cosmos DB Data Contributor
$cosmosId = az cosmosdb show --name cosmos-otbmznhzumuxi --resource-group rg-chatbot-voice --query "id" -o tsv
az role assignment create --assignee-object-id $apiPrincipalId --assignee-principal-type ServicePrincipal --role "00000000-0000-0000-0000-000000000002" --scope $cosmosId 2>$null
Write-Host "Assigned: Cosmos DB Built-in Data Contributor"

# Cognitive Services OpenAI User
$oaiId = az cognitiveservices account show --name oai-otbmznhzumuxi --resource-group rg-chatbot-voice --query "id" -o tsv
az role assignment create --assignee-object-id $apiPrincipalId --assignee-principal-type ServicePrincipal --role "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" --scope $oaiId 2>$null
Write-Host "Assigned: Cognitive Services OpenAI User"

# Search Index Data Reader
$searchId = az search service show --name srch-otbmznhzumuxi --resource-group rg-chatbot-voice --query "id" -o tsv
az role assignment create --assignee-object-id $apiPrincipalId --assignee-principal-type ServicePrincipal --role "1407120a-92aa-4202-b7e9-c0e197c71c8f" --scope $searchId 2>$null
Write-Host "Assigned: Search Index Data Reader"

# Storage Blob Data Reader
$storageId = az storage account show --name stotbmznhzumuxi --resource-group rg-chatbot-voice --query "id" -o tsv
az role assignment create --assignee-object-id $apiPrincipalId --assignee-principal-type ServicePrincipal --role "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1" --scope $storageId 2>$null
Write-Host "Assigned: Storage Blob Data Reader"

# 4. Update API container app env vars with correct values
Write-Host "`n=== Step 4: Updating API environment variables ==="
az containerapp update --name ca-api-otbmznhzumuxi --resource-group rg-chatbot-voice `
    --set-env-vars `
    "COSMOS_CONNECTION_STRING=$cosmosConnStr" `
    "COSMOS_DATABASE_NAME=customer-chatbot" `
    "AZURE_OPENAI_ENDPOINT=https://oai-otbmznhzumuxi.openai.azure.com/" `
    "AZURE_OPENAI_DEPLOYMENT=gpt-4o" `
    "AZURE_OPENAI_API_VERSION=2024-12-01-preview" `
    "AZURE_SEARCH_ENDPOINT=https://srch-otbmznhzumuxi.search.windows.net" `
    "AZURE_SEARCH_INDEX_NAME=products-policies" `
    "AZURE_STORAGE_ACCOUNT_NAME=stotbmznhzumuxi" `
    "AZURE_KEYVAULT_URL=https://kv-otbmznhzumuxi.vault.azure.net/" `
    "AZURE_VOICE_ENDPOINT=" `
    "AZURE_VOICE_KEY=" `
    "AZURE_VOICE_REGION=eastus" `
    "AZURE_TENANT_ID=52b39610-0746-4c25-a83d-d4f89fadedfe" `
    "AZURE_CLIENT_ID=2c9b02f3-a06c-418c-9874-58a29847aaaf" `
    'ALLOWED_ORIGINS=["https://ca-web-otbmznhzumuxi.proudtree-a9193637.eastus.azurecontainerapps.io","http://localhost:5173"]' `
    "LOG_LEVEL=INFO" `
    --output none
Write-Host "API env vars updated"

Write-Host "`n=== Done ==="
Write-Host "Waiting 10s for container to restart..."
Start-Sleep -Seconds 10

# 5. Test health endpoint
Write-Host "`n=== Step 5: Testing health endpoint ==="
try {
    $health = Invoke-RestMethod -Uri "https://ca-api-otbmznhzumuxi.proudtree-a9193637.eastus.azurecontainerapps.io/api/health" -TimeoutSec 30
    Write-Host "Health: $($health | ConvertTo-Json -Compress)"
} catch {
    Write-Host "Health check failed: $($_.Exception.Message)"
}
