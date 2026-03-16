@description('Cosmos DB account name')
param accountName string

@description('Database name')
param databaseName string

@description('Resource location')
param location string

@description('Resource tags')
param tags object = {}

module cosmosAccount 'br/public:avm/res/document-db/database-account:0.11.1' = {
  name: '${accountName}-deploy'
  params: {
    name: accountName
    location: location
    tags: tags
    defaultConsistencyLevel: 'Session'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    sqlDatabases: [
      {
        name: databaseName
        containers: [
          {
            name: 'chat-sessions'
            paths: ['/user_id']
          }
          {
            name: 'chat-messages'
            paths: ['/session_id']
            defaultTtl: 2592000 // 30 days
          }
          {
            name: 'user-profiles'
            paths: ['/id']
          }
          {
            name: 'products'
            paths: ['/category']
          }
        ]
      }
    ]
  }
}

output endpoint string = cosmosAccount.outputs.endpoint
output accountName string = cosmosAccount.outputs.name
output resourceId string = cosmosAccount.outputs.resourceId
