import logging
from typing import Any

import neo4j
from azure.ai.projects import AIProjectClient
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.azure.util.common import extract_identity_principal_ids
from cartography.intel.azure.util.common import get_resource_group_from_id
from cartography.models.azure.ai_foundry.account import AzureAIFoundryAccountSchema
from cartography.models.azure.ai_foundry.agent import AzureAIFoundryAgentSchema
from cartography.models.azure.ai_foundry.connection import (
    AzureAIFoundryConnectionSchema,
)
from cartography.models.azure.ai_foundry.deployment import (
    AzureAIFoundryDeploymentSchema,
)
from cartography.models.azure.ai_foundry.project import AzureAIFoundryProjectSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)

# Cognitive Services account kinds that host Azure AI Foundry projects and/or
# model deployments: AIServices (the AI Foundry resource) and OpenAI
# (standalone Azure OpenAI). Other kinds (Face, SpeechServices, ...) are
# single-purpose cognitive services and are out of scope for this module.
AI_FOUNDRY_ACCOUNT_KINDS = frozenset({"AIServices", "OpenAI"})

# Key under ProjectProperties.endpoints holding the project's data-plane
# endpoint, used for the (optional) Foundry Agent Service listing.
AI_FOUNDRY_API_ENDPOINT_KEY = "AI Foundry API"


@timeit
def get_ai_foundry_accounts(
    client: CognitiveServicesManagementClient, subscription_id: str
) -> list[dict]:
    try:
        return [
            account.as_dict()
            for account in client.accounts.list()
            if account.kind in AI_FOUNDRY_ACCOUNT_KINDS
        ]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get AI Foundry accounts for subscription {subscription_id}: {str(e)}"
        )
        return []


@timeit
def get_ai_foundry_projects(
    client: CognitiveServicesManagementClient,
    resource_group_name: str,
    account_name: str,
) -> list[dict]:
    try:
        return [
            project.as_dict()
            for project in client.projects.list(resource_group_name, account_name)
        ]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get AI Foundry projects for account {account_name}: {str(e)}"
        )
        return []


@timeit
def get_ai_foundry_deployments(
    client: CognitiveServicesManagementClient,
    resource_group_name: str,
    account_name: str,
) -> list[dict]:
    try:
        return [
            deployment.as_dict()
            for deployment in client.deployments.list(resource_group_name, account_name)
        ]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get model deployments for account {account_name}: {str(e)}"
        )
        return []


@timeit
def get_ai_foundry_account_connections(
    client: CognitiveServicesManagementClient,
    resource_group_name: str,
    account_name: str,
) -> list[dict]:
    try:
        return [
            connection.as_dict()
            for connection in client.account_connections.list(
                resource_group_name, account_name
            )
        ]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get connections for account {account_name}: {str(e)}"
        )
        return []


@timeit
def get_ai_foundry_project_connections(
    client: CognitiveServicesManagementClient,
    resource_group_name: str,
    account_name: str,
    project_name: str,
) -> list[dict]:
    try:
        return [
            connection.as_dict()
            for connection in client.project_connections.list(
                resource_group_name, account_name, project_name
            )
        ]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get connections for project {project_name} "
            f"of account {account_name}: {str(e)}"
        )
        return []


@timeit
def get_ai_foundry_agents(
    credential: Any, project_endpoint: str, project_name: str
) -> list[dict]:
    """
    Data-plane call (Foundry Agent Service). Unlike the ARM calls above it
    needs a data-plane RBAC role (e.g. Azure AI User) on the project; without
    it we log and continue so the control-plane graph still syncs.
    """
    try:
        with AIProjectClient(
            endpoint=project_endpoint, credential=credential
        ) as project_client:
            return [agent.as_dict() for agent in project_client.agents.list()]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to list Foundry agents for project {project_name} "
            f"(missing data-plane RBAC on the project?): {str(e)}"
        )
        return []


@timeit
def transform_ai_foundry_accounts(accounts: list[dict]) -> list[dict]:
    transformed_accounts: list[dict[str, Any]] = []
    for account in accounts:
        properties = account.get("properties", {}) or {}
        sku = account.get("sku", {}) or {}
        transformed_accounts.append(
            {
                "id": account["id"],
                "name": account["name"],
                "kind": account.get("kind"),
                "location": account.get("location"),
                "endpoint": properties.get("endpoint"),
                "provisioning_state": properties.get("provisioning_state"),
                "public_network_access": properties.get("public_network_access"),
                "disable_local_auth": properties.get("disable_local_auth"),
                "custom_sub_domain_name": properties.get("custom_sub_domain_name"),
                "sku_name": sku.get("name"),
                "identity_principal_ids": extract_identity_principal_ids(
                    account.get("identity")
                ),
            }
        )
    return transformed_accounts


@timeit
def transform_ai_foundry_projects(projects: list[dict], account_id: str) -> list[dict]:
    transformed_projects: list[dict[str, Any]] = []
    for project in projects:
        properties = project.get("properties", {}) or {}
        transformed_projects.append(
            {
                "id": project["id"],
                "name": project["name"],
                "display_name": properties.get("display_name"),
                "description": properties.get("description"),
                "location": project.get("location"),
                "provisioning_state": properties.get("provisioning_state"),
                "is_default": properties.get("is_default"),
                "identity_principal_ids": extract_identity_principal_ids(
                    project.get("identity")
                ),
                "account_id": account_id,
            }
        )
    return transformed_projects


@timeit
def transform_ai_foundry_deployments(
    deployments: list[dict], account_id: str
) -> list[dict]:
    transformed_deployments: list[dict[str, Any]] = []
    for deployment in deployments:
        properties = deployment.get("properties", {}) or {}
        model = properties.get("model", {}) or {}
        sku = deployment.get("sku", {}) or {}
        transformed_deployments.append(
            {
                "id": deployment["id"],
                "name": deployment["name"],
                "provisioning_state": properties.get("provisioning_state"),
                "model_name": model.get("name"),
                "model_version": model.get("version"),
                "model_format": model.get("format"),
                "model_publisher": model.get("publisher"),
                "sku_name": sku.get("name"),
                "sku_capacity": sku.get("capacity"),
                "rai_policy_name": properties.get("rai_policy_name"),
                "account_id": account_id,
            }
        )
    return transformed_deployments


@timeit
def transform_ai_foundry_connections(
    connections: list[dict],
    account_id: str | None = None,
    project_id: str | None = None,
) -> list[dict]:
    transformed_connections: list[dict[str, Any]] = []
    for connection in connections:
        properties = connection.get("properties", {}) or {}
        metadata = properties.get("metadata") or {}
        transformed_connections.append(
            {
                "id": connection["id"],
                "name": connection["name"],
                "category": properties.get("category"),
                "auth_type": properties.get("auth_type"),
                "target": properties.get("target"),
                # Azure-resource-backed connections carry the target's ARM id
                # in metadata; portal and SDK writers vary the key's casing.
                "target_resource_id": metadata.get("ResourceId")
                or metadata.get("resourceId"),
                "is_shared_to_all": properties.get("is_shared_to_all"),
                "scope": "project" if project_id else "account",
                "account_id": account_id,
                "project_id": project_id,
            }
        )
    return transformed_connections


@timeit
def transform_ai_foundry_agents(
    agents: list[dict], project_id: str, account_id: str
) -> list[dict]:
    # azure-ai-projects models serialize to the camelCase wire format.
    transformed_agents: list[dict[str, Any]] = []
    for agent in agents:
        latest = (agent.get("versions") or {}).get("latest") or {}
        definition = latest.get("definition") or {}
        instance_identity = agent.get("instanceIdentity") or {}
        principal_id = instance_identity.get("principalId")
        model = definition.get("model")
        transformed_agents.append(
            {
                # Agents are data-plane objects with no ARM id; synthesize a
                # globally unique one under the project.
                "id": f"{project_id}/agents/{agent['name']}",
                "agent_guid": agent.get("id"),
                "name": agent["name"],
                "state": agent.get("state"),
                "description": latest.get("description"),
                "kind": definition.get("kind"),
                "model": model,
                "instructions": definition.get("instructions"),
                "tool_types": [
                    tool["type"]
                    for tool in definition.get("tools") or []
                    if isinstance(tool, dict) and tool.get("type")
                ],
                "version": latest.get("version"),
                "created_at": latest.get("createdAt"),
                "identity_principal_ids": [principal_id] if principal_id else [],
                "project_id": project_id,
                # Deployments are named per account, so the deployment the
                # agent calls has a deterministic ARM id (USES_MODEL target).
                "model_deployment_id": (
                    f"{account_id}/deployments/{model}" if model else None
                ),
            }
        )
    return transformed_agents


@timeit
def load_ai_foundry_accounts(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureAIFoundryAccountSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_ai_foundry_projects(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureAIFoundryProjectSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_ai_foundry_deployments(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureAIFoundryDeploymentSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_ai_foundry_connections(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureAIFoundryConnectionSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_ai_foundry_agents(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureAIFoundryAgentSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    # Children first so stale HAS_PROJECT / HAS_DEPLOYMENT / HAS_CONNECTION /
    # HAS_AGENT edges never dangle.
    GraphJob.from_node_schema(AzureAIFoundryAgentSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(
        AzureAIFoundryConnectionSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        AzureAIFoundryDeploymentSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(AzureAIFoundryProjectSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(AzureAIFoundryAccountSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Azure AI Foundry for subscription {subscription_id}.")
    client = CognitiveServicesManagementClient(credentials.credential, subscription_id)

    accounts = get_ai_foundry_accounts(client, subscription_id)
    load_ai_foundry_accounts(
        neo4j_session,
        transform_ai_foundry_accounts(accounts),
        subscription_id,
        update_tag,
    )

    all_projects: list[dict[str, Any]] = []
    all_deployments: list[dict[str, Any]] = []
    all_connections: list[dict[str, Any]] = []
    all_agents: list[dict[str, Any]] = []
    for account in accounts:
        account_id = account["id"]
        account_name = account["name"]
        resource_group_name = get_resource_group_from_id(account_id)
        # Projects only exist on AIServices accounts; standalone Azure OpenAI
        # accounts host deployments directly.
        if account.get("kind") == "AIServices":
            projects = get_ai_foundry_projects(
                client, resource_group_name, account_name
            )
            all_projects.extend(transform_ai_foundry_projects(projects, account_id))
            for project in projects:
                project_connections = get_ai_foundry_project_connections(
                    client, resource_group_name, account_name, project["name"]
                )
                # Project-scoped connections hang off the project only; the
                # account is reachable through HAS_PROJECT.
                all_connections.extend(
                    transform_ai_foundry_connections(
                        project_connections,
                        project_id=project["id"],
                    )
                )
                project_endpoint = (
                    (project.get("properties") or {}).get("endpoints") or {}
                ).get(AI_FOUNDRY_API_ENDPOINT_KEY)
                if project_endpoint:
                    agents = get_ai_foundry_agents(
                        credentials.credential, project_endpoint, project["name"]
                    )
                    all_agents.extend(
                        transform_ai_foundry_agents(agents, project["id"], account_id)
                    )
                else:
                    logger.debug(
                        "Project %s exposes no AI Foundry API endpoint; "
                        "skipping agent listing.",
                        project["name"],
                    )
        deployments = get_ai_foundry_deployments(
            client, resource_group_name, account_name
        )
        all_deployments.extend(
            transform_ai_foundry_deployments(deployments, account_id)
        )
        account_connections = get_ai_foundry_account_connections(
            client, resource_group_name, account_name
        )
        all_connections.extend(
            transform_ai_foundry_connections(account_connections, account_id=account_id)
        )

    load_ai_foundry_projects(neo4j_session, all_projects, subscription_id, update_tag)
    load_ai_foundry_deployments(
        neo4j_session, all_deployments, subscription_id, update_tag
    )
    load_ai_foundry_connections(
        neo4j_session, all_connections, subscription_id, update_tag
    )
    load_ai_foundry_agents(neo4j_session, all_agents, subscription_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
