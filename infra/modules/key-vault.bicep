@description('Key Vault name')
param name string

@description('Resource location')
param location string

@description('Resource tags')
param tags object = {}

module vault 'br/public:avm/res/key-vault/vault:0.11.1' = {
  name: '${name}-deploy'
  params: {
    name: name
    location: location
    tags: tags
    sku: 'standard'
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: false
  }
}

output uri string = vault.outputs.uri
output name string = vault.outputs.name
output resourceId string = vault.outputs.resourceId
