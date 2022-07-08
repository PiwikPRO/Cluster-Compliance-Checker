from cluster_compliance_checker import schema
from cluster_compliance_checker.core import AbstractCheck, Section


class FooSection(Section):
    name = "Foo"
    description = "Foo is example section for foo checks"


@FooSection.register
class MaxOpenedFoobars(AbstractCheck):
    name = "sys.max_opened_foobars"
    description = "Lorem ipsum dolor sit amet"

    def perform_check(self) -> schema.CheckResult:
        return schema.CheckResult(result=True, measured="1337", expected="> 1000")


@FooSection.register
class MinFoobarValue(AbstractCheck):
    name = "sys.min_foobar_value"
    description = "Consectetur adipiscing elit"

    def perform_check(self) -> schema.CheckResult:
        return schema.CheckResult(result=True, measured="13370", expected="< 20000")


@FooSection.register
class SkippedCheck(AbstractCheck):
    name = "Skipped check"
    description = "This check should not appear in the final report"

    def perform_check(self):
        return
