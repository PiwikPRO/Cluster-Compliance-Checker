import pytest
from kubernetes import client

from cluster_compliance_checker.checks.kubernetes import KubernetesVersion
from cluster_compliance_checker.schema import CheckResult


class ApiClientMock:
    _mock_endpoints = {}

    def register_mock_endpoint(self, endpoint: str, returned_value):
        self._mock_endpoints[endpoint] = returned_value

    def call_api(self, resource_path, *args, **kwargs):
        return self._mock_endpoints[resource_path]

    def select_header_accept(self, _):
        return "application/json"


def mk_version_info(**kwargs):
    arguments = {
        "build_date": "",
        "compiler": "",
        "git_commit": "",
        "git_version": "",
        "git_tree_state": "",
        "go_version": "",
        "major": "",
        "minor": "",
        "platform": "",
    }
    arguments.update(kwargs)
    return client.VersionInfo(**arguments)


def mk_node_list(nodes):
    return client.V1NodeList(
        items=[
            client.V1Node(metadata=client.V1ObjectMeta(name=node["name"], labels=node["labels"]))
            for node in nodes
        ]
    )


@pytest.mark.parametrize(
    "endpoints,check,expected_result",
    [
        (
            [("/version/", mk_version_info(git_version="v1.21.0"))],
            KubernetesVersion(),
            CheckResult(True, "v1.21", ">=1.21 and <=1.24"),
        ),
        (
            [("/version/", mk_version_info(git_version="v1.23.0-eks.232"))],
            KubernetesVersion(),
            CheckResult(True, "v1.23", ">=1.21 and <=1.24"),
        ),
        (
            [("/version/", mk_version_info(git_version="1.25.1+dev.232"))],
            KubernetesVersion(),
            CheckResult(False, "1.25", ">=1.21 and <=1.24"),
        ),
    ],
)
def test_kubernetes_check(endpoints, check, expected_result):
    api_client = ApiClientMock()
    for path, response in endpoints:
        api_client.register_mock_endpoint(path, response)

    check.kubernetes_client = api_client
    assert check.perform_check() == expected_result
