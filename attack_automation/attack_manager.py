#!/usr/bin/env python3
"""Attack automation manager orchestrating VPN, SSH, and LLM workflows."""

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .llm_client import LLMClient, LLMClientError
from .ssh_connector import SSHConnector, SSHConnectorError
from .vpn_connector import VPNConnector, VPNConnectorError
from .agent.workflow import NetworkReconWorkflow, ReconWorkflow, InitialAccessWorkflow, PrivilegeEscalationWorkflow


class AttackManagerError(Exception):
    pass


class AttackManager:
    def __init__(self, config_path: str = "attack_automation/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.vpn = self._build_vpn_connector()
        self.llm = self._build_llm_client()
        self.ssh = self._build_ssh_connector()

    def _load_config(self) -> Dict[str, Any]:
        path = Path(self.config_path)
        if not path.is_file():
            raise AttackManagerError(f"Config not found: {self.config_path}")

        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _build_vpn_connector(self) -> Optional[VPNConnector]:
        vpn_cfg = self.config.get("vpn", {})
        if not vpn_cfg:
            return None

        return VPNConnector(
            command=vpn_cfg.get("command"),
            config_path=vpn_cfg.get("config_path"),
        )

    def _build_llm_client(self) -> Optional[LLMClient]:
        llm_cfg = self.config.get("llm", {})
        if not llm_cfg:
            return None

        api_key = llm_cfg.get("api_key") or os.environ.get("OPENAI_API_KEY")
        try:
            return LLMClient(
                provider=llm_cfg.get("provider", "openai"),
                model=llm_cfg.get("model", "gpt-4o"),
                api_key=api_key,
            )
        except LLMClientError as exc:
            raise AttackManagerError(f"LLM client error: {exc}") from exc

    def _build_ssh_connector(self) -> SSHConnector:
        host = self.config.get("host", {})
        if not host:
            raise AttackManagerError("Host configuration is required")

        return SSHConnector(
            hostname=host.get("hostname", ""),
            ip=host.get("ip", ""),
            user=host.get("ssh_user", ""),
            port=host.get("ssh_port", 22),
            key_path=host.get("ssh_key", ""),
            password=host.get("ssh_password"),
        )

    def _run_local_command(self, command: str, timeout: int = 120) -> str:
        try:
            completed = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
            )
            return completed.stdout
        except subprocess.TimeoutExpired:
            return f"Command timed out: {command}"

    def connect_vpn(self) -> None:
        if self.vpn is None:
            return
        try:
            self.vpn.connect()
        except VPNConnectorError as exc:
            raise AttackManagerError(f"VPN connection failed: {exc}") from exc

    def connect_ssh(self) -> None:
        try:
            self.ssh.connect()
        except SSHConnectorError as exc:
            raise AttackManagerError(f"SSH connection failed: {exc}") from exc

    def close(self) -> None:
        if self.ssh:
            self.ssh.close()
        if self.vpn:
            self.vpn.disconnect()

    def run_network_recon(self) -> Dict[str, str]:
        results = {}
        recon = NetworkReconWorkflow()
        target = self.config.get("host", {}).get("ip", "")
        for step in recon.steps:
            command = step.command.format(target=target)
            output = self._run_local_command(command)
            results[step.name] = output
        return results

    def run_recon(self) -> Dict[str, str]:
        results = {}
        recon = ReconWorkflow()
        for step in recon.steps:
            command = step.command.format(target=self.ssh.ip, user=self.ssh.user, port=self.ssh.port, key=self.ssh.key_path)
            code, out, err = self.ssh.run_command(command)
            results[step.name] = out if code == 0 else err
        return results

    def run_initial_access(self) -> Dict[str, str]:
        results = {}
        access = InitialAccessWorkflow()
        for step in access.steps:
            command = step.command.format(target=self.ssh.ip, user=self.ssh.user, port=self.ssh.port, key=self.ssh.key_path)
            code, out, err = self.ssh.run_command(command)
            results[step.name] = out if code == 0 else err
        return results

    def run_privilege_escalation(self) -> Dict[str, str]:
        results = {}
        escal = PrivilegeEscalationWorkflow()
        for step in escal.steps:
            code, out, err = self.ssh.run_command(step.command)
            results[step.name] = out if code == 0 else err
        return results

    def ask_llm(self, prompt: str) -> str:
        if self.llm is None:
            raise AttackManagerError("LLM client is not configured")
        return self.llm.generate(prompt, max_tokens=self.config.get("llm", {}).get("max_tokens", 1000))

    def run_full_attack(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}

        if self.vpn is not None:
            results["vpn"] = "connecting"
            self.connect_vpn()
            results["vpn"] = "connected"

        results["network_recon"] = self.run_network_recon()

        self.connect_ssh()
        results["ssh"] = "connected"

        results["remote_recon"] = self.run_recon()
        results["initial_access"] = self.run_initial_access()
        results["privilege_escalation"] = self.run_privilege_escalation()

        if self.llm is not None:
            prompt = (
                "Based on the following results from network and host reconnaissance, suggest the next safe initial foothold and privilege escalation tasks.\n\n"
                f"{results}\n"
            )
            results["llm_plan"] = self.ask_llm(prompt)

        return results

    def fetch_attack_plan(self) -> str:
        if self.llm is None:
            raise AttackManagerError("LLM client is not configured")

        prompt = "Prepare a safe, structured set of reconnaissance and privilege escalation commands for a Linux host based on the following configuration:\n"
        prompt += f"{self.config}\n"
        return self.ask_llm(prompt)
