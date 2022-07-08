# Writing checks

Checks can be defined in a declarative way by creating new files and classes.
All check classes located in the `cluster_compliance_checker/checks` directory
are automatically detected and used to generate the final report.

## Directory structure

Each `.py` file located in the `checks` directory represents
a single section and can contain any number of check classes.

```text
cluster_compliance_checker/
└── checks
    ├── bar.py
    ├── foo.py
    └── __init__.py
```

## Section module

Section module is a regular python file containing Section and Check classes.
Section class must define both `name` and `description` attributes.
Checks are assigned to a Section with a `register` decorator.

### bar.py

```python
from .. import schema
from ..core import AbstractCheck, Section


class BarSection(Section):
    name = "Section name"
    description = "Section description"


@BarSection.register
class FirstCheck(AbstractCheck):
    ...


@BarSection.register
class SecondCheck(AbstractCheck):
    ...
```

## Check class

Checks should be defined in a form of classes extending `AbstractCheck`.
Each check must contain a `perform_check` method
which returns a `CheckResult` object.
Additionally all checks must define `name` and `description` attributes.

```python
from .. import schema
from ..core import AbstractCheck, Section


class BarSection(Section):
    name = "Section name"
    description = "Section description"


@BarSection.register
class FirstCheck(AbstractCheck):
    name = "Check name"
    description = "Check description"

    def perform_check(self) -> schema.CheckResult:
        return schema.CheckResult(result=False, measured='1337', expected='> 9000')
```

## Check dependencies

We have decided to use an automatic dependency injector for checks.
This allows us to explicitly define
variables and resources required by a particular check,
in order to improve testability and maintainability.

Available dependencies:

- offline
- monthly_traffic
- maintenance_type
- phase
- kubernetes_client
- requirements

```python
from dependency_injector.wiring import Provide
from kubernetes.client.api_client import ApiClient

from .. import schema
from ..core import AbstractCheck, Section
from ..dependencies import Dependencies
from ..enums import MaintenanceType, MonthlyTraffic, Phase
from ..requirements import HardwareRequirements


class BarSection(Section):
    name = "Section name"
    description = "Section description"


@BarSection.register
class DemoCheck(AbstractCheck):
    name = "Demonstration Check"
    description = "Some description"

    # dependencies
    offline: bool = Provide[Dependencies.offline]
    monthly_traffic: MonthlyTraffic = Provide[Dependencies.monthly_traffic]
    maintenance_type: MaintenanceType = Provide[Dependencies.maintenance_type]
    phase: Phase = Provide[Dependencies.phase]
    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]
    requirements: HardwareRequirements = Provide[Dependencies.requirements]

    def perform_check(self) -> schema.CheckResult:
        ...
```

## Skipping checks

Checks can be skipped based on some condition by returning `None` from
the `perform_check` method.

```python
from dependency_injector.wiring import Provide

from typing import Optional

from .. import schema
from ..core import AbstractCheck, Section
from ..dependencies import Dependencies


class BarSection(Section):
    name = "Section name"
    description = "Section description"


@BarSection.register
class SkippableCheck(AbstractCheck):
    name = "Check that will be skipped for offline installations"
    description = ""

    offline: bool = Provide[Dependencies.offline]

    def perform_check(self) -> Optional[schema.CheckResult]:
        if self.offline:
            return
        # Do the check and return result as usual
        return schema.CheckResult(True, "", "")
```

## Skipping entire section

It is possible to skip an entire section.
Main benefit of doing so is that we don't need to wait for
all check dependencies before skip condition is checked.
Example below shows how to skip a section during pre-contract phase.

```python
from ..core import AbstractCheck, Section
from ..dependencies import Dependencies
from ..enums import Phase


class BarSection(Section):
    name = "Section name"
    description = "Section description"
    phase: Phase = Provide[Dependencies.phase]

    def skip(self) -> bool:
        return self.phase is Phase.PRE_CONTRACT


@BarSection.register
class SomeCheck(AbstractCheck):
    ...
```

## Spawning kubernetes resources

It is possible to spawn kubernetes resources during checks
through a helper `Spawner` class.
This class contains context managers
that will take care of creating resources
and deleting them once they are not needed anymore.
We have also written some functions to simplify
the manifest creation process.
You can find them in the `cluster_compliance_checker/manifests.py` file.

> **Note**
> Using dependencies is preferred over spawning resources during check

### StatefulSet

```python
from contextlib import ExitStack

from dependency_injector.wiring import Provide
from kubernetes import client
from kubernetes.client.api_client import ApiClient

from .. import manifests, schema
from ..core import AbstractCheck, Section
from ..dependencies import Dependencies
from ..spawner import Spawner


class BarSection(Section):
    name = "Section name"
    description = "Section description"


@BarSection.register
class TestCheck(AbstractCheck):
    name = "check name"
    description = "check description"

    spawner: Spawner = Provide[Dependencies.spawner]

    def perform_check(self) -> schema.CheckResult:
        name = "check"  # name used for kubernetes resources

        stateful_set_manifest = manifests.mk_stateful_set(name, "nginx:latest")
        with self.spawner.stateful_set(stateful_set_manifest) as stateful_set:
            # Do something with the stateful set
```

### StatefulSet with Service and PVC

You can spawn many resources at once
but you need to use `ExitStack` to handle this.
Below example spawns a `Service` followed by
a `StatefulSet` with a predefined `PVC`.
`ExitStack` takes care of destroying all these resources
after the check is done.

```python
from dependency_injector.wiring import Provide
from contextlib import ExitStack

from kubernetes import client
from kubernetes.client.api_client import ApiClient

from .. import manifests, schema
from ..core import AbstractCheck, Section
from ..dependencies import Dependencies
from ..spawner import Spawner


class BarSection(Section):
    name = "Section name"
    description = "Section description"


@BarSection.register
class TestCheck(AbstractCheck):
    name = "check name"
    description = "check description"

    kubernetes_client: ApiClient = Provide[Dependencies.kubernetes_client]

    def perform_check(self) -> schema.CheckResult:
        name = "check"  # name used for kubernetes resources

        service_manifest = manifests.mk_service(name)
        pvc_manifest = manifests.mk_pvc(name="mnt", size="512Mi")
        stateful_set_manifest = manifests.mk_stateful_set(
            name,
            "nginx:latest",
            service=service_manifest,
            mounts={"/mnt": pvc_manifest},  # Mount PVC at /mnt
        )
        spawner = Spawner(self.kubernetes_client)

        with ExitStack() as stack:
            stack.enter_context(spawner.service(service_manifest))
            stateful_set = stack.enter_context(spawner.stateful_set(stateful_set_manifest))
            # Do something with the stateful set
```

## Major problems

Sometimes a check can come across a major problem, that prevents it's execution
(e.g. you cannot check PVC performance if spawning PVC fails).
In such case, you can return such a problem from the `perform_check` method
and it will appear in a visible place in the final report.

```python
from typing import Optional

from .. import schema
from ..core import AbstractCheck, Section


class BarSection(Section):
    name = "Section name"
    description = "Section description"


@BarSection.register
class CheckWithMajorError(AbstractCheck):
    name = "Check with major problem"
    description = ""

    def perform_check(self) -> Optional[schema.CheckResult]:
        try:
            # Do some pre check action
        except SomeMajorError:
            return self.major_problem("A descriptive error message")
        # Do the check and return result as usual
        return schema.CheckResult(True, "", "")
```
