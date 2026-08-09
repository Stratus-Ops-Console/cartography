from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.container_apps as container_apps
from tests.data.azure.container_apps import API_APP_ID
from tests.data.azure.container_apps import INTERNAL_ENVIRONMENT_ID
from tests.data.azure.container_apps import MOCK_APPS
from tests.data.azure.container_apps import MOCK_ENVIRONMENTS
from tests.data.azure.container_apps import PUBLIC_ENVIRONMENT_ID
from tests.data.azure.container_apps import WORKER_APP_ID
from tests.integration.cartography.intel.azure.common import (
    create_test_azure_subscription,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.container_apps.get_container_apps")
@patch("cartography.intel.azure.container_apps.get_container_apps_environments")
def test_sync_container_apps(mock_get_environments, mock_get_apps, neo4j_session):
    """
    Test that Container Apps environments and apps sync with their
    containment relationships.
    """
    # Arrange
    mock_get_environments.return_value = MOCK_ENVIRONMENTS
    mock_get_apps.return_value = MOCK_APPS
    create_test_azure_subscription(neo4j_session, TEST_SUBSCRIPTION_ID, TEST_UPDATE_TAG)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    container_apps.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert environments, including the internal-LB exposure gate.
    assert check_nodes(
        neo4j_session,
        "AzureContainerAppsEnvironment",
        ["id", "name", "internal_load_balancer"],
    ) == {
        (PUBLIC_ENVIRONMENT_ID, "env-public", None),
        (INTERNAL_ENVIRONMENT_ID, "env-internal", True),
    }

    # Assert apps, including ingress exposure fields.
    assert check_nodes(
        neo4j_session,
        "AzureContainerApp",
        ["id", "name", "ingress_external", "fqdn"],
    ) == {
        (
            API_APP_ID,
            "api-app",
            True,
            "api-app.purplefield-12345678.eastus.azurecontainerapps.io",
        ),
        (WORKER_APP_ID, "worker-app", None, None),
    }

    # Apps carry the cross-provider ComputeService ontology label.
    compute_service_ids = {
        record["id"]
        for record in neo4j_session.run(
            "MATCH (a:AzureContainerApp:ComputeService) RETURN a.id AS id"
        )
    }
    assert compute_service_ids == {API_APP_ID, WORKER_APP_ID}

    # Assert the subscription contains everything as sub-resources.
    assert check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureContainerAppsEnvironment",
        "id",
        "RESOURCE",
    ) == {
        (TEST_SUBSCRIPTION_ID, PUBLIC_ENVIRONMENT_ID),
        (TEST_SUBSCRIPTION_ID, INTERNAL_ENVIRONMENT_ID),
    }
    assert check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureContainerApp",
        "id",
        "RESOURCE",
    ) == {
        (TEST_SUBSCRIPTION_ID, API_APP_ID),
        (TEST_SUBSCRIPTION_ID, WORKER_APP_ID),
    }

    # Assert containment: environment -> apps (including via the legacy
    # managedEnvironmentId field).
    assert check_rels(
        neo4j_session,
        "AzureContainerAppsEnvironment",
        "id",
        "AzureContainerApp",
        "id",
        "HAS_APP",
    ) == {
        (PUBLIC_ENVIRONMENT_ID, API_APP_ID),
        (INTERNAL_ENVIRONMENT_ID, WORKER_APP_ID),
    }
