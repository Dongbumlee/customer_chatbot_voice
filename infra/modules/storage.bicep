@description('Storage account name')
param name string

@description('Resource location')
param location string

@description('Resource tags')
param tags object = {}

module storageAccount 'br/public:avm/res/storage/storage-account:0.14.3' = {
  name: '${name}-deploy'
  params: {
    name: name
    location: location
    tags: tags
    skuName: 'Standard_LRS'
    kind: 'StorageV2'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    blobServices: {
      containers: [
        {
          name: 'policies'
          publicAccess: 'None'
        }
        {
          name: 'product-images'
          publicAccess: 'None'
        }
      ]
    }
  }
}

output name string = storageAccount.outputs.name
output id string = storageAccount.outputs.resourceId
