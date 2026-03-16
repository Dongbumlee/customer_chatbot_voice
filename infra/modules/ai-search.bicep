@description('Azure AI Search service name')
param name string

@description('Resource location')
param location string

@description('Resource tags')
param tags object = {}

module searchService 'br/public:avm/res/search/search-service:0.8.1' = {
  name: '${name}-deploy'
  params: {
    name: name
    location: location
    tags: tags
    sku: 'basic'
    replicaCount: 1
    partitionCount: 1
  }
}

output endpoint string = 'https://${name}.search.windows.net'
output name string = searchService.outputs.name
output resourceId string = searchService.outputs.resourceId
