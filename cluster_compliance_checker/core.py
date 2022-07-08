import inspect
import logging
from abc import ABC, abstractmethod
from copy import copy
from itertools import chain
from typing import Generator, Optional, Type

from dependency_injector.containers import Container
from rich.console import Console

from . import schema


def _log_result(msg: str, *, status: bool = False, skipped: bool = False):
    level = logging.INFO
    if skipped:
        status_msg = "[bold yellow]SKIPPED[/]"
        level = logging.DEBUG
    elif status:
        status_msg = "[bold green]PASSED[/]"
    else:
        status_msg = "[bold red]FAILED[/]"
    logging.log(level, f"{msg} {status_msg}", extra={"markup": True})


def _log_unexpected_error(check_name: str, error: Exception):
    logging.debug(error, exc_info=True)
    logging.error(
        f"Check [blue]{check_name}[/] encountered an unexpected error: " f"[bold red]{error}[/]",
        extra={"markup": True},
    )


class AbstractCheck(ABC):
    """Abstract class representing a single check.
    You can extend this class and implement a `perform_check` method.
    """

    name: str
    description: str

    def __init__(self, *, console: Optional[Console] = None):
        self.console = console or Console()

    @classmethod
    def __init_subclass__(cls):
        if inspect.isabstract(cls):
            return
        if not hasattr(cls, "name"):
            raise AttributeError(f'Class {cls.__name__} must have a "name" attribute')
        if not hasattr(cls, "description"):
            raise AttributeError(f'Class {cls.__name__} must have a "description" attribute')

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return self.name

    @abstractmethod
    def perform_check(self) -> Optional[schema.CheckResult]:
        pass  # pragma: nocover

    def major_problem(self, major_problem: str):
        logging.error(
            f"Check {self} encountered an error: [bold red]{major_problem}[/]",
            extra={"markup": True},
        )
        return schema.CheckResult(
            result=False, measured="", expected="", major_problem=major_problem
        )

    def generate_report(self) -> Optional[schema.Check]:
        """Perform the check and return result.
        Returns None if the check was skipped.
        """
        logging.debug(f"Running check: {self}")
        try:
            with self.console.status(f"Running check: {self}..."):
                check_result = self.perform_check()
        except Exception as ex:
            _log_unexpected_error(str(self), ex)
            check_result = schema.CheckResult(False, "Internal error", "Unknown")
        if check_result is None:
            _log_result(f"Check {self}", skipped=True)
            return None
        logging.debug(f"{self} report: {check_result}")
        _log_result(f"Check {self}", status=check_result.result)
        return schema.Check(name=self.name, description=self.description, check=check_result)


class Section:
    """Section is a group of related checks."""

    name: str
    description: str
    checks: list[Type[AbstractCheck]]

    def __init__(self, *, console: Optional[Console] = None):
        self.console = console or Console()

    @classmethod
    def __init_subclass__(cls):
        if not hasattr(cls, "name"):
            raise AttributeError(f'Class {cls.__name__} must have a "name" attribute')
        if not hasattr(cls, "description"):
            raise AttributeError(f'Class {cls.__name__} must have a "description" attribute')
        cls.checks = []

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f'(name="{self.name}", description="{self.description}", checks={self.checks})'
        )

    def __str__(self):
        return self.name

    def run_all_checks(self) -> Generator[schema.Check, None, None]:
        """Run all checks, entering all reuqired contexts."""
        for check_class in self.checks:
            check = check_class(console=self.console)
            check_result = check.generate_report()
            if check_result is None:
                continue  # Skip check
            yield check_result

    @classmethod
    def register(cls, check_class: Type[AbstractCheck]):
        """Append a check class to list of checks.
        Use as a decorator for check class.
        """
        cls.checks.append(copy(check_class))
        return check_class

    @staticmethod
    def _extract_major_problems(checks: list[schema.Check]) -> list[str]:
        """Get list of unique major problems from a list of checks."""
        return sorted(
            list(
                set(
                    check.check.major_problem
                    for check in checks
                    if check.check.major_problem is not None
                )
            )
        )

    def failed_report(self, major_problem: str) -> schema.Section:
        return schema.Section(
            name=self.name,
            description=self.description,
            result=False,
            checks=[],
            major_problems=[major_problem],
        )

    def skip(self) -> bool:
        return False

    def generate_report(self) -> Optional[schema.Section]:
        """Run all checks from this section and return the result.
        Returns None if there are no checks or all checks were skipped.
        """
        logging.debug(f"Running section: {self}")
        checks = list(self.run_all_checks())
        if not checks:
            _log_result(f"Section {self}", skipped=True)
            return None
        result = all(check.check.result for check in checks)
        major_problems = self._extract_major_problems(checks)
        _log_result(f"Section {self}", status=result)
        return schema.Section(
            name=self.name,
            description=self.description,
            result=result,
            checks=checks,
            major_problems=major_problems,
        )


class Core:
    """Core class, responsible for running all checks and generating the final report."""

    def __init__(
        self,
        sections: list[Type[Section]],
        dependencies: Container,
        *,
        console: Optional[Console] = None,
    ):
        self.sections = sections
        self.dependencies = dependencies
        self.console = console or Console()

    def __repr__(self):
        return f"{self.__class__.__name__}(sections={self.sections})"

    def run_all_sections(self) -> Generator[schema.Section, None, None]:
        for section_class in self.sections:
            try:
                self.dependencies.wire([section_class])
                section = section_class(console=self.console)
                if section.skip():
                    continue  # Skip entire section
                try:
                    with self.console.status(f"Setting up [blue]{section}[/] section..."):
                        self.dependencies.wire(section_class.checks)
                except Exception as ex:
                    logging.debug(ex, exc_info=True)
                    _log_result(f"Section {section}", status=False)
                    yield section.failed_report(
                        f"Failed to provision resources for section {section}"
                    )
                    continue  # Skip section with failed dependencies
                with self.dependencies.reset_singletons():
                    section_result = section.generate_report()
                if section_result is None:
                    continue  # Skip section in which all checks were skipped
                yield section_result
            finally:
                self.dependencies.shutdown_resources()

    @staticmethod
    def _extract_major_problems(sections: list[schema.Section]) -> list[str]:
        return sorted(
            list(set(chain.from_iterable(section.major_problems for section in sections)))
        )

    def generate_report(self) -> schema.Report:
        """Perform all checks in all sections and return the result."""
        sections = list(self.run_all_sections())
        if not sections:
            logging.error("No sections to run")
        result = all(section.result for section in sections)
        major_problems = self._extract_major_problems(sections)
        _log_result("Final result:", status=result)
        return schema.Report(result=result, sections=sections, major_problems=major_problems)
