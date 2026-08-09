# Mock payloads in the shape produced by azure-mgmt-appcontainers
# model.as_dict() (camelCase ARM wire format).

PUBLIC_ENVIRONMENT_ID = (
    "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/"
    "Microsoft.App/managedEnvironments/env-public"
)
INTERNAL_ENVIRONMENT_ID = (
    "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/"
    "Microsoft.App/managedEnvironments/env-internal"
)

MOCK_ENVIRONMENTS = [
    {
        "id": PUBLIC_ENVIRONMENT_ID,
        "name": "env-public",
        "location": "eastus",
        "properties": {
            "provisioningState": "Succeeded",
            "defaultDomain": "purplefield-12345678.eastus.azurecontainerapps.io",
            "staticIp": "20.1.2.3",
            "publicNetworkAccess": "Enabled",
            "zoneRedundant": False,
        },
    },
    {
        # VNet-integrated environment behind an internal load balancer:
        # external ingress on its apps is not publicly reachable.
        "id": INTERNAL_ENVIRONMENT_ID,
        "name": "env-internal",
        "location": "eastus",
        "properties": {
            "provisioningState": "Succeeded",
            "defaultDomain": "internal.greenhill-87654321.eastus.azurecontainerapps.io",
            "staticIp": "10.0.4.4",
            "zoneRedundant": True,
            "vnetConfiguration": {
                "internal": True,
                "infrastructureSubnetId": (
                    "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/"
                    "Microsoft.Network/virtualNetworks/vnet1/subnets/aca"
                ),
            },
        },
    },
]

API_APP_ID = (
    "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/"
    "Microsoft.App/containerApps/api-app"
)
WORKER_APP_ID = (
    "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/"
    "Microsoft.App/containerApps/worker-app"
)

MOCK_APPS = [
    {
        "id": API_APP_ID,
        "name": "api-app",
        "location": "eastus",
        "identity": {
            "type": "SystemAssigned",
            "principalId": "sp-301",
            "tenantId": "tenant-123",
        },
        "properties": {
            "provisioningState": "Succeeded",
            "environmentId": PUBLIC_ENVIRONMENT_ID,
            "workloadProfileName": "Consumption",
            "latestRevisionName": "api-app--rev1",
            "configuration": {
                "activeRevisionsMode": "Single",
                "ingress": {
                    "external": True,
                    "fqdn": "api-app.purplefield-12345678.eastus.azurecontainerapps.io",
                    "targetPort": 8080,
                    "allowInsecure": False,
                },
            },
        },
    },
    {
        # Background worker: no ingress block at all, legacy environment field.
        "id": WORKER_APP_ID,
        "name": "worker-app",
        "location": "eastus",
        "properties": {
            "provisioningState": "Succeeded",
            "managedEnvironmentId": INTERNAL_ENVIRONMENT_ID,
            "latestRevisionName": "worker-app--rev4",
            "configuration": {
                "activeRevisionsMode": "Single",
            },
        },
    },
]
