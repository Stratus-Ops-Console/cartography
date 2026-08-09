import cartography.intel.azure.container_apps as container_apps
from tests.data.azure.container_apps import API_APP_ID
from tests.data.azure.container_apps import INTERNAL_ENVIRONMENT_ID
from tests.data.azure.container_apps import MOCK_APPS
from tests.data.azure.container_apps import MOCK_ENVIRONMENTS
from tests.data.azure.container_apps import PUBLIC_ENVIRONMENT_ID
from tests.data.azure.container_apps import WORKER_APP_ID


def test_transform_container_apps_environments() -> None:
    data = container_apps.transform_container_apps_environments(MOCK_ENVIRONMENTS)

    assert data == [
        {
            "id": PUBLIC_ENVIRONMENT_ID,
            "name": "env-public",
            "location": "eastus",
            "provisioning_state": "Succeeded",
            "default_domain": "purplefield-12345678.eastus.azurecontainerapps.io",
            "static_ip": "20.1.2.3",
            "public_network_access": "Enabled",
            "internal_load_balancer": None,
            "zone_redundant": False,
        },
        {
            "id": INTERNAL_ENVIRONMENT_ID,
            "name": "env-internal",
            "location": "eastus",
            "provisioning_state": "Succeeded",
            "default_domain": "internal.greenhill-87654321.eastus.azurecontainerapps.io",
            "static_ip": "10.0.4.4",
            "public_network_access": None,
            "internal_load_balancer": True,
            "zone_redundant": True,
        },
    ]


def test_transform_container_apps() -> None:
    data = container_apps.transform_container_apps(MOCK_APPS)

    assert data == [
        {
            "id": API_APP_ID,
            "name": "api-app",
            "location": "eastus",
            "provisioning_state": "Succeeded",
            "environment_id": PUBLIC_ENVIRONMENT_ID,
            "fqdn": "api-app.purplefield-12345678.eastus.azurecontainerapps.io",
            "ingress_external": True,
            "target_port": 8080,
            "allow_insecure": False,
            "workload_profile_name": "Consumption",
            "latest_revision_name": "api-app--rev1",
            "identity_principal_ids": ["sp-301"],
        },
        {
            # No ingress: exposure fields are None. The legacy
            # managedEnvironmentId field still resolves the environment link.
            "id": WORKER_APP_ID,
            "name": "worker-app",
            "location": "eastus",
            "provisioning_state": "Succeeded",
            "environment_id": INTERNAL_ENVIRONMENT_ID,
            "fqdn": None,
            "ingress_external": None,
            "target_port": None,
            "allow_insecure": None,
            "workload_profile_name": None,
            "latest_revision_name": "worker-app--rev4",
            "identity_principal_ids": [],
        },
    ]
