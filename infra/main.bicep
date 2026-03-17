targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment (e.g., dev, staging, prod)')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Resource group name override')
param resourceGroupName string = ''

// Azure OpenAI
@description('Azure OpenAI account name')
param openAiAccountName string = ''
@description('Azure OpenAI GPT-4o deployment name')
param openAiDeploymentName string = 'gpt-4o'

// Cosmos DB
@description('Cosmos DB account name')
param cosmosAccountName string = ''
@description('Cosmos DB database name')
param cosmosDatabaseName string = 'customer-chatbot'

// Storage
@description('Storage account name')
param storageAccountName string = ''

// Container Apps
@description('Container registry name')
param containerRegistryName string = ''

// AI Search
@description('Azure AI Search service name')
param searchServiceName string = ''

// Key Vault
@description('Key Vault name')
param keyVaultName string = ''

// Speech Services
@description('Azure Speech Services account name')
param speechAccountName string = ''

var abbrs = loadJsonContent('./abbreviations.json')
var tags = { 'azd-env-name': environmentName }
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// Log Analytics workspace
module logAnalytics './modules/log-analytics.bicep' = {
  name: 'log-analytics'
  scope: rg
  params: {
    name: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    location: location
    tags: tags
  }
}

// Container Registry
module containerRegistry './modules/container-registry.bicep' = {
  name: 'container-registry'
  scope: rg
  params: {
    name: !empty(containerRegistryName) ? containerRegistryName : '${abbrs.containerRegistryRegistries}${resourceToken}'
    location: location
    tags: tags
  }
}

// Container Apps Environment
module containerAppsEnv './modules/container-apps-env.bicep' = {
  name: 'container-apps-env'
  scope: rg
  params: {
    name: '${abbrs.appManagedEnvironments}${resourceToken}'
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalytics.outputs.id
  }
}

// Cosmos DB (deployed to eastus2 due to East US AZ capacity limits)
module cosmosDb './modules/cosmos-db.bicep' = {
  name: 'cosmos-db'
  scope: rg
  params: {
    accountName: !empty(cosmosAccountName) ? cosmosAccountName : '${abbrs.documentDBDatabaseAccounts}${resourceToken}'
    databaseName: cosmosDatabaseName
    location: 'eastus2'
    tags: tags
  }
}

// Storage Account
module storage './modules/storage.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    name: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
    location: location
    tags: tags
  }
}

// Key Vault
module keyVault './modules/key-vault.bicep' = {
  name: 'key-vault'
  scope: rg
  params: {
    name: !empty(keyVaultName) ? keyVaultName : '${abbrs.keyVaultVaults}${resourceToken}'
    location: location
    tags: tags
  }
}

// Azure AI Search
module aiSearch './modules/ai-search.bicep' = {
  name: 'ai-search'
  scope: rg
  params: {
    name: !empty(searchServiceName) ? searchServiceName : '${abbrs.searchSearchServices}${resourceToken}'
    location: location
    tags: tags
  }
}

// Azure OpenAI
module openAi './modules/openai.bicep' = {
  name: 'openai'
  scope: rg
  params: {
    name: !empty(openAiAccountName) ? openAiAccountName : '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    location: location
    tags: tags
    deploymentName: openAiDeploymentName
  }
}

// Azure Speech Services
module speechServices './modules/speech-services.bicep' = {
  name: 'speech-services'
  scope: rg
  params: {
    name: !empty(speechAccountName) ? speechAccountName : '${abbrs.cognitiveServicesSpeech}${resourceToken}'
    location: location
    tags: tags
  }
}

// Container App — API
module apiContainerApp './modules/container-app.bicep' = {
  name: 'container-app-api'
  scope: rg
  params: {
    name: '${abbrs.appContainerApps}api-${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'api' })
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerRegistryLoginServer: containerRegistry.outputs.loginServer
    containerRegistryName: containerRegistry.outputs.name
    targetPort: 8000
  }
}

// Container App — Web
module webContainerApp './modules/container-app.bicep' = {
  name: 'container-app-web'
  scope: rg
  params: {
    name: '${abbrs.appContainerApps}web-${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'web' })
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerRegistryLoginServer: containerRegistry.outputs.loginServer
    containerRegistryName: containerRegistry.outputs.name
    targetPort: 80
  }
}

// ── RBAC Role Assignments for API Container App ─────────────────────────────

// Cosmos DB Built-in Data Contributor (SQL RBAC — not standard ARM role)
module cosmosRbac 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.1' = {
  name: 'cosmos-rbac'
  scope: rg
  params: {
    principalId: apiContainerApp.outputs.principalId
    roleDefinitionId: '/subscriptions/${subscription().subscriptionId}/resourceGroups/${rg.name}/providers/Microsoft.DocumentDB/databaseAccounts/${cosmosDb.outputs.accountName}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalType: 'ServicePrincipal'
    resourceId: cosmosDb.outputs.resourceId
  }
}

// Cognitive Services User on Azure OpenAI
var cognitiveServicesUserRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')

module openAiRbac 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.1' = {
  name: 'openai-rbac'
  scope: rg
  params: {
    principalId: apiContainerApp.outputs.principalId
    roleDefinitionId: cognitiveServicesUserRoleId
    principalType: 'ServicePrincipal'
    resourceId: openAi.outputs.resourceId
  }
}

// Cognitive Services User on Speech Services
module speechRbac 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.1' = {
  name: 'speech-rbac'
  scope: rg
  params: {
    principalId: apiContainerApp.outputs.principalId
    roleDefinitionId: cognitiveServicesUserRoleId
    principalType: 'ServicePrincipal'
    resourceId: speechServices.outputs.resourceId
  }
}

// Storage Blob Data Reader on Storage Account
module storageRbac 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.1' = {
  name: 'storage-rbac'
  scope: rg
  params: {
    principalId: apiContainerApp.outputs.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
    principalType: 'ServicePrincipal'
    resourceId: storage.outputs.id
  }
}

// Outputs for azd
output AZURE_COSMOS_ENDPOINT string = cosmosDb.outputs.endpoint
output AZURE_COSMOS_DATABASE_NAME string = cosmosDatabaseName
output AZURE_STORAGE_ACCOUNT_NAME string = storage.outputs.name
output AZURE_SEARCH_ENDPOINT string = aiSearch.outputs.endpoint
output AZURE_KEYVAULT_URL string = keyVault.outputs.uri
output AZURE_OPENAI_ENDPOINT string = openAi.outputs.endpoint
output AZURE_CONTAINER_REGISTRY_LOGIN_SERVER string = containerRegistry.outputs.loginServer
output AZURE_CONTAINER_APPS_ENVIRONMENT_ID string = containerAppsEnv.outputs.id
output AZURE_SPEECH_ENDPOINT string = speechServices.outputs.endpoint
output API_URL string = apiContainerApp.outputs.fqdn
output WEB_URL string = webContainerApp.outputs.fqdn
