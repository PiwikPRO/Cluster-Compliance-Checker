import pytest

from cluster_compliance_checker import schema
from cluster_compliance_checker.core import AbstractCheck, Core, Section


def test_check_with_major_problem():
    class TestCheck(AbstractCheck):
        name = ""
        description = ""

        def perform_check(self):
            return self.major_problem("This is a problem")

    check = TestCheck()
    result = check.perform_check()
    assert result == schema.CheckResult(False, "", "", "This is a problem")


@pytest.mark.parametrize(
    "checks,expected_problems",
    [
        ([schema.Check("", "", schema.CheckResult(False, "", "", None))], []),
        ([schema.Check("", "", schema.CheckResult(False, "", "", "problem 1"))], ["problem 1"]),
        ([schema.Check("", "", schema.CheckResult(False, "", "", "problem 1"))] * 2, ["problem 1"]),
        (
            [
                schema.Check("", "", schema.CheckResult(False, "", "", "problem 3")),
                schema.Check("", "", schema.CheckResult(False, "", "", "problem 2")),
                schema.Check("", "", schema.CheckResult(False, "", "", "problem 1")),
            ],
            ["problem 1", "problem 2", "problem 3"],
        ),
        (
            [
                schema.Check("", "", schema.CheckResult(False, "", "", None)),
                schema.Check("", "", schema.CheckResult(False, "", "", "problem 1")),
                schema.Check("", "", schema.CheckResult(False, "", "", "problem 1")),
                schema.Check("", "", schema.CheckResult(False, "", "", "problem 2")),
                schema.Check("", "", schema.CheckResult(False, "", "", "problem 3")),
            ],
            ["problem 1", "problem 2", "problem 3"],
        ),
    ],
)
def test_extract_major_problems_from_checks(
    checks: list[schema.Check], expected_problems: list[str]
):
    major_problems = Section._extract_major_problems(checks)
    assert major_problems == expected_problems


@pytest.mark.parametrize(
    "sections,expected_problems",
    [
        ([schema.Section("", "", False, [], major_problems=[])], []),
        (
            [schema.Section("", "", False, [], major_problems=["problem 1", "problem 2"])],
            ["problem 1", "problem 2"],
        ),
        (
            [
                schema.Section("", "", False, [], major_problems=["problem 3"]),
                schema.Section("", "", False, [], major_problems=["problem 2"]),
                schema.Section("", "", False, [], major_problems=["problem 1"]),
            ],
            ["problem 1", "problem 2", "problem 3"],
        ),
        (
            [
                schema.Section("", "", True, [], major_problems=[]),
                schema.Section("", "", False, [], major_problems=["problem 1", "problem 2"]),
                schema.Section("", "", False, [], major_problems=["problem 2", "problem 3"]),
                schema.Section("", "", False, [], major_problems=["problem 1", "problem 3"]),
            ],
            ["problem 1", "problem 2", "problem 3"],
        ),
    ],
)
def test_extract_major_problems_from_sections(
    sections: list[schema.Section], expected_problems: list[str]
):
    major_problems = Core._extract_major_problems(sections)
    assert major_problems == expected_problems
