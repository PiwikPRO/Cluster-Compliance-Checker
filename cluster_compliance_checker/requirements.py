"""Hardware requirements, based on expected monthly traffic.
"""
from dataclasses import asdict, dataclass

from .enums import MonthlyTraffic


@dataclass
class Nodepool:
    name: str
    nodes: int
    cpus: int
    memory: int
    disk_space: int
    iops: int


@dataclass
class PVC:
    name: str
    size: int
    iops: int


@dataclass
class HardwareRequirements:
    nodepool_requirements: list[Nodepool]
    pvc_requirements: list[PVC]

    def nodepool_where(self, **kwargs) -> Nodepool:
        """Returns first nodepool satisfying conditions.
        e.g. hardware_configurations.nodepool_where(name="services")
        """
        for nodepool in self.nodepool_requirements:
            if kwargs.items() <= asdict(nodepool).items():
                return nodepool
        raise ValueError(f"There are no nodepools satisfying conditions: {kwargs}")

    def pvc_where(self, **kwargs) -> PVC:
        """Returns first PVC satisfying conditions.
        e.g. hardware_configurations.pvc_where(name="zookeeper")
        """
        for pvc in self.pvc_requirements:
            if kwargs.items() <= asdict(pvc).items():
                return pvc
        raise ValueError(f"There are no nodepools satisfying conditions: {kwargs}")


hardware_configurations = {
    MonthlyTraffic._10M: HardwareRequirements(
        nodepool_requirements=[
            Nodepool(name="apps", nodes=3, cpus=4, memory=16, disk_space=64, iops=500),
            Nodepool(name="tools", nodes=1, cpus=4, memory=32, disk_space=64, iops=240),
            Nodepool(name="services", nodes=1, cpus=8, memory=32, disk_space=64, iops=240),
            Nodepool(name="clickhouse", nodes=1, cpus=4, memory=16, disk_space=64, iops=500),
        ],
        pvc_requirements=[
            PVC(name="clickhouse", size=256, iops=1000),
            PVC(name="zookeeper", size=32, iops=120),
            PVC(name="rabbitmq", size=32, iops=240),
            PVC(name="consul", size=16, iops=120),
            PVC(name="redis", size=16, iops=120),
            PVC(name="redis_cache", size=16, iops=120),
            PVC(name="monitoring", size=128, iops=500),
        ],
    ),
    MonthlyTraffic._50M: HardwareRequirements(
        nodepool_requirements=[
            Nodepool(name="apps", nodes=3, cpus=4, memory=16, disk_space=64, iops=500),
            Nodepool(name="tools", nodes=1, cpus=4, memory=32, disk_space=64, iops=240),
            Nodepool(name="services", nodes=3, cpus=4, memory=16, disk_space=64, iops=240),
            Nodepool(name="clickhouse", nodes=2, cpus=4, memory=16, disk_space=64, iops=500),
        ],
        pvc_requirements=[
            PVC(name="clickhouse", size=256, iops=1000),
            PVC(name="zookeeper", size=32, iops=120),
            PVC(name="zookeeper_data_transaction_log", size=128, iops=500),
            PVC(name="rabbitmq", size=64, iops=240),
            PVC(name="consul", size=32, iops=120),
            PVC(name="redis", size=32, iops=120),
            PVC(name="redis_cache", size=32, iops=120),
            PVC(name="monitoring", size=256, iops=500),
        ],
    ),
    MonthlyTraffic._100M: HardwareRequirements(
        nodepool_requirements=[
            Nodepool(name="apps", nodes=3, cpus=4, memory=16, disk_space=64, iops=500),
            Nodepool(name="tools", nodes=1, cpus=4, memory=32, disk_space=64, iops=240),
            Nodepool(name="services", nodes=3, cpus=4, memory=16, disk_space=64, iops=240),
            Nodepool(name="clickhouse", nodes=2, cpus=4, memory=32, disk_space=64, iops=500),
        ],
        pvc_requirements=[
            PVC(name="clickhouse", size=512, iops=2000),
            PVC(name="zookeeper", size=32, iops=120),
            PVC(name="zookeeper_data_transaction_log", size=128, iops=500),
            PVC(name="rabbitmq", size=64, iops=240),
            PVC(name="consul", size=32, iops=120),
            PVC(name="redis", size=32, iops=120),
            PVC(name="redis_cache", size=32, iops=120),
            PVC(name="monitoring", size=256, iops=500),
        ],
    ),
    MonthlyTraffic._250M: HardwareRequirements(
        nodepool_requirements=[
            Nodepool(name="apps", nodes=3, cpus=8, memory=16, disk_space=64, iops=500),
            Nodepool(name="tools", nodes=1, cpus=4, memory=32, disk_space=64, iops=240),
            Nodepool(name="services", nodes=3, cpus=8, memory=32, disk_space=64, iops=240),
            Nodepool(name="clickhouse", nodes=4, cpus=8, memory=64, disk_space=64, iops=500),
            Nodepool(
                name="clickhouse_trucker", nodes=2, cpus=4, memory=16, disk_space=64, iops=500
            ),
        ],
        pvc_requirements=[
            PVC(name="clickhouse", size=512, iops=2000),
            PVC(name="clickhouse_trucker", size=128, iops=1000),
            PVC(name="zookeeper", size=32, iops=120),
            PVC(name="zookeeper_data_transaction_log", size=128, iops=500),
            PVC(name="rabbitmq", size=128, iops=500),
            PVC(name="consul", size=32, iops=120),
            PVC(name="redis", size=32, iops=120),
            PVC(name="redis_cache", size=32, iops=120),
            PVC(name="monitoring", size=512, iops=2000),
        ],
    ),
    MonthlyTraffic._500M: HardwareRequirements(
        nodepool_requirements=[
            Nodepool(name="apps", nodes=4, cpus=8, memory=16, disk_space=64, iops=500),
            Nodepool(name="tools", nodes=1, cpus=4, memory=32, disk_space=64, iops=240),
            Nodepool(name="services", nodes=3, cpus=8, memory=32, disk_space=64, iops=240),
            Nodepool(name="clickhouse", nodes=4, cpus=16, memory=128, disk_space=64, iops=500),
            Nodepool(
                name="clickhouse_trucker", nodes=2, cpus=4, memory=16, disk_space=64, iops=500
            ),
        ],
        pvc_requirements=[
            PVC(name="clickhouse", size=1024, iops=5000),
            PVC(name="clickhouse_trucker", size=128, iops=1000),
            PVC(name="zookeeper", size=32, iops=120),
            PVC(name="zookeeper_data_transaction_log", size=128, iops=500),
            PVC(name="rabbitmq", size=128, iops=500),
            PVC(name="consul", size=32, iops=120),
            PVC(name="redis", size=32, iops=120),
            PVC(name="redis_cache", size=32, iops=120),
            PVC(name="monitoring", size=512, iops=2000),
        ],
    ),
}
