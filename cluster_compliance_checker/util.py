import base64
import json
import logging
import time
from typing import Callable, Generator, Optional, TypeVar

from kubernetes import client
from kubernetes.client.api.core_v1_api import CoreV1Api
from kubernetes.stream import stream

T = TypeVar("T", bound=object)


def encode_registry_secret(
    registry_server: str, registry_username: Optional[str], registry_password: Optional[str]
) -> str:
    """Generate base64 encoded registry secret."""
    if registry_username is None and registry_password is None:
        return ""
    data = {
        "auths": {
            registry_server: {
                "username": registry_username,
                "password": registry_password,
            }
        }
    }
    return base64.b64encode(json.dumps(data).encode("UTF-8")).decode("UTF-8")


def wait_for(condition: Callable[[], T], timeout: int, interval: int = 1) -> T:
    start_time = time.perf_counter()
    while time.perf_counter() - start_time < timeout:
        if return_value := condition():
            return return_value
        time.sleep(interval)
    raise TimeoutError


def pods_ready(stateful_set: client.V1StatefulSet) -> bool:
    status = stateful_set.status
    expected_pod_count = stateful_set.spec.replicas  # type: ignore
    if status is None or status.ready_replicas is None:
        return False
    return status.ready_replicas == expected_pod_count


def wait_for_pods_ready(
    api: client.AppsV1Api, stateful_set: client.V1StatefulSet, timeout: int = 60
) -> client.V1StatefulSet:
    name: str = stateful_set.metadata.name  # type: ignore
    namespace: str = stateful_set.metadata.namespace  # type: ignore
    wait_for(
        condition=lambda: pods_ready(api.read_namespaced_stateful_set(name, namespace)),
        timeout=timeout,
    )
    return api.read_namespaced_stateful_set(name, namespace)


def exec_in_pod(cmd: str, api: CoreV1Api, pod_name: str) -> str:
    resp = stream(
        api.connect_get_namespaced_pod_exec,
        pod_name,
        "default",
        command=["/bin/sh", "-c", cmd],
        stdin=False,
        stderr=True,
        stdout=True,
        tty=False,
    )
    output = resp.strip()
    logging.debug(f"Command output: {output}")
    return output


def get_bytes_from_data_size_with_suffix(storage: str) -> int:
    suffix = storage[-2:]
    value = {
        "Ki": 1,
        "Mi": 2,
        "Gi": 3,
        "Ti": 4,
        "Pi": 5,
    }
    return int(storage[:-2]) * pow(1024, value[suffix])


def iter_pods_in_nodepool(
    api: CoreV1Api, nodepool: str, label_selector: Optional[str], namespace: str = "default"
) -> Generator[client.V1Pod, None, None]:
    nodepool_nodes = api.list_node(label_selector=f"{nodepool}=true")
    for node in nodepool_nodes.items:
        node_name: str = node.metadata.name  # type: ignore
        pod_list = api.list_namespaced_pod(
            namespace=namespace,
            field_selector=f"spec.nodeName={node_name}",
            label_selector=label_selector,
        )
        for pod in pod_list.items:
            yield pod
