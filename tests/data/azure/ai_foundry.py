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
            "endpoints": {
                "AI Foundry API": (
                    "https://foundry-prod.services.ai.azure.com/api/projects/agents"
                ),
            },
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


SEARCH_CONNECTION_ID = f"{FOUNDRY_ACCOUNT_ID}/connections/search-shared"
KV_CONNECTION_ID = f"{AGENTS_PROJECT_ID}/connections/kv-agents"
CUSTOM_CONNECTION_ID = f"{AGENTS_PROJECT_ID}/connections/crm-api"

KEY_VAULT_RESOURCE_ID = (
    "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/"
    "Microsoft.KeyVault/vaults/agents-kv"
)

MOCK_ACCOUNT_CONNECTIONS = [
    {
        "id": SEARCH_CONNECTION_ID,
        "name": "search-shared",
        "properties": {
            "auth_type": "AAD",
            "category": "CognitiveSearch",
            "target": "https://estate-search.search.windows.net/",
            "is_shared_to_all": True,
            "metadata": {
                "ResourceId": (
                    "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/"
                    "Microsoft.Search/searchServices/estate-search"
                ),
            },
        },
    },
]

MOCK_PROJECT_CONNECTIONS = [
    {
        "id": KV_CONNECTION_ID,
        "name": "kv-agents",
        "properties": {
            "auth_type": "ManagedIdentity",
            "category": "AzureKeyVault",
            "target": "https://agents-kv.vault.azure.net/",
            # Lowercase metadata key spelling seen from some SDK writers.
            "metadata": {"resourceId": KEY_VAULT_RESOURCE_ID},
        },
    },
    {
        # Static-secret connection to an arbitrary external API: the shape a
        # key-auth governance query needs to surface.
        "id": CUSTOM_CONNECTION_ID,
        "name": "crm-api",
        "properties": {
            "auth_type": "ApiKey",
            "category": "CustomKeys",
            "target": "https://crm.example.com/api",
        },
    },
]


SUPPORT_AGENT_ID = f"{AGENTS_PROJECT_ID}/agents/support-agent"
TRIAGE_AGENT_ID = f"{AGENTS_PROJECT_ID}/agents/triage-agent"

# Data-plane payloads (azure-ai-projects, camelCase wire format).
MOCK_AGENTS = [
    {
        "object": "agent",
        "id": "agt_11111111",
        "name": "support-agent",
        "state": "enabled",
        "instanceIdentity": {"principalId": "sp-203", "status": "Enabled"},
        "versions": {
            "latest": {
                "id": "agtver_11111111",
                "name": "support-agent",
                "version": "3",
                "createdAt": "2026-08-01T10:00:00Z",
                "description": "Answers customer support tickets",
                "definition": {
                    "kind": "prompt",
                    "model": "gpt-4o",
                    "instructions": "Help customers with their tickets.",
                    "tools": [
                        {"type": "file_search"},
                        {"type": "mcp", "server_label": "crm"},
                    ],
                },
            },
        },
    },
    {
        # Minimal agent: no instance identity (acts as the project identity),
        # no tools.
        "object": "agent",
        "id": "agt_22222222",
        "name": "triage-agent",
        "state": "disabled",
        "versions": {
            "latest": {
                "id": "agtver_22222222",
                "name": "triage-agent",
                "version": "1",
                "createdAt": "2026-07-15T08:30:00Z",
                "definition": {
                    "kind": "prompt",
                    "model": "gpt-4o",
                    "instructions": "Label incoming tickets.",
                },
            },
        },
    },
]
