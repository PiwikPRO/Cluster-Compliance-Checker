from typing import Optional

from dependency_injector.wiring import Provide
from kubernetes import client
from kubernetes.client.api.core_v1_api import CoreV1Api
from kubernetes.client.api_client import ApiClient
from kubernetes.client.exceptions import ApiException
from packaging import version

from .. import schema
from ..core import AbstractCheck, Section
from ..dependencies import Dependencies


class Kubernetes(Section):
    name = "Kubernetes"
    description = "Checks related to kubernetes settings"


def get_nodes_list_by_label(
    kubernetes_client: ApiClient, labels: dict[str, str]
) -> list[client.V1Node]:
    """Fetch list of nodes that match given labels"""

    def match_labels(node: client.V1Node):
        return labels.items() <= node.metadata.labels.items()  # type: ignore

    api = client.CoreV1Api(kubernetes_client)
    nodes = api.list_node().items
    filtered_nodes = filter(match_labels, nodes)
    return list(filtered_nodes)


@Kubernetes.register
class KubernetesVersion(AbstractCheck):
    name = "Kubernetes version"
    description = "Ensures that kubernetes has supported version"
    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]

    def perform_check(self) -> schema.CheckResult:
        supported_min_ver_k8s = "v1.21.0"
        supported_max_ver_k8s = "v1.24.0"

        api = client.VersionApi(self.kubernetes_client)
        measured_ver_k8s = str(api.get_code().git_version)
        result = version.parse(supported_min_ver_k8s) <= version.parse(
            measured_ver_k8s
        ) and version.parse(supported_max_ver_k8s) >= version.parse(measured_ver_k8s)

        return schema.CheckResult(
            result=result,
            measured=measured_ver_k8s,
            expected=f">{supported_min_ver_k8s} and <{supported_max_ver_k8s}",
        )


@Kubernetes.register
class ClusterAdminPrivileges(AbstractCheck):
    name = "Cluster Admin privileges"
    description = "Ensures that we have Cluster Admin level privileges"
    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]

    def perform_check(self) -> schema.CheckResult:
        api = client.AuthorizationV1Api(self.kubernetes_client)
        privileges = api.create_self_subject_access_review(
            client.V1SelfSubjectAccessReview(
                spec=client.V1SelfSubjectAccessReviewSpec(
                    resource_attributes=client.V1ResourceAttributes(resource="*", verb="*")
                )
            )
        )

        result = privileges.status.allowed

        return schema.CheckResult(
            result=result,
            measured="Yes" if result else "No",
            expected="Yes",
        )


@Kubernetes.register
class CalicoVersion(AbstractCheck):
    name = "Calico version"
    description = "Ensures that a supported version of Calico is running"
    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]

    def perform_check(self) -> schema.CheckResult:
        min_supported_version = "v3.22"

        api = client.CustomObjectsApi(self.kubernetes_client)
        try:
            calico_info_list = api.list_cluster_custom_object(
                "crd.projectcalico.org", "v1", "clusterinformations"
            )
            calico_info = next(iter(calico_info_list["items"]))
            calico_version = calico_info["spec"]["calicoVersion"]
        except (ApiException, StopIteration, KeyError):
            return self.major_problem("Calico information not found")

        return schema.CheckResult(
            result=version.parse(calico_version) > version.parse(min_supported_version),
            measured=calico_version,
            expected=f"> {min_supported_version}",
        )


@Kubernetes.register
class Namespaces(AbstractCheck):
    name = "Namespaces"
    description = "Check if there are no unexpected namespaces"
    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]
    additional_namespace_whitelist: list[str] = Provide[Dependencies.namespace_whitelist]

    default_namespace_whitelist = [
        "default",
        "kube-system",
        "kube-public",
        "kube-node-lease",
        "calico-system",
        "tigera-operator",
        "calico-apiserver",
    ]

    @property
    def namespace_whitelist(self) -> set[str]:
        return set(self.default_namespace_whitelist) | set(self.additional_namespace_whitelist)

    def read_namespaces(self) -> set[str]:
        api = CoreV1Api(self.kubernetes_client)
        namespaces = api.list_namespace().items
        return set(namespace.metadata.name for namespace in namespaces)  # type: ignore

    def perform_check(self) -> Optional[schema.CheckResult]:
        actual_namespaces = self.read_namespaces()
        unexpected_namespaces = actual_namespaces - self.namespace_whitelist
        return schema.CheckResult(
            not bool(unexpected_namespaces),
            f"Unexpected: {unexpected_namespaces}" if unexpected_namespaces else "",
            f"Allowed: {self.namespace_whitelist}",
        )
