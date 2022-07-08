from typing import Mapping, Tuple

import pytest

from cluster_compliance_checker.discovery import process_checks_to_find


@pytest.mark.parametrize(
    "input_,output",
    (
        (None, {}),
        ((), {}),
        (("section",), {"section": []}),
        (("section.check", "section.check2"), {"section": ["check", "check2"]}),
        (("section.check", "bla.bla"), {"section": ["check"], "bla": ["bla"]}),
    ),
)
def test_process_checks_to_find(input_: Tuple[str], output: Mapping[str, str]):
    result = process_checks_to_find(input_)
    assert result == output


@pytest.mark.parametrize(
    "input_",
    (
        ("section.check.that.is.too.long",),
        ("",),
        (".",),
    ),
)
def test_invalid_checks_to_find(input_: Tuple[str]):
    with pytest.raises(ValueError):
        process_checks_to_find(input_)
