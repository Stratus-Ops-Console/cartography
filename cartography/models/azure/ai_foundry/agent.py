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
class AzureAIFoundryAgentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Synthetic unique id of the agent: the project's ARM id plus "
            "/agents/<name>. Agents are a data-plane object without an ARM id "
            "of their own."
        ),
    )
    agent_guid: PropertyRef = PropertyRef(
        "agent_guid",
        description="Service-assigned id of the agent object.",
    )
    name: PropertyRef = PropertyRef("name", description="Name of the agent.")
    state: PropertyRef = PropertyRef(
        "state", description="Whether the agent is enabled or disabled."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the agent's latest version."
    )
    kind: PropertyRef = PropertyRef(
        "kind",
        description='Definition kind of the agent (e.g. "prompt", "hosted").',
    )
    model: PropertyRef = PropertyRef(
        "model",
        extra_index=True,
        description="Model deployment name the agent's latest version calls.",
    )
    instructions: PropertyRef = PropertyRef(
        "instructions",
        description="System instructions of the agent's latest version.",
    )
    tool_types: PropertyRef = PropertyRef(
        "tool_types",
        description=(
            "Kinds of tools the agent's latest version can invoke "
            '(e.g. "code_interpreter", "file_search", "function", "mcp").'
        ),
    )
    version: PropertyRef = PropertyRef(
        "version", description="Version label of the agent's latest version."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Creation time of the agent's latest version.",
    )
    identity_principal_ids: PropertyRef = PropertyRef(
        "identity_principal_ids",
        description=(
            "Object id of the agent's instance identity, when the agent runs "
            "as its own managed identity. Anchors the RUNS_AS and ASSUMES "
            "edges; agents without one act as the project's identity."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureAIFoundryAgentToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryAgentToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the agent as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureAIFoundryAgentToSubscriptionRelProperties = (
        AzureAIFoundryAgentToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryAgentToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryAgentToProjectRel(CartographyRelSchema):
    """An AI Foundry project hosts the agent."""

    target_node_label: str = "AzureAIFoundryProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_AGENT"
    properties: AzureAIFoundryAgentToProjectRelProperties = (
        AzureAIFoundryAgentToProjectRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryAgentToDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryAgentToDeploymentRel(CartographyRelSchema):
    """The agent calls a model deployment hosted by the account."""

    target_node_label: str = "AzureAIFoundryDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("model_deployment_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_MODEL"
    properties: AzureAIFoundryAgentToDeploymentRelProperties = (
        AzureAIFoundryAgentToDeploymentRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryAgentToServicePrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryAgentToServicePrincipalRel(CartographyRelSchema):
    """The agent runs as its instance identity's service principal."""

    target_node_label: str = "EntraServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("identity_principal_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_AS"
    properties: AzureAIFoundryAgentToServicePrincipalRelProperties = (
        AzureAIFoundryAgentToServicePrincipalRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryAgentToRoleAssumesRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:AzureAIFoundryAgent)-[:ASSUMES]->(:AzureRoleDefinition).
# The agent acts with the permissions of the role definitions assigned to its
# instance identity. Assembled by joining the identity principalId to
# AzureRoleAssignment -> AzureRoleDefinition after the RBAC sync, so it is
# loaded as a MatchLink rather than a direct edge on the node.
class AzureAIFoundryAgentToRoleAssumesMatchLink(CartographyRelSchema):
    """An AI Foundry agent assumes a role assigned to its instance identity."""

    rel_label: str = "ASSUMES"
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: AzureAIFoundryAgentToRoleAssumesRelProperties = (
        AzureAIFoundryAgentToRoleAssumesRelProperties()
    )
    target_node_label: str = "AzureRoleDefinition"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_definition_id")},
    )
    source_node_label: str = "AzureAIFoundryAgent"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("workload_id")},
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureAIFoundryAgentSchema(CartographyNodeSchema):
    """
    An agent defined in an Azure AI Foundry project (data plane, Foundry Agent
    Service). Reflects the agent's latest version: the model deployment it
    calls, the kinds of tools it can invoke, and the identity it acts as.
    """

    label: str = "AzureAIFoundryAgent"
    properties: AzureAIFoundryAgentProperties = AzureAIFoundryAgentProperties()
    sub_resource_relationship: AzureAIFoundryAgentToSubscriptionRel = (
        AzureAIFoundryAgentToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureAIFoundryAgentToProjectRel(),
            AzureAIFoundryAgentToDeploymentRel(),
            AzureAIFoundryAgentToServicePrincipalRel(),
        ],
    )
