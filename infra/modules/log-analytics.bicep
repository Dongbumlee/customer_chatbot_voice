@description('Log Analytics workspace name')
param name string

@description('Resource location')
param location string

@description('Resource tags')
param tags object = {}

module workspace 'br/public:avm/res/operational-insights/workspace:0.9.1' = {
  name: '${name}-deploy'
  params: {
    name: name
    location: location
    tags: tags
    dataRetention: 30
    skuName: 'PerGB2018'
  }
}

output id string = workspace.outputs.resourceId
output name string = workspace.outputs.name
output customerId string = workspace.outputs.logAnalyticsWorkspaceId
