from dependency_injector.wiring import Provide

from cluster_compliance_checker import schema
from cluster_compliance_checker.core import AbstractCheck, Section


class BarSection(Section):
    name = "Bar"
    description = "Bar is example section for bar type checks"


@BarSection.register
class FoobarCheck1(AbstractCheck):
    name = "Foobar version"
    description = "Sed do eiusmod tempor incididunt ut labore"

    def perform_check(self) -> schema.CheckResult:
        return schema.CheckResult(result=False, measured="1337", expected="> 9000")


@BarSection.register
class FoobarCheck2(AbstractCheck):
    name = "Foobar admin privileges"
    description = "Ut enim ad minim veniam"

    test_dependency: str = Provide["test_dependency"]

    def perform_check(self) -> schema.CheckResult:
        assert self.test_dependency == "test value"
        return schema.CheckResult(result=True, measured="true", expected="true")
