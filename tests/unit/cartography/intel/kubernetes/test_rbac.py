import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from kubernetes.client import V1ObjectMeta
from kubernetes.client import V1PolicyRule
from kubernetes.client import V1Role
from kubernetes.client import V1ServiceAccount
from kubernetes.client.exceptions import ApiException

from cartography.intel.kubernetes.rbac import sync_kubernetes_rbac
from cartography.intel.kubernetes.rbac import transform_roles
from cartography.intel.kubernetes.rbac import transform_service_accounts

_LIST_FUNCTIONS = {
    "core": ["list_service_account_for_all_namespaces"],
    "rbac": [
        "list_role_for_all_namespaces",
        "list_role_binding_for_all_namespaces",
        "list_cluster_role",
        "list_cluster_role_binding",
    ],
}


def _client_failing_on(failing: str, error: ApiException) -> MagicMock:
    client = MagicMock()
    client.name = "my-cluster"
    for api_name, functions in _LIST_FUNCTIONS.items():
        for function_name in functions:
            list_func = getattr(getattr(client, api_name), function_name)
            list_func.__name__ = function_name
            if function_name == failing:
                list_func.side_effect = error
            else:
                list_func.return_value = MagicMock(
                    items=[], metadata=MagicMock(_continue=None)
                )
    return client


@patch("cartography.intel.kubernetes.rbac.cleanup")
@patch("cartography.intel.kubernetes.rbac.load_service_accounts")
def test_sync_rbac_skips_load_and_cleanup_on_forbidden(
    mock_load_service_accounts, mock_cleanup, caplog
):
    # Arrange
    mock_client = _client_failing_on(
        "list_cluster_role_binding", ApiException(status=403, reason="Forbidden")
    )

    # Act
    with caplog.at_level("WARNING"):
        sync_kubernetes_rbac(
            session=MagicMock(),
            client=mock_client,
            update_tag=1,
            common_job_parameters={"CLUSTER_ID": "cluster-id"},
        )

    # Assert
    mock_load_service_accounts.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any(
        "lacks permission to list RBAC resources" in record.message
        for record in caplog.records
    )


@patch("cartography.intel.kubernetes.rbac.cleanup")
def test_sync_rbac_raises_on_other_api_errors(mock_cleanup):
    # Arrange
    mock_client = _client_failing_on(
        "list_role_for_all_namespaces",
        ApiException(status=500, reason="Internal Server Error"),
    )

    # Act and assert
    with pytest.raises(ApiException):
        sync_kubernetes_rbac(
            session=MagicMock(),
            client=mock_client,
            update_tag=1,
            common_job_parameters={"CLUSTER_ID": "cluster-id"},
        )
    mock_cleanup.assert_not_called()


def test_transform_roles_keeps_rules_with_api_field_names():
    # Arrange
    role = V1Role(
        metadata=V1ObjectMeta(name="reader", namespace="ns", uid="role-uid"),
        rules=[
            V1PolicyRule(
                api_groups=[""],
                resources=["secrets"],
                resource_names=["db"],
                verbs=["get"],
            ),
            V1PolicyRule(non_resource_urls=["/healthz"], verbs=["get"]),
        ],
    )

    # Act
    transformed = transform_roles([role], "cluster")

    # Assert
    assert json.loads(transformed[0]["rules"]) == [
        {
            "apiGroups": [""],
            "resourceNames": ["db"],
            "resources": ["secrets"],
            "verbs": ["get"],
        },
        {"nonResourceURLs": ["/healthz"], "verbs": ["get"]},
    ]



def _sa(name: str, annotations: dict[str, str] | None) -> V1ServiceAccount:
    return V1ServiceAccount(
        metadata=V1ObjectMeta(
            name=name,
            namespace="apps",
            uid=f"uid-{name}",
            resource_version="1",
            annotations=annotations,
        ),
    )


def _by_name(service_accounts: list[V1ServiceAccount]) -> dict[str, dict]:
    return {
        sa["name"]: sa
        for sa in transform_service_accounts(service_accounts, "my-cluster")
    }


def test_transform_service_accounts_extracts_cloud_workload_identity_annotations():
    result = _by_name(
        [
            _sa(
                "irsa",
                {"eks.amazonaws.com/role-arn": "arn:aws:iam::123456789012:role/r"},
            ),
            _sa(
                "gke",
                {"iam.gke.io/gcp-service-account": "sa@proj.iam.gserviceaccount.com"},
            ),
            _sa(
                "aks",
                {
                    "azure.workload.identity/client-id": (
                        "5d1c8a1e-1111-4b2c-9d3e-aaaaaaaaaaaa"
                    ),
                    "azure.workload.identity/tenant-id": (
                        "72f988bf-86f1-41af-91ab-2d7cd011db47"
                    ),
                },
            ),
            _sa("plain", None),
        ]
    )

    assert result["irsa"]["aws_role_arn"] == "arn:aws:iam::123456789012:role/r"
    assert result["gke"]["gcp_service_account"] == "sa@proj.iam.gserviceaccount.com"
    assert result["aks"]["azure_client_id"] == "5d1c8a1e-1111-4b2c-9d3e-aaaaaaaaaaaa"
    assert result["aks"]["azure_tenant_id"] == "72f988bf-86f1-41af-91ab-2d7cd011db47"
    assert result["aks"]["id"] == "my-cluster/apps/aks"

    # Annotations of one provider never leak into another provider's fields.
    for name in ("irsa", "gke", "plain"):
        assert result[name]["azure_client_id"] is None
        assert result[name]["azure_tenant_id"] is None
    assert result["aks"]["aws_role_arn"] is None
    assert result["aks"]["gcp_service_account"] is None


def test_transform_service_accounts_normalizes_aks_workload_identity_guids():
    result = _by_name(
        [
            # Client id only: the tenant falls back to the webhook default.
            _sa(
                "upper",
                {
                    "azure.workload.identity/client-id": (
                        " 5D1C8A1E-1111-4B2C-9D3E-AAAAAAAAAAAA "
                    ),
                },
            ),
            _sa(
                "blank",
                {
                    "azure.workload.identity/client-id": "  ",
                    "azure.workload.identity/tenant-id": "",
                },
            ),
        ]
    )

    assert result["upper"]["azure_client_id"] == "5d1c8a1e-1111-4b2c-9d3e-aaaaaaaaaaaa"
    assert result["upper"]["azure_tenant_id"] is None
    assert result["blank"]["azure_client_id"] is None
    assert result["blank"]["azure_tenant_id"] is None
