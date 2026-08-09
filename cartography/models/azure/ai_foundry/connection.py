import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher

logger = logging.getLogger(__name__)


# --- Node Definitions ---
@dataclass(frozen=True)
class AzureAIFoundryConnectionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the connection."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the connection.")
    category: PropertyRef = PropertyRef(
        "category",
        description=(
            'Kind of resource the connection points at (e.g. "CognitiveSearch", '
            '"AzureStorageAccount", "AzureOpenAI", "ApiKey", "CustomKeys").'
        ),
    )
    auth_type: PropertyRef = PropertyRef(
        "auth_type",
        description=(
            'How the connection authenticates to its target (e.g. "AAD", '
            '"ManagedIdentity", "ApiKey", "AccountKey", "SAS"). Static-secret '
            "types mean a credential is stored with the connection."
        ),
    )
    target: PropertyRef = PropertyRef(
        "target", description="Endpoint URL or resource the connection points at."
    )
    target_resource_id: PropertyRef = PropertyRef(
        "target_resource_id",
        extra_index=True,
        description=(
            "ARM resource ID of the target when the connection points at an "
            "Azure resource (from the connection's ResourceId metadata)."
        ),
    )
    is_shared_to_all: PropertyRef = PropertyRef(
        "is_shared_to_all",
        description="Whether the connection is shared with all projects in the account.",
    )
    scope: PropertyRef = PropertyRef(
        "scope",
        description='Where the connection is defined: "account" or "project".',
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureAIFoundryConnectionToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryConnectionToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the connection as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureAIFoundryConnectionToSubscriptionRelProperties = (
        AzureAIFoundryConnectionToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryConnectionToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryConnectionToAccountRel(CartographyRelSchema):
    """An AI Foundry account defines the (account-scoped) connection."""

    target_node_label: str = "AzureAIFoundryAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CONNECTION"
    properties: AzureAIFoundryConnectionToAccountRelProperties = (
        AzureAIFoundryConnectionToAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryConnectionToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryConnectionToProjectRel(CartographyRelSchema):
    """An AI Foundry project defines the (project-scoped) connection."""

    target_node_label: str = "AzureAIFoundryProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CONNECTION"
    properties: AzureAIFoundryConnectionToProjectRelProperties = (
        AzureAIFoundryConnectionToProjectRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryConnectionToKeyVaultRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryConnectionToKeyVaultRel(CartographyRelSchema):
    """The connection points at an Azure Key Vault ingested by the key vault sync."""

    target_node_label: str = "AzureKeyVault"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_resource_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_TO"
    properties: AzureAIFoundryConnectionToKeyVaultRelProperties = (
        AzureAIFoundryConnectionToKeyVaultRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryConnectionToStorageAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryConnectionToStorageAccountRel(CartographyRelSchema):
    """The connection points at an Azure Storage account ingested by the storage sync."""

    target_node_label: str = "AzureStorageAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_resource_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_TO"
    properties: AzureAIFoundryConnectionToStorageAccountRelProperties = (
        AzureAIFoundryConnectionToStorageAccountRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureAIFoundryConnectionSchema(CartographyNodeSchema):
    """
    A connection defined on an Azure AI Foundry account or project: a named,
    reusable pointer to an external resource (search index, storage account,
    key vault, another AI endpoint, arbitrary API) together with the credential
    used to reach it. Connections are what give agents and tools in a project
    their reach, so the auth_type and target of each connection are the core
    of an AI data-access review.
    """

    label: str = "AzureAIFoundryConnection"
    properties: AzureAIFoundryConnectionProperties = (
        AzureAIFoundryConnectionProperties()
    )
    sub_resource_relationship: AzureAIFoundryConnectionToSubscriptionRel = (
        AzureAIFoundryConnectionToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureAIFoundryConnectionToAccountRel(),
            AzureAIFoundryConnectionToProjectRel(),
            AzureAIFoundryConnectionToKeyVaultRel(),
            AzureAIFoundryConnectionToStorageAccountRel(),
        ],
    )
