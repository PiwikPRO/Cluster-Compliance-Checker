import logging
from contextlib import contextmanager
from typing import Generator, Optional

from kubernetes import client
from kubernetes.client.api_client import ApiClient
from kubernetes.client.exceptions import ApiException

from .errors import NoRegistryCredentials


class Spawner:
    def __init__(self, api_client: Optional[ApiClient] = None):
        self.api_client = api_client or ApiClient()

    def _delete_all_pvcs(self, label_selector: str, namespace: str = "default"):
        api = client.CoreV1Api(self.api_client)
        pvcs = api.list_namespaced_persistent_volume_claim(namespace, label_selector=label_selector)
        for pvc in pvcs.items:
            if pvc.metadata is None or pvc.metadata.name is None:
                continue
            pvc_name = pvc.metadata.name
            logging.debug(f"Deleting PVC {pvc_name}...")
            api.delete_namespaced_persistent_volume_claim(pvc_name, namespace)

    @contextmanager
    def secret(
        self, name: str, data: Optional[dict[str, str]], namespace: str = "default"
    ) -> Generator[client.V1Secret, None, None]:
        """Find a secret with a given name.
        If secret was not found and data is provided, create new secret.
        """
        api = client.CoreV1Api(self.api_client)
        try:
            yield api.read_namespaced_secret(name=name, namespace=namespace)
            return
        except ApiException as ex:
            if data is None:
                raise NoRegistryCredentials("Registry credendials not found.") from ex
            logging.debug(f"Secret {name} not found. Creating...")
        try:
            yield api.create_namespaced_secret(
                namespace,
                body=client.V1Secret(
                    type="kubernetes.io/dockerconfigjson",
                    metadata=client.V1ObjectMeta(name=name),
                    data=data,
                ),
            )
        finally:
            api.delete_namespaced_secret(name, namespace)

    @contextmanager
    def service(
        self, manifest: client.V1Service, namespace: str = "default"
    ) -> Generator[client.V1Service, None, None]:
        name: str = manifest.metadata.name  # type: ignore
        api = client.CoreV1Api(self.api_client)
        logging.debug(f"Creating Service {name}...")
        try:
            yield api.create_namespaced_service(namespace=namespace, body=manifest)
        finally:
            logging.debug(f"Deleting Service {name}...")
            api.delete_namespaced_service(name=name, namespace=namespace)

    @contextmanager
    def stateful_set(
        self, manifest: client.V1StatefulSet, namespace: str = "default"
    ) -> Generator[client.V1StatefulSet, None, None]:
        name: str = manifest.metadata.name  # type: ignore
        apps_api = client.AppsV1Api(self.api_client)
        logging.debug(f"Creating StatefulSet {name}...")
        try:
            yield apps_api.create_namespaced_stateful_set(namespace=namespace, body=manifest)
        finally:
            logging.debug(f"Deleting StatefulSet {name}...")
            apps_api.delete_namespaced_stateful_set(name, namespace)
            self._delete_all_pvcs(label_selector=f"app={name}", namespace=namespace)
