@description('Container Apps Environment name')
param name string

@description('Resource location')
param location string

@description('Resource tags')
param tags object = {}

@description('Log Analytics workspace resource ID')
param logAnalyticsWorkspaceId string

module managedEnvironment 'br/public:avm/res/app/managed-environment:0.8.1' = {
  name: '${name}-deploy'
  params: {
    name: name
    location: location
    tags: tags
    logAnalyticsWorkspaceResourceId: logAnalyticsWorkspaceId
    zoneRedundant: false
  }
}

output id string = managedEnvironment.outputs.resourceId
output name string = managedEnvironment.outputs.name
