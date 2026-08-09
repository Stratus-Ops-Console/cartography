import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher

logger = logging.getLogger(__name__)


# --- Node Definitions ---
@dataclass(frozen=True)
class AzureContainerAppsEnvironmentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the Container Apps environment."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the Container Apps environment."
    )
    location: PropertyRef = PropertyRef(
        "location", description="Azure region where the environment is deployed."
    )
    provisioning_state: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Current provisioning state of the environment.",
    )
    default_domain: PropertyRef = PropertyRef(
        "default_domain",
        description="Default DNS domain assigned to apps in the environment.",
    )
    static_ip: PropertyRef = PropertyRef(
        "static_ip", description="Static IP of the environment's ingress."
    )
    public_network_access: PropertyRef = PropertyRef(
        "public_network_access",
        description="Whether the environment accepts traffic from public networks (Enabled/Disabled).",
    )
    internal_load_balancer: PropertyRef = PropertyRef(
        "internal_load_balancer",
        description=(
            "Whether the environment's ingress is bound to an internal (VNet-only) "
            "load balancer; external ingress on apps is not publicly reachable "
            "when true."
        ),
    )
    zone_redundant: PropertyRef = PropertyRef(
        "zone_redundant",
        description="Whether the environment is zone redundant.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureContainerAppsEnvironmentToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerAppsEnvironmentToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the Container Apps environment as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureContainerAppsEnvironmentToSubscriptionRelProperties = (
        AzureContainerAppsEnvironmentToSubscriptionRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureContainerAppsEnvironmentSchema(CartographyNodeSchema):
    """
    An Azure Container Apps managed environment (Microsoft.App/managedEnvironments):
    the secure network and observability boundary that hosts container apps.
    """

    label: str = "AzureContainerAppsEnvironment"
    properties: AzureContainerAppsEnvironmentProperties = (
        AzureContainerAppsEnvironmentProperties()
    )
    sub_resource_relationship: AzureContainerAppsEnvironmentToSubscriptionRel = (
        AzureContainerAppsEnvironmentToSubscriptionRel()
    )
