import json

import pytest
from bs4 import BeautifulSoup

from cluster_compliance_checker.template import template


@pytest.mark.parametrize(
    "file_name",
    [
        ("valid_schema"),
        ("valid_schema_with_major_problem"),
        ("valid_schema_empty_sections"),
        ("valid_schema_mouthful_section_description"),
        ("valid_schema_mouthful_check_description"),
        ("invalid_schema_incorrect_section_name"),
    ],
)
def test_valid(file_name):
    with open(f"test/mock_html/{file_name}.html") as file:
        mock_html = BeautifulSoup(file, features="html.parser")

    with open(f"test/mock_data/{file_name}.json") as file:
        data = json.load(file)
    result_html = BeautifulSoup(template(data), features="html.parser")

    assert mock_html == result_html
