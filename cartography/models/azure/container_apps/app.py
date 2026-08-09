import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import COMPUTE_SERVICE

logger = logging.getLogger(__name__)


# --- Node Definitions ---
@dataclass(frozen=True)
class AzureContainerAppProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the container app."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the container app.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region where the app is deployed."
    )
    provisioning_state: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Current provisioning state of the app.",
    )
    environment_id: PropertyRef = PropertyRef(
        "environment_id",
        description="Resource ID of the managed environment hosting the app.",
    )
    fqdn: PropertyRef = PropertyRef(
        "fqdn", description="Fully qualified domain name of the app's ingress."
    )
    ingress_external: PropertyRef = PropertyRef(
        "ingress_external",
        description=(
            "Whether the app's ingress accepts traffic from outside the "
            "environment. Publicly reachable when the environment is not on an "
            "internal load balancer; null when the app has no ingress."
        ),
    )
    target_port: PropertyRef = PropertyRef(
        "target_port", description="Container port the ingress routes traffic to."
    )
    allow_insecure: PropertyRef = PropertyRef(
        "allow_insecure",
        description="Whether plain-HTTP (non-TLS) ingress traffic is allowed.",
    )
    workload_profile_name: PropertyRef = PropertyRef(
        "workload_profile_name",
        description="Workload profile the app runs on (Consumption when null).",
    )
    latest_revision_name: PropertyRef = PropertyRef(
        "latest_revision_name", description="Name of the app's latest revision."
    )
    identity_principal_ids: PropertyRef = PropertyRef(
        "identity_principal_ids",
        description=(
            "Object ids of the app's managed identities (system- and "
            "user-assigned). These anchor the RUNS_AS and ASSUMES edges."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureContainerAppToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerAppToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the container app as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureContainerAppToSubscriptionRelProperties = (
        AzureContainerAppToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureContainerAppToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerAppToEnvironmentRel(CartographyRelSchema):
    """A Container Apps environment hosts the container app."""

    target_node_label: str = "AzureContainerAppsEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("environment_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_APP"
    properties: AzureContainerAppToEnvironmentRelProperties = (
        AzureContainerAppToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class AzureContainerAppToServicePrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerAppToServicePrincipalRel(CartographyRelSchema):
    """The container app runs as its managed identity's service principal."""

    target_node_label: str = "EntraServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("identity_principal_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_AS"
    properties: AzureContainerAppToServicePrincipalRelProperties = (
        AzureContainerAppToServicePrincipalRelProperties()
    )


@dataclass(frozen=True)
class AzureContainerAppToRoleAssumesRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:AzureContainerApp)-[:ASSUMES]->(:AzureRoleDefinition).
# The container app runs with the permissions of the role definitions assigned
# to its managed identity. Assembled by joining the identity principalId to
# AzureRoleAssignment -> AzureRoleDefinition after the RBAC sync, so it is
# loaded as a MatchLink rather than a direct edge on the node.
class AzureContainerAppToRoleAssumesMatchLink(CartographyRelSchema):
    """A container app assumes a role assigned to its managed identity."""

    rel_label: str = "ASSUMES"
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: AzureContainerAppToRoleAssumesRelProperties = (
        AzureContainerAppToRoleAssumesRelProperties()
    )
    target_node_label: str = "AzureRoleDefinition"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_definition_id")},
    )
    source_node_label: str = "AzureContainerApp"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("workload_id")},
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureContainerAppSchema(CartographyNodeSchema):
    """
    An Azure Container App (Microsoft.App/containerApps): a serverless
    containerized application running in a Container Apps managed environment.
    """

    label: str = "AzureContainerApp"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_SERVICE])
    properties: AzureContainerAppProperties = AzureContainerAppProperties()
    sub_resource_relationship: AzureContainerAppToSubscriptionRel = (
        AzureContainerAppToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureContainerAppToEnvironmentRel(),
            AzureContainerAppToServicePrincipalRel(),
        ],
    )
