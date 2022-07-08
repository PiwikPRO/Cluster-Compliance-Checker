"""Functions from this module can be used to find checks and sections.
"""
import inspect
import logging
from collections import defaultdict
from copy import copy
from importlib import import_module
from pkgutil import iter_modules
from types import ModuleType
from typing import DefaultDict, Generator, Iterable, Mapping, Optional, Type

from .core import Section


def find_section_class(module: ModuleType):
    """Find Section class in a given module.
    Valid section must be a subclass of `core.Section`.
    """
    for _, member in inspect.getmembers(module):
        if inspect.isclass(member) and issubclass(member, Section) and member is not Section:
            return member
    raise ValueError(f"No Section class found in {module} module")


def iter_sections(
    checks_module: ModuleType,
    checks_to_find: Mapping[str, list[str]],
) -> Generator[Type[Section], None, None]:
    """Iterate over section contained in the module.
    Section is skipped if `checks_to_find` is not empty and given module is not present as a key.
    """
    for _, modname, ispkg in iter_modules(checks_module.__path__):
        if ispkg or (checks_to_find and checks_to_find.get(modname) is None):
            continue
        module = import_module(f"{checks_module.__package__}.{modname}")
        section_class = copy(find_section_class(module))
        if checks_to_find and checks_to_find[modname]:
            filtered_checks = filter(
                lambda check: check.__name__ in checks_to_find[modname], section_class.checks
            )
            section_class.checks = list(filtered_checks)
        logging.debug(f"Discovered section: {section_class.name}")
        yield section_class


def process_checks_to_find(checks_to_find: Optional[Iterable[str]]) -> Mapping[str, list[str]]:
    """Convert list of checks to find passed from commandline
    into a dictionary that is easier to work with.

    Example:
        Input: ['section.check', section.check2, section2.check3]
        Output: {'section': ['check', 'check2'], 'section2': ['check3']}.
    """
    if checks_to_find is None:
        return {}
    result: DefaultDict[str, list[str]] = defaultdict(list)
    for section_check in checks_to_find:
        split_value = section_check.split(".")
        # Just section
        if len(split_value) == 1 and split_value[0]:
            result[section_check]
        # Section and check
        elif len(split_value) == 2 and all(split_value):
            section, check = split_value
            result[section].append(check)
        else:
            raise ValueError(f'Check "{section_check}" is invalid')
    return dict(result)


def discover_sections(
    module: ModuleType,
    checks_to_find: Optional[Iterable[str]] = None,
) -> list[Type[Section]]:
    """Search a module in order to find all sections and checks."""
    logging.debug("Discovering sections and checks...")
    return list(iter_sections(module, process_checks_to_find(checks_to_find)))
