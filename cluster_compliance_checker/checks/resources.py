from typing import Optional

from dependency_injector.wiring import Provide
from kubernetes import client
from kubernetes.client.api_client import ApiClient

from .. import schema
from ..core import AbstractCheck, Section
from ..dependencies import Dependencies
from ..enums import Phase
from ..requirements import HardwareRequirements
from ..util import get_bytes_from_data_size_with_suffix


class Resources(Section):
    name = "Resources"
    description = (
        "Checks ensuring that infrastructure meets our Hardware and Software Requirements needs."
    )


class NumberOfNodesInNodepool(AbstractCheck):
    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]
    hardware_requirements: HardwareRequirements = Provide[Dependencies.requirements]
    phase: Phase = Provide[Dependencies.phase]

    def get_nodes_number_check_result_for_nodes_in_nodepool(
        self, nodepool_name: str
    ) -> Optional[schema.CheckResult]:
        if self.phase == Phase.PRE_CONTRACT:
            return None

        api = client.CoreV1Api(self.kubernetes_client)

        nodes_required = self.hardware_requirements.nodepool_where(name=nodepool_name).nodes
        nodes_measured = len(api.list_node(label_selector=nodepool_name).items)

        if nodes_measured == 0:
            return self.major_problem(f'No nodes with "{nodepool_name}" label found')

        return schema.CheckResult(
            nodes_required <= nodes_measured,
            nodes_measured,
            f">= {nodes_required}",
        )


@Resources.register
class NumberOfNodesInApps(NumberOfNodesInNodepool):
    name = 'Number of nodes in "apps" nodepool'
    description = """Ensure that nodes count in "apps" nodepool matches our requirements"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_nodes_number_check_result_for_nodes_in_nodepool("apps")


@Resources.register
class NumberOfNodesInTools(NumberOfNodesInNodepool):
    name = 'Number of nodes in "tools" nodepool'
    description = """Ensure that nodes count in "tools" nodepool matches our requirements"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_nodes_number_check_result_for_nodes_in_nodepool("tools")


@Resources.register
class NumberOfNodesInServices(NumberOfNodesInNodepool):
    name = 'Number of nodes in "services" nodepool'
    description = """Ensure that nodes count in "services" nodepool matches our requirements"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_nodes_number_check_result_for_nodes_in_nodepool("services")


@Resources.register
class NumberOfNodesInClickhouse(NumberOfNodesInNodepool):
    name = 'Number of nodes in "clickhouse" nodepool'
    description = """Ensure that nodes count in "clickhouse" nodepool matches our requirements"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_nodes_number_check_result_for_nodes_in_nodepool("clickhouse")


@Resources.register
class NumberOfNodesInClickhouseTrucker(NumberOfNodesInNodepool):
    name = 'Number of nodes in "clickhouse_trucker" nodepool'
    description = (
        """Ensure that nodes count in "clickhouse_trucker" nodepool matches our requirements"""
    )

    def perform_check(self) -> Optional[schema.CheckResult]:
        if not any(
            nodepool.name == "clickhouse_trucker"
            for nodepool in self.hardware_requirements.nodepool_requirements
        ):
            return None

        return self.get_nodes_number_check_result_for_nodes_in_nodepool("clickhouse_trucker")


class CPUInNodesInNodepool(AbstractCheck):
    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]
    hardware_requirements: HardwareRequirements = Provide[Dependencies.requirements]
    phase: Phase = Provide[Dependencies.phase]

    def get_cpu_check_result_for_nodes_in_nodepool(
        self, nodepool_name: str
    ) -> Optional[schema.CheckResult]:
        if self.phase == Phase.PRE_CONTRACT:
            return None

        api = client.CoreV1Api(self.kubernetes_client)

        cpu_required = self.hardware_requirements.nodepool_where(name=nodepool_name).cpus
        cpus = []
        for node in api.list_node(label_selector=nodepool_name).items:
            cpus.append(int(node.status.capacity["cpu"]))

        if len(cpus) == 0:
            return self.major_problem(f'No nodes with "{nodepool_name}" label found')

        return schema.CheckResult(
            all(cpu_required <= cpu for cpu in cpus),
            cpus,
            f">= {cpu_required}",
        )


@Resources.register
class CPUInNodesInApps(CPUInNodesInNodepool):
    name = 'Number of CPUs in "apps" nodepool'
    description = """Ensure that each node in "apps" nodepool has enough CPUs"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_cpu_check_result_for_nodes_in_nodepool("apps")


@Resources.register
class CPUInNodesInTools(CPUInNodesInNodepool):
    name = 'Number of CPUs in "tools" nodepool'
    description = """Ensure that each node in "tools" nodepool has enough CPUs"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_cpu_check_result_for_nodes_in_nodepool("tools")


@Resources.register
class CPUInNodesInServices(CPUInNodesInNodepool):
    name = 'Number of CPUs in "services" nodepool'
    description = """Ensure that each node in "services" nodepool has enough CPUs"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_cpu_check_result_for_nodes_in_nodepool("services")


@Resources.register
class CPUInNodesInClickhouse(CPUInNodesInNodepool):
    name = 'Number of CPUs in "clickhouse" nodepool'
    description = """Ensure that each node in "clickhouse" nodepool has enough CPUs"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_cpu_check_result_for_nodes_in_nodepool("clickhouse")


class CPUInNodesInClickhouseTrucker(CPUInNodesInNodepool):
    name = 'Number of CPUs in "clickhouse_trucker" nodepool'
    description = """Ensure that each node in "clickhouse_trucker" nodepool has enough CPUs"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        if not any(
            nodepool.name == "clickhouse_trucker"
            for nodepool in self.hardware_requirements.nodepool_requirements
        ):
            return None

        return self.get_cpu_check_result_for_nodes_in_nodepool("clickhouse_trucker")


class MemoryInNodesInNodepool(AbstractCheck):
    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]
    hardware_requirements: HardwareRequirements = Provide[Dependencies.requirements]
    phase: Phase = Provide[Dependencies.phase]

    def get_memory_check_result_for_nodes_in_nodepool(
        self, nodepool_name: str
    ) -> Optional[schema.CheckResult]:
        if self.phase == Phase.PRE_CONTRACT:
            return None

        api = client.CoreV1Api(self.kubernetes_client)

        memory_required_value = self.hardware_requirements.nodepool_where(name=nodepool_name).memory
        memory_required = get_bytes_from_data_size_with_suffix(f"{memory_required_value}Gi")
        memory_tolerance = 0.05
        memory_list = []
        for node in api.list_node(label_selector=nodepool_name).items:
            memory_list.append(get_bytes_from_data_size_with_suffix(node.status.capacity["memory"]))

        if len(memory_list) == 0:
            return self.major_problem(f'No nodes with "{nodepool_name}" label found')

        return schema.CheckResult(
            all(memory_required * (1 - memory_tolerance) <= memory for memory in memory_list),
            [f"{round(memory * pow(1024, -3), 2)}Gi" for memory in memory_list],
            f">= {round(memory_required * pow(1024, -3), 2)}Gi",
        )


@Resources.register
class MemoryInNodesInApps(MemoryInNodesInNodepool):
    name = 'Nodes\' memory in "apps" nodepool'
    description = """Ensure that each node in "apps" nodepool has enough memory"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_memory_check_result_for_nodes_in_nodepool("apps")


@Resources.register
class MemoryInNodesInTools(MemoryInNodesInNodepool):
    name = 'Nodes\' memory in "tools" nodepool'
    description = """Ensure that each node in "tools" nodepool has enough memory"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_memory_check_result_for_nodes_in_nodepool("tools")


@Resources.register
class MemoryInNodesInServices(MemoryInNodesInNodepool):
    name = 'Nodes\' memory in "services" nodepool'
    description = """Ensure that each node in "services" nodepool has enough memory"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_memory_check_result_for_nodes_in_nodepool("services")


@Resources.register
class MemoryInNodesInClickhouse(MemoryInNodesInNodepool):
    name = 'Nodes\' memory in "clickhouse" nodepool'
    description = """Ensure that each node in "clickhouse" nodepool has enough memory"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_memory_check_result_for_nodes_in_nodepool("clickhouse")


@Resources.register
class MemoryInNodesInClickhouseTrucker(MemoryInNodesInNodepool):
    name = 'Nodes\' memory in "clickhouse" nodepool'
    description = """Ensure that each node in "clickhouse" nodepool has enough memory"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        if not any(
            nodepool.name == "clickhouse_trucker"
            for nodepool in self.hardware_requirements.nodepool_requirements
        ):
            return None

        return self.get_memory_check_result_for_nodes_in_nodepool("clickhouse_trucker")


class EphemeralStorageInNodesInNodepool(AbstractCheck):
    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]
    hardware_requirements: HardwareRequirements = Provide[Dependencies.requirements]
    phase: Phase = Provide[Dependencies.phase]

    def get_ephemeral_storage_check_result_for_nodes_in_nodepool(
        self, nodepool_name: str
    ) -> Optional[schema.CheckResult]:
        if self.phase == Phase.PRE_CONTRACT:
            return None

        api = client.CoreV1Api(self.kubernetes_client)

        ephemeral_storage_required_value = self.hardware_requirements.nodepool_where(
            name=nodepool_name
        ).disk_space
        ephemeral_storage_required = get_bytes_from_data_size_with_suffix(
            f"{ephemeral_storage_required_value}Gi"
        )
        ephemeral_storage_tolerance = 0.05
        ephemeral_storage_list = []
        for node in api.list_node(label_selector=nodepool_name).items:
            ephemeral_storage_list.append(
                get_bytes_from_data_size_with_suffix(node.status.capacity["ephemeral-storage"])
            )

        if len(ephemeral_storage_list) == 0:
            return self.major_problem(f'No nodes with "{nodepool_name}" label found')

        return schema.CheckResult(
            all(
                ephemeral_storage_required * (1 - ephemeral_storage_tolerance) <= ephemeral_storage
                for ephemeral_storage in ephemeral_storage_list
            ),
            [
                f"{round(ephemeral_storage * pow(1024, -3), 2)}Gi"
                for ephemeral_storage in ephemeral_storage_list
            ],
            f">= {round(ephemeral_storage_required * pow(1024, -3), 2)}Gi",
        )


@Resources.register
class EphemeralStorageInNodesInApps(EphemeralStorageInNodesInNodepool):
    name = 'Nodes\' ephemeral storage in "apps" nodepool'
    description = """Ensure that each node in "apps" nodepool has enough ephemeral torage"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_ephemeral_storage_check_result_for_nodes_in_nodepool("apps")


@Resources.register
class EphemeralStorageInNodesInTools(EphemeralStorageInNodesInNodepool):
    name = 'Nodes\' ephemeral storage in "tools" nodepool'
    description = """Ensure that each node in "tools" nodepool has enough ephemeral storage"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_ephemeral_storage_check_result_for_nodes_in_nodepool("tools")


@Resources.register
class EphemeralStorageInNodesInServices(EphemeralStorageInNodesInNodepool):
    name = 'Nodes\' ephemeral storage in "services" nodepool'
    description = """Ensure that each node in "services" nodepool has enough ephemeral storage"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_ephemeral_storage_check_result_for_nodes_in_nodepool("services")


@Resources.register
class EphemeralStorageInNodesInClickhouse(EphemeralStorageInNodesInNodepool):
    name = 'Nodes\' ephemeral storage in "clickhouse" nodepool'
    description = """Ensure that each node in "clickhouse" nodepool has enough ephemeral storage"""

    def perform_check(self) -> Optional[schema.CheckResult]:
        return self.get_ephemeral_storage_check_result_for_nodes_in_nodepool("clickhouse")


@Resources.register
class EphemeralStorageInNodesInClickhouseTrucker(EphemeralStorageInNodesInNodepool):
    name = 'Nodes\' ephemeral storage in "clickhouse_trucker" nodepool'
    description = (
        """Ensure that each node in "clickhouse_trucker" nodepool has enough ephemeral storage"""
    )

    def perform_check(self) -> Optional[schema.CheckResult]:
        if not any(
            nodepool.name == "clickhouse_trucker"
            for nodepool in self.hardware_requirements.nodepool_requirements
        ):
            return None

        return self.get_ephemeral_storage_check_result_for_nodes_in_nodepool("clickhouse_trucker")
