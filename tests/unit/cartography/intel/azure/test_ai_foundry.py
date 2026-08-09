from unittest.mock import MagicMock

import cartography.intel.azure.ai_foundry as ai_foundry
from tests.data.azure.ai_foundry import FOUNDRY_ACCOUNT_ID
from tests.data.azure.ai_foundry import GPT4O_DEPLOYMENT_ID
from tests.data.azure.ai_foundry import MOCK_ACCOUNTS
from tests.data.azure.ai_foundry import MOCK_FOUNDRY_DEPLOYMENTS
from tests.data.azure.ai_foundry import MOCK_PROJECTS


def _fake_account(kind: str, payload: dict) -> MagicMock:
    account = MagicMock(kind=kind)
    account.as_dict.return_value = payload
    return account


def test_get_ai_foundry_accounts_filters_to_ai_kinds() -> None:
    client = MagicMock()
    client.accounts.list.return_value = [
        _fake_account("AIServices", MOCK_ACCOUNTS[0]),
        _fake_account("OpenAI", MOCK_ACCOUNTS[1]),
        # Single-purpose cognitive services are out of scope.
        _fake_account("Face", {"id": "face-1", "name": "face-1"}),
        _fake_account("SpeechServices", {"id": "speech-1", "name": "speech-1"}),
    ]

    accounts = ai_foundry.get_ai_foundry_accounts(client, "00-00-00-00")

    assert accounts == [MOCK_ACCOUNTS[0], MOCK_ACCOUNTS[1]]


def test_transform_ai_foundry_accounts() -> None:
    data = ai_foundry.transform_ai_foundry_accounts(MOCK_ACCOUNTS)

    assert data == [
        {
            "id": FOUNDRY_ACCOUNT_ID,
            "name": "foundry-prod",
            "kind": "AIServices",
            "location": "eastus",
            "endpoint": "https://foundry-prod.cognitiveservices.azure.com/",
            "provisioning_state": "Succeeded",
            "public_network_access": "Enabled",
            "disable_local_auth": True,
            "custom_sub_domain_name": "foundry-prod",
            "sku_name": "S0",
            "identity_principal_ids": ["sp-201"],
        },
        {
            "id": MOCK_ACCOUNTS[1]["id"],
            "name": "openai-legacy",
            "kind": "OpenAI",
            "location": "westeurope",
            "endpoint": "https://openai-legacy.openai.azure.com/",
            "provisioning_state": "Succeeded",
            "public_network_access": "Enabled",
            "disable_local_auth": False,
            "custom_sub_domain_name": "openai-legacy",
            "sku_name": "S0",
            "identity_principal_ids": [],
        },
    ]


def test_transform_ai_foundry_projects_stamps_account_id() -> None:
    data = ai_foundry.transform_ai_foundry_projects(MOCK_PROJECTS, FOUNDRY_ACCOUNT_ID)

    assert [p["account_id"] for p in data] == [FOUNDRY_ACCOUNT_ID] * 2
    assert data[0]["display_name"] == "Customer Agents"
    assert data[0]["is_default"] is True
    assert data[0]["identity_principal_ids"] == ["sp-202"]
    # Optional fields absent from the payload come through as None/empty.
    assert data[1]["description"] is None
    assert data[1]["identity_principal_ids"] == []


def test_transform_ai_foundry_deployments_flattens_model_and_sku() -> None:
    data = ai_foundry.transform_ai_foundry_deployments(
        MOCK_FOUNDRY_DEPLOYMENTS, FOUNDRY_ACCOUNT_ID
    )

    assert data == [
        {
            "id": GPT4O_DEPLOYMENT_ID,
            "name": "gpt-4o",
            "provisioning_state": "Succeeded",
            "model_name": "gpt-4o",
            "model_version": "2024-08-06",
            "model_format": "OpenAI",
            "model_publisher": "OpenAI",
            "sku_name": "GlobalStandard",
            "sku_capacity": 50,
            "rai_policy_name": "Microsoft.DefaultV2",
            "account_id": FOUNDRY_ACCOUNT_ID,
        },
    ]


def test_transform_ai_foundry_connections_account_scope() -> None:
    from tests.data.azure.ai_foundry import MOCK_ACCOUNT_CONNECTIONS
    from tests.data.azure.ai_foundry import SEARCH_CONNECTION_ID

    data = ai_foundry.transform_ai_foundry_connections(
        MOCK_ACCOUNT_CONNECTIONS, account_id=FOUNDRY_ACCOUNT_ID
    )

    assert data == [
        {
            "id": SEARCH_CONNECTION_ID,
            "name": "search-shared",
            "category": "CognitiveSearch",
            "auth_type": "AAD",
            "target": "https://estate-search.search.windows.net/",
            "target_resource_id": (
                "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/"
                "Microsoft.Search/searchServices/estate-search"
            ),
            "is_shared_to_all": True,
            "scope": "account",
            "account_id": FOUNDRY_ACCOUNT_ID,
            "project_id": None,
        },
    ]


def test_transform_ai_foundry_connections_project_scope() -> None:
    from tests.data.azure.ai_foundry import AGENTS_PROJECT_ID
    from tests.data.azure.ai_foundry import KEY_VAULT_RESOURCE_ID
    from tests.data.azure.ai_foundry import MOCK_PROJECT_CONNECTIONS

    data = ai_foundry.transform_ai_foundry_connections(
        MOCK_PROJECT_CONNECTIONS, project_id=AGENTS_PROJECT_ID
    )

    assert [c["scope"] for c in data] == ["project", "project"]
    assert [c["account_id"] for c in data] == [None, None]
    assert [c["project_id"] for c in data] == [AGENTS_PROJECT_ID] * 2
    # Lowercase resourceId metadata spelling still resolves the ARM id.
    assert data[0]["target_resource_id"] == KEY_VAULT_RESOURCE_ID
    # No metadata at all: no target resource id, auth type still surfaced.
    assert data[1]["target_resource_id"] is None
    assert data[1]["auth_type"] == "ApiKey"


def test_transform_ai_foundry_agents() -> None:
    from tests.data.azure.ai_foundry import AGENTS_PROJECT_ID
    from tests.data.azure.ai_foundry import GPT4O_DEPLOYMENT_ID
    from tests.data.azure.ai_foundry import MOCK_AGENTS
    from tests.data.azure.ai_foundry import SUPPORT_AGENT_ID
    from tests.data.azure.ai_foundry import TRIAGE_AGENT_ID

    data = ai_foundry.transform_ai_foundry_agents(
        MOCK_AGENTS, AGENTS_PROJECT_ID, FOUNDRY_ACCOUNT_ID
    )

    assert data[0] == {
        "id": SUPPORT_AGENT_ID,
        "agent_guid": "agt_11111111",
        "name": "support-agent",
        "state": "enabled",
        "description": "Answers customer support tickets",
        "kind": "prompt",
        "model": "gpt-4o",
        "instructions": "Help customers with their tickets.",
        "tool_types": ["file_search", "mcp"],
        "version": "3",
        "created_at": "2026-08-01T10:00:00Z",
        "identity_principal_ids": ["sp-203"],
        "project_id": AGENTS_PROJECT_ID,
        "model_deployment_id": GPT4O_DEPLOYMENT_ID,
    }
    # No instance identity -> empty principal list; no tools -> empty list.
    assert data[1]["id"] == TRIAGE_AGENT_ID
    assert data[1]["identity_principal_ids"] == []
    assert data[1]["tool_types"] == []
    assert data[1]["model_deployment_id"] == GPT4O_DEPLOYMENT_ID
