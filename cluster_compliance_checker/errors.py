class CheckerError(Exception):
    ...


class KubernetesClientError(CheckerError):
    ...


class NoRegistryCredentials(CheckerError):
    ...
