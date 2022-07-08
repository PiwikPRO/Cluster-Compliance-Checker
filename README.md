# Piwik PRO Cluster Compliance Checker

## Introduction

This tool's purpose is to confirm that given Kubernetes cluster
(prepared either by client or by us) is capable of running Piwik PRO Analytics Suite.
Also, it can be used for ensuring said compliance just before installation process.
It runs a series of checks divided in several sections on Kubernetes cluster,
and after it finishes, it presents a report in HTML format.

Cluster Compliance Checker is meant to run on an empty Kubernetes cluster.
It requires admin access for its operation
in order to spawn arbitrary resources in the default namespace.
The checker runs no priprietary code on your Kubernetes cluster,
all the logic it executes is part of this repository, so you can freely inspect it.
In short, checks performed by Checker include (but are not limited to):

- Cluster information (Kubernetes version, Calico, details about nodes)

- Linux kernel parameters (read using `sysctl`)

- Access to external services (container registry, PagerDuty)

- Disk and PVC performance
  ([fio](https://fio.readthedocs.io/en/latest/fio_doc.html) benchmarks)

## Run using docker

There are several ways of running Cluster Compliance Checker.
The simplest method is to run it in _docker_ on the operators machine.
Make sure you have a valid _kubeconfig_ with proper read permissions
so the container can actually read it.

```bash
# Run docker with kubeconfig mounted as volume
docker run -v /path/to/kube/config:/piwikpro/.kube/config \
    -p 8080:8080 -it ghcr.io/piwikpro/cluster-compliance-checker:latest

# You can also pass arguments
docker run -it ghcr.io/piwikpro/cluster-compliance-checker:latest --help
```

Once all checks are done, report will be served on the port 8080.
Open `http://localhost:8080` in the browser to view it.

## Technology stack

### Poetry

We use [poetry](https://python-poetry.org) to develop this project.
Poetry automates the process of creating venv,
installing dependencies and building the packages.

### Jinja2

[Jinja2](https://jinja.palletsprojects.com) is frontend basis of this application.
Jinja yields final report by rendering its template, fed by JSON report.

### Bootstrap

We use [bootstrap](https://getbootstrap.com/docs/5.1/getting-started/download/)
and [bootstrap icons](https://github.com/twbs/icons/releases/) for _html_ styling.


## Contributing

Please review [dedicated document](CONTRIBUTING.md).
