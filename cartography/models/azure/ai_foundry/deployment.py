import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import AI_MODEL

logger = logging.getLogger(__name__)


# --- Node Definitions ---
@dataclass(frozen=True)
class AzureAIFoundryDeploymentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the model deployment."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the deployment (the name callers invoke)."
    )
    provisioning_state: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Current provisioning state of the deployment.",
    )
    model_name: PropertyRef = PropertyRef(
        "model_name",
        extra_index=True,
        description='Name of the deployed model (e.g. "gpt-4o").',
    )
    model_version: PropertyRef = PropertyRef(
        "model_version", description="Version of the deployed model."
    )
    model_format: PropertyRef = PropertyRef(
        "model_format",
        description='Format/provider of the model (e.g. "OpenAI", "DeepSeek").',
    )
    model_publisher: PropertyRef = PropertyRef(
        "model_publisher", description="Publisher of the deployed model."
    )
    sku_name: PropertyRef = PropertyRef(
        "sku_name",
        description='Deployment SKU (e.g. "Standard", "GlobalStandard", "ProvisionedManaged").',
    )
    sku_capacity: PropertyRef = PropertyRef(
        "sku_capacity",
        description="Provisioned capacity of the deployment (SKU-specific units).",
    )
    rai_policy_name: PropertyRef = PropertyRef(
        "rai_policy_name",
        description="Responsible AI (content filter) policy applied to the deployment.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureAIFoundryDeploymentToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryDeploymentToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the model deployment as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureAIFoundryDeploymentToSubscriptionRelProperties = (
        AzureAIFoundryDeploymentToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureAIFoundryDeploymentToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureAIFoundryDeploymentToAccountRel(CartographyRelSchema):
    """An AI Foundry account hosts the model deployment."""

    target_node_label: str = "AzureAIFoundryAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DEPLOYMENT"
    properties: AzureAIFoundryDeploymentToAccountRelProperties = (
        AzureAIFoundryDeploymentToAccountRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureAIFoundryDeploymentSchema(CartographyNodeSchema):
    """
    A model deployment in an Azure AI Foundry (or Azure OpenAI) account: a
    named, callable instance of a foundation model with its own SKU, capacity
    and Responsible AI content-filter policy.
    """

    label: str = "AzureAIFoundryDeployment"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([AI_MODEL])
    properties: AzureAIFoundryDeploymentProperties = (
        AzureAIFoundryDeploymentProperties()
    )
    sub_resource_relationship: AzureAIFoundryDeploymentToSubscriptionRel = (
        AzureAIFoundryDeploymentToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureAIFoundryDeploymentToAccountRel(),
        ],
    )
