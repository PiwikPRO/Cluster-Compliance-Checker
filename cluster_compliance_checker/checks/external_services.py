from typing import Optional

from dependency_injector.wiring import Provide
from kubernetes import client
from kubernetes.client.api_client import ApiClient

from .. import schema
from ..core import AbstractCheck, Section
from ..dependencies import Dependencies
from ..enums import MaintenanceType, Phase
from ..manifests import mk_stateful_set
from ..spawner import Spawner
from ..util import exec_in_pod, wait_for_pods_ready


class ExternalServices(Section):
    name = "External services"
    description = "Checks related to access to external services"


@ExternalServices.register
class PagerDutyAccess(AbstractCheck):
    name = "PagerDuty access"
    description = "Check if cluster has access to PagerDuty"

    offline: bool = Provide[Dependencies.offline]
    maintenance_type: MaintenanceType = Provide[Dependencies.maintenance_type]
    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]
    stateful_set: client.V1StatefulSet = Provide[Dependencies.single_pod]

    def perform_check(self) -> Optional[schema.CheckResult]:
        if self.offline or self.maintenance_type is MaintenanceType.SELF_SUPPORT:
            return

        api = client.CoreV1Api(self.kubernetes_client)
        url = "https://status.pagerduty.com/api/v2/status.json"
        http_status_code = exec_in_pod(
            cmd=f'curl -s -o /dev/null -w "%{{http_code}}" {url}',
            api=api,
            pod_name=f"{self.stateful_set.metadata.name}-0",  # type: ignore
        )

        result = http_status_code == "200"
        return schema.CheckResult(result, "Yes" if result else "No", "Yes")


@ExternalServices.register
class RegistryAccess(AbstractCheck):
    name = "Registry/ACR access"
    description = "Check if kubernetes can pull Piwik PRO images from ACR or other registry"

    phase: Phase = Provide[Dependencies.phase]
    spawner: Spawner = Provide[Dependencies.spawner]
    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]
    registry_server: str = Provide[Dependencies.registry_server]
    registry_secret: client.V1Secret = Provide[Dependencies.registry_secret]

    def perform_check(self) -> Optional[schema.CheckResult]:
        if self.phase is Phase.PRE_CONTRACT:
            return
        stateful_set_name = "backup-tools"
        secret_name = self.registry_secret.metadata.name  # type: ignore
        manifest = mk_stateful_set(
            stateful_set_name,
            f"{self.registry_server}/framework/backup-tools:1.2.0",
            pull_secrets=[client.V1LocalObjectReference(name=secret_name)],
        )
        api = client.AppsV1Api(self.kubernetes_client)
        with self.spawner.stateful_set(manifest):
            try:
                wait_for_pods_ready(api, manifest)
            except TimeoutError:
                return self.major_problem("Cannot access registry")
        return schema.CheckResult(True, "Yes", "Yes")
