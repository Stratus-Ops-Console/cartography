# Mock payloads in the shape produced by azure-mgmt-cognitiveservices
# model.as_dict() (msrest snake_case with a nested 'properties' dict).

FOUNDRY_ACCOUNT_ID = (
    "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/"
    "Microsoft.CognitiveServices/accounts/foundry-prod"
)
OPENAI_ACCOUNT_ID = (
    "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/"
    "Microsoft.CognitiveServices/accounts/openai-legacy"
)

MOCK_ACCOUNTS = [
    {
        "id": FOUNDRY_ACCOUNT_ID,
        "name": "foundry-prod",
        "kind": "AIServices",
        "location": "eastus",
        "sku": {"name": "S0"},
        "identity": {
            "type": "SystemAssigned",
            "principal_id": "sp-201",
            "tenant_id": "tenant-123",
        },
        "properties": {
            "endpoint": "https://foundry-prod.cognitiveservices.azure.com/",
            "provisioning_state": "Succeeded",
            "public_network_access": "Enabled",
            "disable_local_auth": True,
            "custom_sub_domain_name": "foundry-prod",
        },
    },
    {
        # Standalone Azure OpenAI account: hosts deployments but no projects,
        # and still accepts static API keys (disable_local_auth False).
        "id": OPENAI_ACCOUNT_ID,
        "name": "openai-legacy",
        "kind": "OpenAI",
        "location": "westeurope",
        "sku": {"name": "S0"},
        "properties": {
            "endpoint": "https://openai-legacy.openai.azure.com/",
            "provisioning_state": "Succeeded",
            "public_network_access": "Enabled",
            "disable_local_auth": False,
            "custom_sub_domain_name": "openai-legacy",
        },
    },
]

AGENTS_PROJECT_ID = f"{FOUNDRY_ACCOUNT_ID}/projects/agents"
EVALS_PROJECT_ID = f"{FOUNDRY_ACCOUNT_ID}/projects/evals"

MOCK_PROJECTS = [
    {
        "id": AGENTS_PROJECT_ID,
        "name": "agents",
        "location": "eastus",
        "identity": {
            "type": "SystemAssigned",
            "principal_id": "sp-202",
            "tenant_id": "tenant-123",
        },
        "properties": {
            "display_name": "Customer Agents",
            "description": "Production agent workloads",
            "provisioning_state": "Succeeded",
            "is_default": True,
        },
    },
    {
        "id": EVALS_PROJECT_ID,
        "name": "evals",
        "location": "eastus",
        "properties": {
            "display_name": "Model Evals",
            "provisioning_state": "Succeeded",
            "is_default": False,
        },
    },
]

GPT4O_DEPLOYMENT_ID = f"{FOUNDRY_ACCOUNT_ID}/deployments/gpt-4o"
EMBEDDING_DEPLOYMENT_ID = f"{OPENAI_ACCOUNT_ID}/deployments/text-embedding-3-large"

MOCK_FOUNDRY_DEPLOYMENTS = [
    {
        "id": GPT4O_DEPLOYMENT_ID,
        "name": "gpt-4o",
        "sku": {"name": "GlobalStandard", "capacity": 50},
        "properties": {
            "provisioning_state": "Succeeded",
            "model": {
                "format": "OpenAI",
                "name": "gpt-4o",
                "version": "2024-08-06",
                "publisher": "OpenAI",
            },
            "rai_policy_name": "Microsoft.DefaultV2",
        },
    },
]

MOCK_OPENAI_DEPLOYMENTS = [
    {
        "id": EMBEDDING_DEPLOYMENT_ID,
        "name": "text-embedding-3-large",
        "sku": {"name": "Standard", "capacity": 120},
        "properties": {
            "provisioning_state": "Succeeded",
            "model": {
                "format": "OpenAI",
                "name": "text-embedding-3-large",
                "version": "1",
            },
            "rai_policy_name": "Microsoft.Default",
        },
    },
]
