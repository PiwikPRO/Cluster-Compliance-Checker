import logging
import socketserver
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback_handler

from . import checks
from .core import Core
from .dependencies import Dependencies
from .discovery import discover_sections
from .enums import LogLevel, MaintenanceType, MonthlyTraffic, Phase
from .report_request_handler import ReportRequestHandler
from .requirements import hardware_configurations
from .template import template


def install_rich_handlers(
    level: str, kubernetes_log_level: str, show_locals: bool, console: Console
):
    install_rich_traceback_handler(show_locals=show_locals, console=console)
    logging.basicConfig(
        level=logging._nameToLevel[level.upper()],
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(rich_tracebacks=True, tracebacks_show_locals=show_locals, console=console)
        ],
    )
    logging.getLogger("kubernetes").setLevel(logging._nameToLevel[kubernetes_log_level.upper()])


def main(
    monthly_traffic: MonthlyTraffic = typer.Option(
        MonthlyTraffic._10M.value,
        envvar="PP_MONTHLY_TRAFFIC",
        help="Expected monthly traffic in Millions of Actions",
    ),
    maintenance_type: MaintenanceType = typer.Option(
        MaintenanceType.REMOTE_ACCESS.value,
        envvar="PP_MAINTENANCE_TYPE",
        help="Maintenance model",
    ),
    offline: bool = typer.Option(
        False,
        "--offline/--online",
        envvar="PP_OFFLINE",
        help="Offline installation",
    ),
    phase: Phase = typer.Option(
        Phase.PRE_CONTRACT.value,
        envvar="PP_PHASE",
        help="Choose a phase at which the program is executed",
    ),
    checks_to_run: list[str] = typer.Option(
        [],
        "--check",
        help=(
            'Specify check "section_file_name.check_class_name" '
            'or section "section_file_name" to run. '
            "Can be used multiple times to specify multiple checks or sections."
        ),
    ),
    registry_server: str = typer.Option(
        "piwikpro.azurecr.io",
        envvar="PP_REGISTRY_URL",
        help="Image registry url",
    ),
    registry_username: Optional[str] = typer.Option(
        None,
        envvar="PP_REGISTRY_USERNAME",
        help="Image registry username",
    ),
    registry_password: Optional[str] = typer.Option(
        None,
        envvar="PP_REGISTRY_PASSWORD",
        help="Image registry password",
    ),
    tools_image: str = typer.Option(
        "ghcr.io/piwikpro/cluster-compliance-checker-tools",
        envvar="PP_TOOLS_IMAGE",
        help="Use specific image of cluster-compliance-checker-tools",
    ),
    tools_image_tag: str = typer.Option(
        version(__package__),
        envvar="PP_TOOLS_IMAGE_TAG",
        help="Use specific version of cluster-compliance-checker-tools image",
    ),
    storage_class: str = typer.Option(
        "",
        envvar="PP_STORAGE_CLASS",
        help="Storage class used spawn volumes",
    ),
    namespace_whitelist: list[str] = typer.Option(
        [],
        envvar="PP_NAMESPACE_WHITELIST",
        help=(
            "Additional allowed namespaces that may live in the cluster. "
            "Can be used multiple times. "
            "EV accepts a space separated list of values."
        ),
    ),
    port: int = typer.Option(
        8080,
        envvar="PP_PORT",
        help="Port to expose webserver on",
    ),
    serve: bool = typer.Option(
        True,
        help="Start a http server and host the results",
    ),
    log_level: LogLevel = typer.Option(
        LogLevel.INFO.value,
        envvar="PP_LOG_LEVEL",
        help="Log level threshold",
    ),
    kubernetes_log_level: LogLevel = typer.Option(
        LogLevel.WARN.value,
        envvar="PP_KUBE_LOG_LEVEL",
        help="Log level threshold for the Kubernetes library",
    ),
    show_locals: bool = typer.Option(
        False,
        help="Show local variables in error tracebacks",
    ),
):
    console = Console(record=True)
    install_rich_handlers(log_level, kubernetes_log_level, show_locals, console)
    dependencies = Dependencies(
        offline=offline,
        monthly_traffic=monthly_traffic,
        maintenance_type=maintenance_type,
        phase=phase,
        requirements=hardware_configurations[monthly_traffic],
        registry_server=str(registry_server),
        registry_username=str(registry_username),
        registry_password=str(registry_password),
        tools_image=f"{tools_image}:{tools_image_tag}",
        storage_class=storage_class,
        namespace_whitelist=list(namespace_whitelist),
    )

    html = "Sorry, something went wrong. Visit /logs to see details."
    try:
        sections = discover_sections(checks, list(checks_to_run))
        core = Core(sections=sections, console=console, dependencies=dependencies)
        report = core.generate_report()
        html = template(data=asdict(report))
    except Exception:
        console.print_exception(show_locals=show_locals)
        raise
    finally:
        logs = console.export_html()
        report_path = Path("report/report.html")
        logs_path = report_path.parent / "logs.html"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w") as file:
            file.write(html)
        with logs_path.open("w") as file:
            file.write(logs)

        if serve:
            logging.info(
                "If you run Piwik PRO Cluster Compliance Checker in kubernetes, "
                "you need to use port forwarding in order to access the results page."
            )
            with (
                socketserver.TCPServer(("", port), ReportRequestHandler) as httpd,
                console.status(f"Running http server on port [blue]{port}[/]..."),
            ):
                httpd.serve_forever()


def entrypoint():
    typer.run(main)


if __name__ == "__main__":
    entrypoint()
