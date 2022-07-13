"""Context managers and functions, that can be used as check dependencies.
"""
from pathlib import Path
from typing import Generator, Optional

from dependency_injector import containers, providers
from kubernetes import client
from kubernetes.client.api_client import ApiClient
from kubernetes.client.exceptions import ApiException
from kubernetes.config.config_exception import ConfigException
from kubernetes.config.incluster_config import load_incluster_config
from kubernetes.config.kube_config import KUBE_CONFIG_DEFAULT_LOCATION, load_kube_config
from urllib3.exceptions import MaxRetryError

from . import manifests
from .enums import MaintenanceType, MonthlyTraffic, Phase
from .errors import KubernetesClientError
from .requirements import HardwareRequirements
from .spawner import Spawner
from .util import encode_registry_secret, wait_for


def get_kubernetes_client() -> Generator[ApiClient, None, None]:
    """Load proper kubernetes client configuration (from kubeconfig or service account)
    and instantiate an API client object.
    """
    config_path = Path(KUBE_CONFIG_DEFAULT_LOCATION).expanduser()
    try:
        if config_path.is_file():
            load_kube_config()
        else:
            load_incluster_config()
    except ConfigException as ex:
        raise KubernetesClientError("Failed to load kubernetes config") from ex

    with ApiClient() as api_client:  # type: ignore
        try:
            api_client.call_api("/readyz", "GET", auth_settings=["BearerToken"])
        except (ApiException, MaxRetryError) as ex:
            raise KubernetesClientError("Kubernetes health check failed") from ex
        yield api_client


def spawn_pod_on_each_node(
    spawner: Spawner,
    image: str,
    secret: Optional[client.V1Secret] = None,
    volume_size: Optional[str] = None,
    storage_class: Optional[str] = None,
) -> Generator[client.V1StatefulSet, None, None]:
    name = "pod-on-each-node"
    namespace = "default"
    core_api = client.CoreV1Api(spawner.api_client)
    apps_api = client.AppsV1Api(spawner.api_client)
    node_count = len(core_api.list_node().items)
    secret_name = secret.metadata.name  # type: ignore
    pull_secrets = [] if secret is None else [client.V1LocalObjectReference(name=secret_name)]
    mounts = (
        {"/mnt": manifests.mk_pvc(name, size=volume_size, storage_class_name=storage_class or None)}
        if volume_size
        else None
    )

    def pods_ready():
        stateful_set = apps_api.read_namespaced_stateful_set(name, namespace)
        status = stateful_set.status
        if status is None or status.ready_replicas is None:
            return
        if status.ready_replicas == node_count:
            return stateful_set

    manifest = manifests.mk_stateful_set(
        name=name,
        image=image,
        replicas=node_count,
        namespace=namespace,
        pull_secrets=pull_secrets,
        mounts=mounts,
    )
    with spawner.stateful_set(manifest):
        stateful_set = wait_for(pods_ready, 120)
        yield stateful_set  # type: ignore


def spawn_single_pod(
    spawner: Spawner, image: str, secret: Optional[client.V1Secret] = None
) -> Generator[client.V1StatefulSet, None, None]:
    name = "single-pod"
    namespace = "default"
    apps_api = client.AppsV1Api(spawner.api_client)
    secret_name = secret.metadata.name  # type: ignore
    pull_secrets = [] if secret is None else [client.V1LocalObjectReference(name=secret_name)]

    def pod_ready():
        stateful_set = apps_api.read_namespaced_stateful_set(name, namespace)
        status = stateful_set.status
        if status is None or status.ready_replicas is None:
            return
        if status.ready_replicas == 1:
            return stateful_set

    manifest = manifests.mk_stateful_set(
        name=name, image=image, replicas=1, namespace=namespace, pull_secrets=pull_secrets
    )
    with spawner.stateful_set(manifest):
        stateful_set = wait_for(pod_ready, 60)
        yield stateful_set  # type: ignore


def registry_secret(spawner: Spawner, data: str) -> Generator[client.V1Secret, None, None]:
    docker_config = {".dockerconfigjson": data} if data else None
    with spawner.secret("piwik-pro-registry", docker_config) as secret:
        yield secret


class Dependencies(containers.DeclarativeContainer):
    offline = providers.Dependency(bool)
    monthly_traffic = providers.Dependency(MonthlyTraffic)
    maintenance_type = providers.Dependency(MaintenanceType)
    phase = providers.Dependency(Phase)
    requirements = providers.Dependency(HardwareRequirements)
    registry_server = providers.Dependency(str)
    registry_username = providers.Dependency(str)
    registry_password = providers.Dependency(str)
    tools_image = providers.Dependency(str)
    storage_class = providers.Dependency(str)
    namespace_whitelist = providers.Dependency(list)

    kubernetes_client = providers.Resource(get_kubernetes_client)
    spawner = providers.Singleton(Spawner, api_client=kubernetes_client)
    registry_secret_data = providers.Factory(
        encode_registry_secret,
        registry_server=registry_server,
        registry_username=registry_username,
        registry_password=registry_password,
    )
    registry_secret = providers.Resource(
        registry_secret, spawner=spawner, data=registry_secret_data
    )
    pod_on_each_node = providers.Resource(
        spawn_pod_on_each_node, spawner=spawner, image=tools_image, secret=registry_secret
    )
    pod_with_volume_on_each_node = providers.Resource(
        spawn_pod_on_each_node,
        spawner=spawner,
        image=tools_image,
        secret=registry_secret,
        volume_size="1Gi",
        storage_class=storage_class,
    )
    single_pod = providers.Resource(
        spawn_single_pod, spawner=spawner, image=tools_image, secret=registry_secret
    )
