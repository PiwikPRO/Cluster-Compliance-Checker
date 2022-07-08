from dependency_injector.wiring import Provide
from kubernetes import client
from kubernetes.client.api_client import ApiClient

from .. import manifests, schema
from ..core import AbstractCheck, Section
from ..dependencies import Dependencies
from ..requirements import HardwareRequirements
from ..spawner import Spawner
from ..util import exec_in_pod, get_bytes_from_data_size_with_suffix, wait_for_pods_ready


class Storage(Section):
    name = "Storage"
    description = "Checks related to access to external services"


@Storage.register
class RequestingPVC(AbstractCheck):
    name = "Requesting PVC"
    description = "Ensures that disk space may be requested on demand."

    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]
    registry_secret: client.V1Secret = Provide[Dependencies.registry_secret]
    spawner: Spawner = Provide[Dependencies.spawner]
    image: str = Provide[Dependencies.tools_image]

    def perform_check(self) -> schema.CheckResult:
        name = "request-pvc"
        secret_name = self.registry_secret.metadata.name  # type: ignore

        pvc_manifest = manifests.mk_pvc(name="mnt", size="1Gi")
        stateful_set_manifest = manifests.mk_stateful_set(
            name,
            self.image,
            pull_secrets=[client.V1LocalObjectReference(name=secret_name)],
            mounts={"/mnt": pvc_manifest},
        )

        with self.spawner.stateful_set(stateful_set_manifest) as stateful_set:
            api = client.CoreV1Api(self.kubernetes_client)
            apps_api = client.AppsV1Api(self.kubernetes_client)
            self.stateful_set = wait_for_pods_ready(apps_api, stateful_set)

            output = exec_in_pod(api=api, pod_name=f"{name}-0", cmd="mountpoint /mnt")
            result = "is a mountpoint" in output

            return schema.CheckResult(result, "Yes" if result else "No", "Yes")


@Storage.register
class QuotaForPVCCount(AbstractCheck):
    name = "Quota for PVC count"
    description = "Checks if we can request enough PVCs needed for the product."

    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]
    hardware_configurations: HardwareRequirements = Provide[Dependencies.requirements]

    def perform_check(self) -> schema.CheckResult:
        pvc_needed = len(self.hardware_configurations.pvc_requirements)

        api = client.CoreV1Api(self.kubernetes_client)
        resource_quotas = api.list_resource_quota_for_all_namespaces()

        pvc_quota = "No quota found"
        max_pvc_count = None
        for quota in resource_quotas.items:
            if "persistentvolumeclaims" in quota.spec.hard and (
                max_pvc_count is None
                or max_pvc_count > int(quota.spec.hard["persistentvolumeclaims"])
            ):
                max_pvc_count = int(quota.spec.hard["persistentvolumeclaims"])
                pvc_quota = quota.spec.hard["persistentvolumeclaims"]

        if max_pvc_count is None:
            return None

        return schema.CheckResult(
            max_pvc_count >= pvc_needed,
            pvc_quota,
            f">= {pvc_needed}",
        )


@Storage.register
class QuotaForPVCSize(AbstractCheck):
    name = "Quota for PVC size"
    description = "Checks if we can request large enough PVC to cover all product requirements."

    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]
    hardware_configurations: HardwareRequirements = Provide[Dependencies.requirements]

    def perform_check(self) -> schema.CheckResult:
        pvc_space_needed = sum([pvc.size for pvc in self.hardware_configurations.pvc_requirements])

        api = client.CoreV1Api(self.kubernetes_client)
        resource_quotas = api.list_resource_quota_for_all_namespaces()

        pvc_quota = "No quota found"
        max_pvc_size_in_bytes = None
        for quota in resource_quotas.items:
            if "requests.storage" in quota.spec.hard and (
                max_pvc_size_in_bytes is None
                or max_pvc_size_in_bytes
                > get_bytes_from_data_size_with_suffix(quota.spec.hard["requests.storage"])
            ):
                max_pvc_size_in_bytes = get_bytes_from_data_size_with_suffix(
                    quota.spec.hard["requests.storage"]
                )
                pvc_quota = quota.spec.hard["requests.storage"]

        if max_pvc_size_in_bytes is None:
            return None

        return schema.CheckResult(
            max_pvc_size_in_bytes >= pvc_space_needed * pow(1024, 3),
            pvc_quota,
            f">= {pvc_space_needed}Gi",
        )
