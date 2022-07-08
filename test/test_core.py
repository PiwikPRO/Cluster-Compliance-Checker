from dataclasses import asdict
from test.mock_checks.foo import SkippedCheck

from dependency_injector import providers
from dependency_injector.containers import DynamicContainer

from cluster_compliance_checker.core import Core, Section
from cluster_compliance_checker.discovery import discover_sections
from cluster_compliance_checker.template import template

from . import mock_checks


def test_report():
    """High level test similar to what happens in the main function."""
    with open("test/mock_html/valid_schema.html") as file:
        mock_html = file.read()
    dependencies = DynamicContainer()
    dependencies.test_dependency = providers.Object("test value")
    sections = discover_sections(mock_checks)
    core = Core(sections=sections, dependencies=dependencies)
    report = core.generate_report()
    result_html = template(data=asdict(report))
    assert result_html == mock_html


def test_skip_check():
    """Skip a single check by returning None."""
    check = SkippedCheck()
    report = check.generate_report()
    assert report is None


def test_skip_all_checks_in_section():
    """Skip all checks in the section."""

    class TestSection(Section):
        name = "Mock section"
        description = ""
        checks = [SkippedCheck, SkippedCheck, SkippedCheck]

    section = TestSection()
    report = section.generate_report()
    assert report is None
