# Contributing

## Development

In order to work on this project, you will need _python 3.9_, _poetry_,
_npm_ and _docker_ installed on your system.

### Initial setup

You can setup your worspace by cloning the repository
and installing all dependencies with _poetry_ and _npm_.

```bash
git clone https://github.com/PiwikPRO/Cluster-Compliance-Checker.git
cd Cluster-Compliance-Checker

# If you have multiple python versions installed,
# it may be necessary to point poetry to a proper one
poetry env use python3.9

# Install dependencies to venv in dev mode
poetry install

# Install bootstrap
npm install
```

### Running locally

You can use `poetry run` to launch the application locally.
This command will run checks and start a http server with results report
on the port _8080_.

```bash
poetry run cluster-compliance-checker
# Run help to learn about supported options
poetry run cluster-compliance-checker --help
# You can also use a short executable name
poetry run pp3c
```

### Building docker images

There are 2 dockerfiles present in the repo.
_Dockerfile_ in the root directory of the project is a main application
and the one in the _tools_ directory describes a complementary image
that can be spawned in the cluster during checks.

```bash
docker build -t image_name:image_tag .
docker build -t tools_image_name:image_tag tools
```

### Editing the code

Make sure your IDE/Code Editor uses _venv_ created by _poetry_ for LSP.
You can find a proper path to the _venv_ by running `poetry env info`.

```text
$ poetry env info

Virtualenv
Python:         3.9.13
Implementation: CPython
Path:           /home/username/.cache/pypoetry/virtualenvs/cluster-compliance-checker-wf0Cbvge-py3.9
Valid:          True

System
Platform: linux
OS:       posix
Python:   /usr
```

#### pyrightconfig.json

```json
{
  "venvPath": "/home/username/.cache/pypoetry/virtualenvs",
  "venv": "cluster-compliance-checker-wf0Cbvge-py3.9"
}
```

### Tests

Pytest is our test framework of choice.
All tests are located in the `test` directory.

```bash
poetry run pytest
```

### Linting

Linting checks are performed using pylama,
which aggregates several linting plugins.

```bash
poetry run pylama
```

### Autoformatter

We use `black` and `isort` to format the code,
it is also used to check compliance in CI pipeline.

```bash
poetry run black .
poetry run isort .
```
