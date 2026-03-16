@description('Azure OpenAI account name')
param name string

@description('Resource location')
param location string

@description('Resource tags')
param tags object = {}

@description('GPT-4o deployment name')
param deploymentName string = 'gpt-4o'

module cognitiveServices 'br/public:avm/res/cognitive-services/account:0.9.1' = {
  name: '${name}-deploy'
  params: {
    name: name
    location: location
    tags: tags
    kind: 'OpenAI'
    sku: 'S0'
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
    deployments: [
      {
        name: deploymentName
        model: {
          format: 'OpenAI'
          name: 'gpt-4o'
          version: '2024-11-20'
        }
        sku: {
          name: 'Standard'
          capacity: 30
        }
      }
    ]
  }
}

output endpoint string = cognitiveServices.outputs.endpoint
output name string = cognitiveServices.outputs.name
output resourceId string = cognitiveServices.outputs.resourceId
