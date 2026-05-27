#!/usr/bin/env python3
"""Workflow definitions for attack automation."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class WorkflowStep:
    name: str
    description: str
    command: str
    required: bool = True


@dataclass
class Workflow:
    name: str
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)

    def add_step(self, step: WorkflowStep) -> None:
        self.steps.append(step)

    def summarize(self) -> str:
        lines = [f"Workflow: {self.name}", f"Description: {self.description}", "Steps:"]
        for step in self.steps:
            lines.append(f" - {step.name}: {step.description} ({step.command})")
        return "\n".join(lines)


class ReconWorkflow(Workflow):
    def __init__(self):
        super().__init__(
            name="recon",
            description="Collect service, user, and environment information",
        )
        self.steps = [
            WorkflowStep("enumerate_services", "List open ports and services", "nmap -sV -p- {target}"),
            WorkflowStep("list_users", "List local users", "cat /etc/passwd"),
            WorkflowStep("env_info", "Collect environment variables", "env"),
        ]


class NetworkReconWorkflow(Workflow):
    def __init__(self):
        super().__init__(
            name="network_recon",
            description="Run VPN-connected network reconnaissance tasks from the local host",
        )
        self.steps = [
            WorkflowStep("ping_target", "Verify target reachability", "ping -c 2 {target}"),
            WorkflowStep("tcp_scan", "Scan open TCP ports and services", "nmap -sV -p- {target}"),
            WorkflowStep("http_probe", "Probe HTTP service if available", "curl -IkL --max-time 15 http://{target}"),
            WorkflowStep("https_probe", "Probe HTTPS service if available", "curl -IkL --max-time 15 https://{target}"),
        ]


class InitialAccessWorkflow(Workflow):
    def __init__(self):
        super().__init__(
            name="initial_access",
            description="Attempt an initial foothold with non-destructive checks",
        )
        self.steps = [
            WorkflowStep("whoami", "Confirm current remote user", "whoami"),
            WorkflowStep("id", "Inspect user identity and groups", "id"),
            WorkflowStep("uname", "Collect kernel and system information", "uname -a"),
            WorkflowStep("processes", "List top running processes", "ps aux --sort=-%mem | head -n 20"),
        ]


class PrivilegeEscalationWorkflow(Workflow):
    def __init__(self):
        super().__init__(
            name="privilege_escalation",
            description="Identify local privilege escalation vectors",
        )
        self.steps = [
            WorkflowStep("sudo_checks", "List sudo privileges", "sudo -l"),
            WorkflowStep("kernel_info", "Inspect kernel and distro info", "uname -a && cat /etc/os-release"),
        ]
