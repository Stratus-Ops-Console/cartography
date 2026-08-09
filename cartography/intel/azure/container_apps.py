import logging
from typing import Any

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.appcontainers import ContainerAppsAPIClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.azure.util.common import extract_identity_principal_ids
from cartography.models.azure.container_apps.app import AzureContainerAppSchema
from cartography.models.azure.container_apps.environment import (
    AzureContainerAppsEnvironmentSchema,
)
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_container_apps_environments(
    client: ContainerAppsAPIClient, subscription_id: str
) -> list[dict]:
    try:
        return [
            environment.as_dict()
            for environment in client.managed_environments.list_by_subscription()
        ]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get Container Apps environments for subscription {subscription_id}: {str(e)}"
        )
        return []


@timeit
def get_container_apps(
    client: ContainerAppsAPIClient, subscription_id: str
) -> list[dict]:
    try:
        return [app.as_dict() for app in client.container_apps.list_by_subscription()]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get container apps for subscription {subscription_id}: {str(e)}"
        )
        return []


@timeit
def transform_container_apps_environments(environments: list[dict]) -> list[dict]:
    # azure-mgmt-appcontainers models serialize to the camelCase ARM wire format.
    transformed_environments: list[dict[str, Any]] = []
    for environment in environments:
        properties = environment.get("properties", {}) or {}
        vnet_configuration = properties.get("vnetConfiguration") or {}
        transformed_environments.append(
            {
                "id": environment["id"],
                "name": environment["name"],
                "location": environment.get("location"),
                "provisioning_state": properties.get("provisioningState"),
                "default_domain": properties.get("defaultDomain"),
                "static_ip": properties.get("staticIp"),
                "public_network_access": properties.get("publicNetworkAccess"),
                "internal_load_balancer": vnet_configuration.get("internal"),
                "zone_redundant": properties.get("zoneRedundant"),
            }
        )
    return transformed_environments


@timeit
def transform_container_apps(apps: list[dict]) -> list[dict]:
    transformed_apps: list[dict[str, Any]] = []
    for app in apps:
        properties = app.get("properties", {}) or {}
        configuration = properties.get("configuration") or {}
        ingress = configuration.get("ingress") or {}
        transformed_apps.append(
            {
                "id": app["id"],
                "name": app["name"],
                "location": app.get("location"),
                "provisioning_state": properties.get("provisioningState"),
                # environmentId superseded managedEnvironmentId; older apps may
                # only carry the legacy field.
                "environment_id": properties.get("environmentId")
                or properties.get("managedEnvironmentId"),
                "fqdn": ingress.get("fqdn"),
                "ingress_external": ingress.get("external"),
                "target_port": ingress.get("targetPort"),
                "allow_insecure": ingress.get("allowInsecure"),
                "workload_profile_name": properties.get("workloadProfileName"),
                "latest_revision_name": properties.get("latestRevisionName"),
                "identity_principal_ids": extract_identity_principal_ids(
                    app.get("identity")
                ),
            }
        )
    return transformed_apps


@timeit
def load_container_apps_environments(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureContainerAppsEnvironmentSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_container_apps(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureContainerAppSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    # Apps first so stale HAS_APP edges never dangle.
    GraphJob.from_node_schema(AzureContainerAppSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(
        AzureContainerAppsEnvironmentSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Azure Container Apps for subscription {subscription_id}.")
    client = ContainerAppsAPIClient(credentials.credential, subscription_id)

    environments = get_container_apps_environments(client, subscription_id)
    load_container_apps_environments(
        neo4j_session,
        transform_container_apps_environments(environments),
        subscription_id,
        update_tag,
    )

    apps = get_container_apps(client, subscription_id)
    load_container_apps(
        neo4j_session,
        transform_container_apps(apps),
        subscription_id,
        update_tag,
    )

    cleanup(neo4j_session, common_job_parameters)
