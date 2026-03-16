@description('Container Registry name')
param name string

@description('Resource location')
param location string

@description('Resource tags')
param tags object = {}

module registry 'br/public:avm/res/container-registry/registry:0.6.0' = {
  name: '${name}-deploy'
  params: {
    name: name
    location: location
    tags: tags
    acrSku: 'Basic'
    acrAdminUserEnabled: true
  }
}

output loginServer string = registry.outputs.loginServer
output name string = registry.outputs.name
output resourceId string = registry.outputs.resourceId
