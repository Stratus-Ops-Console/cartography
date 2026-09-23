from kubernetes.client import V1ObjectMeta
from kubernetes.client import V1ServiceAccount

from cartography.intel.kubernetes.rbac import transform_service_accounts


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
