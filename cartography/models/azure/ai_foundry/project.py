import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher

logger = logging.getLogger(__name__)


# --- Node Definitions ---
@dataclass(frozen=True)
class AzureAIFoundryProjectProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the AI Foundry project."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the AI Foundry project."
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Human-readable display name of the project."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the project."
    )
    location: PropertyRef = PropertyRef(
        "location", description="Azure region where the project is deployed."
    )
    provisioning_state: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Current provisioning state of the project.",
    )
    is_default: PropertyRef = PropertyRef(
        "is_default",
        description="Whether this is the account's default project.",
    )
    identity_principal_ids: PropertyRef = PropertyRef(
        "identity_principal_ids",
        description=(
            "Object ids of the project's managed identities (system- and "
            "user-assigned). Foundry agents in the project act as these "
            "identities; they anchor the RUNS_AS and ASSUMES edges."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureAIFoundryProjectToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryProjectToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the AI Foundry project as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureAIFoundryProjectToSubscriptionRelProperties = (
        AzureAIFoundryProjectToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryProjectToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryProjectToAccountRel(CartographyRelSchema):
    """An AI Foundry account contains the project."""

    target_node_label: str = "AzureAIFoundryAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_PROJECT"
    properties: AzureAIFoundryProjectToAccountRelProperties = (
        AzureAIFoundryProjectToAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryProjectToServicePrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryProjectToServicePrincipalRel(CartographyRelSchema):
    """The AI Foundry project runs as its managed identity's service principal."""

    target_node_label: str = "EntraServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("identity_principal_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_AS"
    properties: AzureAIFoundryProjectToServicePrincipalRelProperties = (
        AzureAIFoundryProjectToServicePrincipalRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryProjectToRoleAssumesRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:AzureAIFoundryProject)-[:ASSUMES]->(:AzureRoleDefinition).
# Foundry agents and tools in the project act with the permissions of the role
# definitions assigned to the project's managed identity. Assembled by joining
# the identity principalId to AzureRoleAssignment -> AzureRoleDefinition after
# the RBAC sync, so it is loaded as a MatchLink rather than a direct edge.
class AzureAIFoundryProjectToRoleAssumesMatchLink(CartographyRelSchema):
    """An AI Foundry project assumes a role assigned to its managed identity."""

    rel_label: str = "ASSUMES"
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: AzureAIFoundryProjectToRoleAssumesRelProperties = (
        AzureAIFoundryProjectToRoleAssumesRelProperties()
    )
    target_node_label: str = "AzureRoleDefinition"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_definition_id")},
    )
    source_node_label: str = "AzureAIFoundryProject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("workload_id")},
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureAIFoundryProjectSchema(CartographyNodeSchema):
    """
    An Azure AI Foundry project (Microsoft.CognitiveServices/accounts/projects):
    the collaboration and isolation boundary inside a Foundry account where
    agents, evaluations and data connections live.
    """

    label: str = "AzureAIFoundryProject"
    properties: AzureAIFoundryProjectProperties = AzureAIFoundryProjectProperties()
    sub_resource_relationship: AzureAIFoundryProjectToSubscriptionRel = (
        AzureAIFoundryProjectToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureAIFoundryProjectToAccountRel(),
            AzureAIFoundryProjectToServicePrincipalRel(),
        ],
    )
