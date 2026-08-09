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
class AzureAIFoundryAccountProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the AI Foundry account."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the AI Foundry account."
    )
    kind: PropertyRef = PropertyRef(
        "kind",
        description=(
            "Cognitive Services account kind: AIServices (Azure AI Foundry) "
            "or OpenAI (Azure OpenAI)."
        ),
    )
    location: PropertyRef = PropertyRef(
        "location", description="Azure region where the account is deployed."
    )
    endpoint: PropertyRef = PropertyRef(
        "endpoint", description="Primary API endpoint of the account."
    )
    provisioning_state: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Current provisioning state of the account.",
    )
    public_network_access: PropertyRef = PropertyRef(
        "public_network_access",
        description="Whether the account accepts traffic from public networks (Enabled/Disabled).",
    )
    disable_local_auth: PropertyRef = PropertyRef(
        "disable_local_auth",
        description=(
            "Whether API-key (local) authentication is disabled. False or null "
            "means the account accepts static API keys in addition to Entra ID."
        ),
    )
    custom_sub_domain_name: PropertyRef = PropertyRef(
        "custom_sub_domain_name",
        description="Custom subdomain used for token-based (Entra ID) authentication.",
    )
    sku_name: PropertyRef = PropertyRef(
        "sku_name", description="SKU of the account (e.g. S0)."
    )
    identity_principal_ids: PropertyRef = PropertyRef(
        "identity_principal_ids",
        description=(
            "Object ids of the account's managed identities (system- and "
            "user-assigned). These anchor the RUNS_AS and ASSUMES edges."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureAIFoundryAccountToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryAccountToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the AI Foundry account as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureAIFoundryAccountToSubscriptionRelProperties = (
        AzureAIFoundryAccountToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryAccountToServicePrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryAccountToServicePrincipalRel(CartographyRelSchema):
    """The AI Foundry account runs as its managed identity's service principal."""

    target_node_label: str = "EntraServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("identity_principal_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_AS"
    properties: AzureAIFoundryAccountToServicePrincipalRelProperties = (
        AzureAIFoundryAccountToServicePrincipalRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryAccountToRoleAssumesRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:AzureAIFoundryAccount)-[:ASSUMES]->(:AzureRoleDefinition).
# The account's workloads run with the permissions of the role definitions
# assigned to its managed identity. Assembled by joining the identity
# principalId to AzureRoleAssignment -> AzureRoleDefinition after the RBAC
# sync, so it is loaded as a MatchLink rather than a direct edge on the node.
class AzureAIFoundryAccountToRoleAssumesMatchLink(CartographyRelSchema):
    """An AI Foundry account assumes a role assigned to its managed identity."""

    rel_label: str = "ASSUMES"
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: AzureAIFoundryAccountToRoleAssumesRelProperties = (
        AzureAIFoundryAccountToRoleAssumesRelProperties()
    )
    target_node_label: str = "AzureRoleDefinition"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_definition_id")},
    )
    source_node_label: str = "AzureAIFoundryAccount"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("workload_id")},
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureAIFoundryAccountSchema(CartographyNodeSchema):
    """
    An Azure AI Foundry account (Microsoft.CognitiveServices/accounts of kind
    AIServices, or a standalone Azure OpenAI account of kind OpenAI). The
    account is the management container for Foundry projects and model
    deployments.
    """

    label: str = "AzureAIFoundryAccount"
    properties: AzureAIFoundryAccountProperties = AzureAIFoundryAccountProperties()
    sub_resource_relationship: AzureAIFoundryAccountToSubscriptionRel = (
        AzureAIFoundryAccountToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureAIFoundryAccountToServicePrincipalRel(),
        ],
    )
