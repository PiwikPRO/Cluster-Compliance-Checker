# Cluster Compliance Checker

## Introduction

This chart deploys:

- [Piwik PRO Checker](https://github.com/PiwikPRO/Cluster-Compliance-Checker)
  with dependencies for checking cluster's compliance with kubernetes cluster.

## Deployment

### Pre-contract phase

Pre-contract phase is the default mode of Cluster Compliance Checker.

```bash
CHART=https://github.com/PiwikPRO/cluster-compliance-checker/releases/download/1.1.0/cluster-compliance-checker-1.1.0.tgz
helm install cluster-compliance-checker $CHART
```

### Pre-install phase

During pre-install phase it is necessary to have access to
PiwikPRO container registry.

```bash
helm install cluster-compliance-checker $CHART \
    --set env.PP_PHASE=pre-install \
    --set env.PP_REGISTRY_USERNAME=$ACR_USER \
    --set env.PP_REGISTRY_PASSWORD=$ACR_PASS
```

### Arguments

You can reconfigure Checker's behaviour by properly adjusting
[those](#env) variables, e.g.:

```bash
helm install cluster-compliance-checker $CHART \
    --set env.PP_OFFLINE=true \
    --set env.PP_MONTHLY_TRAFFIC=500 \
    --set env.PP_LOG_LEVEL=debug
```

## Usage

After deployment, Checker will perform all necessary checks needed to ensure
that provided kubernetes cluster is capable of running Piwik PRO Analyics Suite.
After all checks are finished, you can see generated report served by
Checker by forwarding port (by default - `8080`) to your local computer.

## Configuration

The following table lists the configurable parameters
of the chart and their default values.

### affinity

| Parameter | Description                 | Default |
| --------- | --------------------------- | ------- |
| affinity  | Affinity for pod assignment | None    |

### deployRBAC

| Parameter  | Description                                                                                         | Default |
| ---------- | --------------------------------------------------------------------------------------------------- | ------- |
| deployRBAC | It will deploy `ServiceAccount`, `ClusterRole` and `ClusterRoleBinding` with full access to cluster | `True`  |

### docker

| Parameter         | Description                                  | Default                             |
| ----------------- | -------------------------------------------- | ----------------------------------- |
| docker.registry   | Checker image registry                       | ghcr.io                             |
| docker.image      | Checker image repository                     | piwikpro/cluster-compliance-checker |
| docker.tag        | Checker image tag                            | The same as Chart version           |
| docker.pullPolicy | Checker image pull policy                    | IfNotPresent                        |
| docker.pullSecret | Specify external docker-registry secret name | None                                |

### env

| Parameter                  | Description                                                                            | Default                                           |
| -------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------- |
| env.PP_MONTHLY_TRAFFIC     | Expected monthly traffic in Millions of Acctions                                       | 10                                                |
| env.PP_MAINTENANCE_TYPE    | Maintenance type (either `remote-access` or `self-support`)                            | remote-access                                     |
| env.PP_OFFLINE             | Whether installation will be offline or not                                            | false                                             |
| env.PP_PHASE               | Phase (`pre-contract`, `pre-install`)                                                  | `pre-contract`                                    |
| env.PP_LOG_LEVEL           | Log level (possible values: `debug`, `info`, `warn` and `error`)                       | info                                              |
| env.PP_KUBE_LOG_LEVEL      | Log level for kubernetes client (possible values: `debug`, `info`, `warn` and `error`) | info                                              |
| env.PP_NAMESPACE_WHITELIST | Additional namespaces allowed to live in the cluster                                   | None                                              |
| env.PP_STORAGE_CLASS       | Storage class used for PVC                                                             | None                                              |
| env.PP_PORT                | Port used to serve the report                                                          | 8080                                              |
| env.PP_REGISTRY_URL        | PiwikPRO registry url                                                                  | piwikpro.azurecr.io                               |
| env.PP_REGISTRY_USERNAME   | PiwikPRO registry username                                                             | None                                              |
| env.PP_REGISTRY_PASSWORD   | PiwikPRO registry password                                                             | None                                              |
| env.PP_TOOLS_IMAGE         | Tools image repository name                                                            | ghcr.io/piwikpro/cluster-compliance-checker-tools |
| env.PP_TOOLS_IMAGE_TAG     | Tools image tag                                                                        | The same as Checker version                       |

### name

| Parameter | Description   | Default                    |
| --------- | ------------- | -------------------------- |
| name      | Name of chart | cluster-compliance-checker |

### namespaceOverride

| Parameter         | Description                              | Default |
| ----------------- | ---------------------------------------- | ------- |
| namespaceOverride | Override namespace for Checker resources | None    |

### resources

| Parameter                 | Description                                               | Default |
| ------------------------- | --------------------------------------------------------- | ------- |
| resources.limits.cpu      | The resources limit for cpu for the Checker containers    | 1000m   |
| resources.limits.memory   | The resources limit for memory for the Checker containers | 512Mi   |
| resources.requests.cpu    | The requested cpu for the Checker containers              | 10m     |
| resources.requests.memory | The requested memory for the Checker containers           | 32Mi    |

### security

| Parameter                         | Description                                                 | Default |
| --------------------------------- | ----------------------------------------------------------- | ------- |
| security.allowPrivilegeEscalation | Set Checker pod's Security Context allowPrivilegeEscalation | False   |
| security.fsGroup                  | Set Checker pod's Security Context fsGroup                  | 1000    |
| security.runAsGroup               | Set Checker containers' Security Context runAsGroup         | 1000    |
| security.runAsUser                | Set Checker containers' Security Context runAsUser          | 1000    |

### reportStorageDir

| Parameter        | Description                            | Default       |
| ---------------- | -------------------------------------- | ------------- |
| reportStorageDir | Override where Checker puts its report | `/app/report` |
