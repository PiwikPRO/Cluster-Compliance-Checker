from typing import Optional

from dependency_injector.wiring import Provide
from kubernetes import client
from kubernetes.client.api_client import ApiClient

from .. import schema
from ..core import AbstractCheck, Section
from ..dependencies import Dependencies
from ..util import exec_in_pod


class Kernel(Section):
    name = "Kernel"
    description = "Checks related to kernel parameters"


class KernelCheckBase(AbstractCheck):
    kubernetes_client: ApiClient = Provide["kubernetes_client"]
    stateful_set: client.V1StatefulSet = Provide[Dependencies.pod_on_each_node]

    def sysctl_on_each_node(self, variable: str) -> list[str]:
        api = client.CoreV1Api(self.kubernetes_client)
        pod_count = self.stateful_set.status.replicas  # type: ignore
        pod_name = self.stateful_set.metadata.name  # type: ignore
        return [
            exec_in_pod(f"sysctl {variable}", api, f"{pod_name}-{i}").split(" ")[-1]
            for i in range(pod_count)
        ]


@Kernel.register
class IONotifyMaxUserWatches(KernelCheckBase):
    name = "fs.inotify.max_user_watches"
    description = f"Checks {name} kernel value for each kubernetes node"

    def perform_check(self) -> Optional[schema.CheckResult]:
        min_value = 65536
        measured = self.sysctl_on_each_node("fs.inotify.max_user_watches")
        result = all(int(value) >= min_value for value in measured)
        return schema.CheckResult(result, str(measured), f">= {min_value}")


@Kernel.register
class IONotifyMaxUserInstances(KernelCheckBase):
    name = "fs.inotify.max_user_instances"
    description = f"Checks {name} kernel value for each kubernetes node"

    def perform_check(self) -> Optional[schema.CheckResult]:
        min_value = 1024
        measured = self.sysctl_on_each_node("fs.inotify.max_user_instances")
        result = all(int(value) >= min_value for value in measured)
        return schema.CheckResult(result, str(measured), f">= {min_value}")
