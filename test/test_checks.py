import pytest
from kubernetes import client

from cluster_compliance_checker.checks.kubernetes import KubernetesVersion, get_nodes_list_by_label
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
            [("/version/", mk_version_info(git_version="v1.23.0"))],
            KubernetesVersion(),
            CheckResult(True, "v1.23.0", ">v1.21.0 and <v1.24.0"),
        ),
    ],
)
def test_kubernetes_check(endpoints, check, expected_result):
    api_client = ApiClientMock()
    for path, response in endpoints:
        api_client.register_mock_endpoint(path, response)

    check.kubernetes_client = api_client
    assert check.perform_check() == expected_result


@pytest.mark.parametrize(
    "endpoints,label,expected_result",
    [
        (
            [("/api/v1/nodes", mk_node_list([{"name": "foo", "labels": {"services": "true"}}]))],
            {"services": "true"},
            mk_node_list([{"name": "foo", "labels": {"services": "true"}}]).items,
        ),
        (
            [
                (
                    "/api/v1/nodes",
                    mk_node_list(
                        [
                            {"name": "foo", "labels": {"services": "true"}},
                            {"name": "bar", "labels": {"services": "true"}},
                            {"name": "foobar", "labels": {"other": "true"}},
                        ]
                    ),
                )
            ],
            {"services": "true"},
            mk_node_list(
                [
                    {"name": "foo", "labels": {"services": "true"}},
                    {"name": "bar", "labels": {"services": "true"}},
                ]
            ).items,
        ),
        (
            [("/api/v1/nodes", mk_node_list([{"name": "foobar", "labels": {"other": "true"}}]))],
            {"services": "true"},
            mk_node_list([]).items,
        ),
    ],
)
def test_get_nodes_list_by_label(endpoints, label, expected_result):
    api_client = ApiClientMock()
    for path, response in endpoints:
        api_client.register_mock_endpoint(path, response)

    assert get_nodes_list_by_label(api_client, label) == expected_result  # type: ignore
