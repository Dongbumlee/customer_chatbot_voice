@description('Azure Speech Services account name')
param name string

@description('Resource location')
param location string

@description('Resource tags')
param tags object = {}

module speechAccount 'br/public:avm/res/cognitive-services/account:0.9.1' = {
  name: '${name}-deploy'
  params: {
    name: name
    location: location
    tags: tags
    kind: 'SpeechServices'
    sku: 'S0'
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
  }
}

output endpoint string = speechAccount.outputs.endpoint
output name string = speechAccount.outputs.name
output resourceId string = speechAccount.outputs.resourceId
