@description('The name of the Digital Twin application')
param appName string = 'digital-twin'

@description('The location for all resources')
param location string = resourceGroup().location

@description('Environment (dev, staging, prod)')
param environment string = 'prod'

@description('Container image tag')
param imageTag string = 'latest'

@description('Container registry server')
param registryServer string = ''

@description('Container registry username')
param registryUsername string = ''

@description('Container registry password')
param registryPassword string = ''

@description('OpenAI API Key')
param openaiApiKey string = ''

@description('Azure Search Endpoint')
param searchEndpoint string = ''

@description('Azure Search Key')
param searchKey string = ''

@description('Azure Search Index')
param searchIndex string = 'digital-twin-index'

@description('Application Insights Connection String')
param appInsightsConnectionString string = ''

// Variables
var containerAppName = '${appName}-${environment}'
var logAnalyticsWorkspaceName = '${appName}-logs-${environment}'
var containerRegistryName = '${appName}registry${uniqueString(resourceGroup().id)}'

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Container Registry (if not provided)
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = if (empty(registryServer)) {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// Container Apps Environment
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${appName}-env-${environment}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

// Container App
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        allowInsecure: false
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
      registries: [
        {
          server: empty(registryServer) ? containerRegistry.properties.loginServer : registryServer
          username: empty(registryServer) ? containerRegistry.name : registryUsername
          passwordSecretRef: 'registry-password'
        }
      ]
      secrets: [
        {
          name: 'registry-password'
          value: empty(registryServer) ? containerRegistry.listCredentials().passwords[0].value : registryPassword
        }
        {
          name: 'openai-api-key'
          value: openaiApiKey
        }
        {
          name: 'azure-search-key'
          value: searchKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'digital-twin'
          image: empty(registryServer) ? '${containerRegistry.properties.loginServer}/digital-twin:${imageTag}' : '${registryServer}/digital-twin:${imageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'MODE'
              value: environment
            }
            {
              name: 'OPENAI_API_KEY'
              secretRef: 'openai-api-key'
            }
            {
              name: 'AZURE_SEARCH_ENDPOINT'
              value: searchEndpoint
            }
            {
              name: 'AZURE_SEARCH_KEY'
              secretRef: 'azure-search-key'
            }
            {
              name: 'AZURE_INDEX'
              value: searchIndex
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsightsConnectionString
            }
            {
              name: 'PORT'
              value: '8000'
            }
          ]
          probes: [
            {
              type: 'readiness'
              httpGet: {
                path: '/health'
                port: 8000
                httpHeaders: [
                  {
                    name: 'Host'
                    value: 'localhost'
                  }
                ]
              }
              initialDelaySeconds: 10
              periodSeconds: 5
            }
            {
              type: 'liveness'
              httpGet: {
                path: '/health'
                port: 8000
                httpHeaders: [
                  {
                    name: 'Host'
                    value: 'localhost'
                  }
                ]
              }
              initialDelaySeconds: 30
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
output containerAppUrl string = containerApp.properties.configuration.ingress.fqdn
output containerAppName string = containerApp.name
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id 