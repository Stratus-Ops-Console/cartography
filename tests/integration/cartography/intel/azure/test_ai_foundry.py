from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.ai_foundry as ai_foundry
from tests.data.azure.ai_foundry import AGENTS_PROJECT_ID
from tests.data.azure.ai_foundry import CUSTOM_CONNECTION_ID
from tests.data.azure.ai_foundry import EMBEDDING_DEPLOYMENT_ID
from tests.data.azure.ai_foundry import EVALS_PROJECT_ID
from tests.data.azure.ai_foundry import FOUNDRY_ACCOUNT_ID
from tests.data.azure.ai_foundry import GPT4O_DEPLOYMENT_ID
from tests.data.azure.ai_foundry import KEY_VAULT_RESOURCE_ID
from tests.data.azure.ai_foundry import KV_CONNECTION_ID
from tests.data.azure.ai_foundry import MOCK_ACCOUNT_CONNECTIONS
from tests.data.azure.ai_foundry import MOCK_ACCOUNTS
from tests.data.azure.ai_foundry import MOCK_FOUNDRY_DEPLOYMENTS
from tests.data.azure.ai_foundry import MOCK_OPENAI_DEPLOYMENTS
from tests.data.azure.ai_foundry import MOCK_PROJECT_CONNECTIONS
from tests.data.azure.ai_foundry import MOCK_PROJECTS
from tests.data.azure.ai_foundry import OPENAI_ACCOUNT_ID
from tests.data.azure.ai_foundry import SEARCH_CONNECTION_ID
from tests.integration.cartography.intel.azure.common import (
    create_test_azure_subscription,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.ai_foundry.get_ai_foundry_project_connections")
@patch("cartography.intel.azure.ai_foundry.get_ai_foundry_account_connections")
@patch("cartography.intel.azure.ai_foundry.get_ai_foundry_deployments")
@patch("cartography.intel.azure.ai_foundry.get_ai_foundry_projects")
@patch("cartography.intel.azure.ai_foundry.get_ai_foundry_accounts")
def test_sync_ai_foundry(
    mock_get_accounts,
    mock_get_projects,
    mock_get_deployments,
    mock_get_account_connections,
    mock_get_project_connections,
    neo4j_session,
):
    """
    Test that accounts, projects, model deployments and connections sync with
    their containment relationships.
    """
    # Arrange
    mock_get_accounts.return_value = MOCK_ACCOUNTS
    # Projects are only listed for the AIServices account.
    mock_get_projects.return_value = MOCK_PROJECTS
    # One deployments call per account, in accounts order.
    mock_get_deployments.side_effect = [
        MOCK_FOUNDRY_DEPLOYMENTS,
        MOCK_OPENAI_DEPLOYMENTS,
    ]
    # One account-connections call per account; one project-connections call
    # per project of the AIServices account.
    mock_get_account_connections.side_effect = [MOCK_ACCOUNT_CONNECTIONS, []]
    mock_get_project_connections.side_effect = [MOCK_PROJECT_CONNECTIONS, []]
    create_test_azure_subscription(neo4j_session, TEST_SUBSCRIPTION_ID, TEST_UPDATE_TAG)
    # A Key Vault ingested by the key vault sync, targeted by kv-agents.
    neo4j_session.run(
        "MERGE (kv:AzureKeyVault{id: $kv_id}) SET kv.lastupdated = $update_tag",
        kv_id=KEY_VAULT_RESOURCE_ID,
        update_tag=TEST_UPDATE_TAG,
    )
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    ai_foundry.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert accounts, including the key-auth posture flag.
    assert check_nodes(
        neo4j_session,
        "AzureAIFoundryAccount",
        ["id", "kind", "disable_local_auth"],
    ) == {
        (FOUNDRY_ACCOUNT_ID, "AIServices", True),
        (OPENAI_ACCOUNT_ID, "OpenAI", False),
    }

    # Assert projects.
    assert check_nodes(
        neo4j_session,
        "AzureAIFoundryProject",
        ["id", "display_name", "is_default"],
    ) == {
        (AGENTS_PROJECT_ID, "Customer Agents", True),
        (EVALS_PROJECT_ID, "Model Evals", False),
    }

    # Assert deployments.
    assert check_nodes(
        neo4j_session,
        "AzureAIFoundryDeployment",
        ["id", "model_name", "sku_name"],
    ) == {
        (GPT4O_DEPLOYMENT_ID, "gpt-4o", "GlobalStandard"),
        (EMBEDDING_DEPLOYMENT_ID, "text-embedding-3-large", "Standard"),
    }

    # Deployments carry the cross-provider AIModel ontology label.
    ai_model_ids = {
        record["id"]
        for record in neo4j_session.run(
            "MATCH (d:AzureAIFoundryDeployment:AIModel) RETURN d.id AS id"
        )
    }
    assert ai_model_ids == {GPT4O_DEPLOYMENT_ID, EMBEDDING_DEPLOYMENT_ID}

    # Assert the subscription contains everything as sub-resources.
    assert check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureAIFoundryAccount",
        "id",
        "RESOURCE",
    ) == {
        (TEST_SUBSCRIPTION_ID, FOUNDRY_ACCOUNT_ID),
        (TEST_SUBSCRIPTION_ID, OPENAI_ACCOUNT_ID),
    }
    assert check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureAIFoundryProject",
        "id",
        "RESOURCE",
    ) == {
        (TEST_SUBSCRIPTION_ID, AGENTS_PROJECT_ID),
        (TEST_SUBSCRIPTION_ID, EVALS_PROJECT_ID),
    }
    assert check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureAIFoundryDeployment",
        "id",
        "RESOURCE",
    ) == {
        (TEST_SUBSCRIPTION_ID, GPT4O_DEPLOYMENT_ID),
        (TEST_SUBSCRIPTION_ID, EMBEDDING_DEPLOYMENT_ID),
    }

    # Assert connections, including auth posture and scope.
    assert check_nodes(
        neo4j_session,
        "AzureAIFoundryConnection",
        ["id", "auth_type", "scope"],
    ) == {
        (SEARCH_CONNECTION_ID, "AAD", "account"),
        (KV_CONNECTION_ID, "ManagedIdentity", "project"),
        (CUSTOM_CONNECTION_ID, "ApiKey", "project"),
    }

    # Account-scoped connection hangs off the account; project-scoped off the
    # project only.
    assert check_rels(
        neo4j_session,
        "AzureAIFoundryAccount",
        "id",
        "AzureAIFoundryConnection",
        "id",
        "HAS_CONNECTION",
    ) == {(FOUNDRY_ACCOUNT_ID, SEARCH_CONNECTION_ID)}
    assert check_rels(
        neo4j_session,
        "AzureAIFoundryProject",
        "id",
        "AzureAIFoundryConnection",
        "id",
        "HAS_CONNECTION",
    ) == {
        (AGENTS_PROJECT_ID, KV_CONNECTION_ID),
        (AGENTS_PROJECT_ID, CUSTOM_CONNECTION_ID),
    }

    # A resource-backed connection links to the target node the key vault
    # sync ingested.
    assert check_rels(
        neo4j_session,
        "AzureAIFoundryConnection",
        "id",
        "AzureKeyVault",
        "id",
        "CONNECTS_TO",
        rel_direction_right=True,
    ) == {(KV_CONNECTION_ID, KEY_VAULT_RESOURCE_ID)}

    # Assert containment: account -> projects, account -> deployments.
    assert check_rels(
        neo4j_session,
        "AzureAIFoundryAccount",
        "id",
        "AzureAIFoundryProject",
        "id",
        "HAS_PROJECT",
    ) == {
        (FOUNDRY_ACCOUNT_ID, AGENTS_PROJECT_ID),
        (FOUNDRY_ACCOUNT_ID, EVALS_PROJECT_ID),
    }
    assert check_rels(
        neo4j_session,
        "AzureAIFoundryAccount",
        "id",
        "AzureAIFoundryDeployment",
        "id",
        "HAS_DEPLOYMENT",
    ) == {
        (FOUNDRY_ACCOUNT_ID, GPT4O_DEPLOYMENT_ID),
        (OPENAI_ACCOUNT_ID, EMBEDDING_DEPLOYMENT_ID),
    }
