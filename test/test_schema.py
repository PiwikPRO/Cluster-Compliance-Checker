import json

import dacite.core
import pytest

from cluster_compliance_checker.schema import Report


@pytest.mark.parametrize(
    "file_name",
    [
        ("test/mock_data/valid_schema.json"),
        ("test/mock_data/valid_schema_empty_sections.json"),
    ],
)
def test_valid(file_name):
    with open(file_name) as file:
        data = json.load(file)
    dacite.core.from_dict(Report, data)
