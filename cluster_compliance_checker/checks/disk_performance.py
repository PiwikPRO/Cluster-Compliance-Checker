import ast
import itertools
import logging
from abc import abstractmethod, abstractproperty
from pathlib import PosixPath
from typing import Generator, Iterable, Optional

from dependency_injector.wiring import Provide
from kubernetes import client
from kubernetes.client.api.core_v1_api import CoreV1Api
from kubernetes.client.api_client import ApiClient

from .. import schema
from ..core import AbstractCheck, Section
from ..dependencies import Dependencies
from ..enums import Phase
from ..requirements import HardwareRequirements
from ..util import exec_in_pod, iter_pods_in_nodepool


class DiskPerformance(Section):
    name = "Disk I/O"
    description = "Check responsible for determining IOPS."
    phase: Phase = Provide[Dependencies.phase]

    def skip(self) -> bool:
        return self.phase is Phase.PRE_CONTRACT


def generate_args_list(**kwargs: str) -> list[str]:
    return [f"--{key}={val}" for key, val in kwargs.items()]


class BaseCheck(AbstractCheck):
    benchmark_root: str

    kubernetes_client: ApiClient = Provide["kubernetes_client"]
    stateful_set: client.V1StatefulSet = Provide[Dependencies.pod_with_volume_on_each_node]
    requirements: HardwareRequirements = Provide[Dependencies.requirements]

    @abstractmethod
    def list_pods(self) -> Iterable[client.V1Pod]:
        ...

    @abstractproperty
    def iops_threshold(self) -> int:
        ...

    @property
    def api(self):
        return CoreV1Api(self.kubernetes_client)

    def exec_fio(self, pod_name: str, **kwargs) -> dict:
        args = generate_args_list(
            filename=str(PosixPath(self.benchmark_root) / "benchmark.fio"),
            name="test",
            ioengine="libaio",
            direct="1",
            gtod_reduce="1",
            bs="4k",
            iodepth="64",
            size="128Mi",
            **kwargs,
        )
        cmd = " ".join(("fio", "--output-format=json", *args))
        output = exec_in_pod(cmd=cmd, api=self.api, pod_name=pod_name)
        return ast.literal_eval(output)

    def exec_fio_in_each_pod(self, **kwargs) -> Generator[dict, None, None]:
        for pod in self.list_pods():
            pod_name: str = pod.metadata.name  # type: ignore
            yield self.exec_fio(pod_name=pod_name, **kwargs)

    def measure_write_iops_on_each_pod(self) -> Generator[float, None, None]:
        for pod_result in self.exec_fio_in_each_pod(readwrite="randwrite"):
            yield pod_result["jobs"][0]["write"]["iops_mean"]

    def measure_read_iops_on_each_pod(self) -> Generator[float, None, None]:
        for pod_result in self.exec_fio_in_each_pod(readwrite="randread"):
            yield pod_result["jobs"][0]["read"]["iops_mean"]

    def _perform_check(self) -> Optional[schema.CheckResult]:
        try:
            read_iops = self.measure_write_iops_on_each_pod()
            write_iops = self.measure_read_iops_on_each_pod()
        except SyntaxError:
            return self.major_problem("Failed to parse fio output")
        try:
            min_measured_iops = min(itertools.chain(write_iops, read_iops))
        except ValueError:
            logging.warning("There are no pods matching check criteria")
            return
        result = min_measured_iops >= self.iops_threshold
        return schema.CheckResult(result, str(min_measured_iops), f">= {self.iops_threshold}")


class BasePodDiskPerformance(BaseCheck):
    nodepool: str

    @classmethod
    def __init_subclass__(cls):
        cls.name = f"{cls.nodepool.capitalize()} pod's disk performance"
        cls.description = (
            "Perform an I/O benchmark on pod's storage "
            f"(runs or all nodes in the {cls.nodepool} nodepool)"
        )
        cls.perform_check = cls._perform_check

    def list_pods(self) -> Iterable[client.V1Pod]:
        app_label: str = self.stateful_set.metadata.labels["app"]  # type: ignore
        return iter_pods_in_nodepool(self.api, self.nodepool, label_selector=f"app={app_label}")

    @property
    def iops_threshold(self) -> int:
        return self.requirements.nodepool_where(name=self.nodepool).iops


class BasePVCPerformance(BaseCheck):
    @classmethod
    def __init_subclass__(cls):
        cls.name = "PVC performance"
        cls.description = "Perform an I/O benchmark on PVC"
        cls.perform_check = cls._perform_check

    def list_pods(self) -> Iterable[client.V1Pod]:
        app_label: str = self.stateful_set.metadata.labels["app"]  # type: ignore
        namespace: str = self.stateful_set.metadata.namespace  # type: ignore
        return self.api.list_namespaced_pod(
            namespace=namespace, label_selector=f"app={app_label}"
        ).items

    @property
    def iops_threshold(self) -> int:
        """Find max required IOPS value from all PVC requirements."""
        return max(pvc.iops for pvc in self.requirements.pvc_requirements)


@DiskPerformance.register
class AppsPodDiskPerformance(BasePodDiskPerformance):
    nodepool = "apps"
    benchmark_root = "~/"


@DiskPerformance.register
class ServicesPodDiskPerformance(BasePodDiskPerformance):
    nodepool = "services"
    benchmark_root = "~/"


@DiskPerformance.register
class ToolsPodDiskPerformance(BasePodDiskPerformance):
    nodepool = "tools"
    benchmark_root = "~/"


@DiskPerformance.register
class ControlPodDiskPerformance(BasePodDiskPerformance):
    nodepool = "control"
    benchmark_root = "~/"


@DiskPerformance.register
class ClickhousePodDiskPerformance(BasePodDiskPerformance):
    nodepool = "clickhouse"
    benchmark_root = "~/"


@DiskPerformance.register
class PVCPerformance(BasePVCPerformance):
    benchmark_root = "/mnt"
