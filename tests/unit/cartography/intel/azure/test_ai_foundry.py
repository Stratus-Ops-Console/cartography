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
