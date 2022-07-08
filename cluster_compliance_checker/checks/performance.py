import ast
from typing import Optional

from dependency_injector.wiring import Provide
from kubernetes import client
from kubernetes.client.api_client import ApiClient

from .. import schema
from ..core import AbstractCheck, Section
from ..dependencies import Dependencies
from ..enums import Phase
from ..spawner import Spawner
from ..util import exec_in_pod


class CPUPerformance(Section):
    name = "Performance"
    description = (
        "Checks responsible for ensuring that cluster has enough performance to handle PPAS"
    )
    phase: Phase = Provide[Dependencies.phase]

    def skip(self) -> bool:
        return self.phase is Phase.PRE_CONTRACT


@CPUPerformance.register
class NoisyNeighbours(AbstractCheck):
    name = "No noisy neighbours"
    description = (
        "Check that the cluster is not overloaded to ensure "
        "that the product will have enough resources to run properly. "
        "Result is percentage of CPU usage for user space processes."
    )
    spawner: Spawner = Provide[Dependencies.spawner]
    kubernetes_client: ApiClient = Provide["kubernetes_client"]
    stateful_set: client.V1StatefulSet = Provide[Dependencies.pod_on_each_node]

    def mpstat_on_each_node(self, mpstat_arguments: str) -> list[dict]:
        api = client.CoreV1Api(self.kubernetes_client)
        pod_count = self.stateful_set.status.replicas  # type: ignore
        pod_name = self.stateful_set.metadata.name  # type: ignore
        return [
            # Unfortunately, python kubernetes client returns invalid JSON output, so it
            # needs to be fixed by "ast.literal_eval" below.
            ast.literal_eval(
                exec_in_pod(api=api, pod_name=f"{pod_name}-{i}", cmd=f"mpstat {mpstat_arguments}")
            )["sysstat"]["hosts"][0]["statistics"]
            for i in range(pod_count)
        ]

    def perform_check(self) -> Optional[schema.CheckResult]:
        checks_count = 5
        checks_interval = 2

        perfomance_check_results = self.mpstat_on_each_node(
            f"{checks_interval} {checks_count} -o JSON"
        )
        threshold = 5

        max_check_results: list[float] = [
            max(stats["cpu-load"][0]["usr"] for stats in check)
            for check in perfomance_check_results
        ]

        result = all(utilization < threshold for utilization in max_check_results)
        return schema.CheckResult(result, str(max_check_results), f"> {threshold}")
