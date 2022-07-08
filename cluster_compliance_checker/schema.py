from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CheckResult:
    """Values related to a particular check."""

    result: bool
    measured: str
    expected: str
    major_problem: Optional[str] = None


@dataclass
class Check:
    """Single measurement of some value."""

    name: str
    description: str
    check: CheckResult


@dataclass
class Section:
    """Group of related checks."""

    name: str
    description: str
    result: bool
    checks: list[Check]
    major_problems: list[str] = field(default_factory=list)


@dataclass
class Report:
    """Top-level class containing the entire result report."""

    result: bool
    sections: list[Section]
    major_problems: list[str] = field(default_factory=list)
