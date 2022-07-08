from typing import Optional

from kubernetes import client


def mk_service(name: str, ports: Optional[list[client.V1ServicePort]] = None) -> client.V1Service:
    return client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(
            name=name,
        ),
        spec=client.V1ServiceSpec(
            selector={"app": name},
            cluster_ip="None",
            type="ClusterIP",
            ports=ports,
        ),
    )


def mk_pvc(
    name: str, size: str = "100Mi", storage_class_name: Optional[str] = None
) -> client.V1PersistentVolumeClaim:
    return client.V1PersistentVolumeClaim(
        metadata=client.V1ObjectMeta(
            name=name,
        ),
        spec=client.V1PersistentVolumeClaimSpec(
            storage_class_name=storage_class_name,
            access_modes=["ReadWriteOnce"],
            resources=client.V1ResourceRequirements(
                requests={"storage": size},
            ),
        ),
    )


def mk_stateful_set(
    name: str,
    image: str,
    replicas: int = 1,
    namespace: str = "default",
    service: Optional[client.V1Service] = None,
    mounts: Optional[dict[str, client.V1PersistentVolumeClaim]] = None,
    pull_secrets: Optional[list[client.V1LocalObjectReference]] = None,
) -> client.V1StatefulSet:
    """Create a StatefulSet manifest object.
    Optionally supports PersistentVolumeClaim and Service."""
    mounts = mounts or {}
    pull_secrets = pull_secrets or []
    volume_mounts = [
        client.V1VolumeMount(name=vol.metadata.name, mount_path=path)  # type: ignore
        for path, vol in mounts.items()
    ]
    try:  # service, metadata and name are all optional
        service_name = service.metadata.name or ""  # type: ignore
    except AttributeError:
        service_name = ""

    return client.V1StatefulSet(
        api_version="apps/v1",
        kind="StatefulSet",
        metadata=client.V1ObjectMeta(
            name=name,
            namespace=namespace,
            labels={
                "app": name,
            },
        ),
        spec=client.V1StatefulSetSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(
                match_labels={
                    "app": name,
                },
            ),
            service_name=service_name,
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    name=name,
                    labels={
                        "app": name,
                    },
                ),
                spec=client.V1PodSpec(
                    security_context=client.V1PodSecurityContext(fs_group=1000),
                    affinity=client.V1Affinity(
                        pod_anti_affinity=client.V1PodAntiAffinity(
                            required_during_scheduling_ignored_during_execution=[
                                client.V1PodAffinityTerm(
                                    topology_key="kubernetes.io/hostname",
                                    label_selector=client.V1LabelSelector(
                                        match_expressions=[
                                            client.V1LabelSelectorRequirement(
                                                key="app", operator="In", values=[name]
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    ),
                    containers=[
                        client.V1Container(
                            name=name,
                            image=image,
                            image_pull_policy="IfNotPresent",
                            command=["tail", "-f", "/dev/null"],
                            resources=client.V1ResourceRequirements(
                                limits={"memory": "512Mi", "cpu": "100m"},
                                requests={"memory": "512Mi", "cpu": "100m"},
                            ),
                            volume_mounts=volume_mounts,
                        ),
                    ],
                    image_pull_secrets=pull_secrets,
                ),
            ),
            volume_claim_templates=list(mounts.values()),
        ),
    )
