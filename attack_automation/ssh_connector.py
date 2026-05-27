#!/usr/bin/env python3
"""SSH connector for remote command execution."""

import os
from typing import Optional, Tuple

try:
    import paramiko
except ImportError:  # pragma: no cover
    paramiko = None


class SSHConnectorError(Exception):
    pass


class SSHConnector:
    def __init__(
        self,
        hostname: str,
        ip: str,
        user: str = "",
        port: int = 22,
        key_path: str = "",
        password: Optional[str] = None,
    ):
        self.hostname = hostname
        self.ip = ip
        self.user = user
        self.port = port
        self.key_path = os.path.expanduser(key_path) if key_path else ""
        self.password = password
        self.client = None

    def _ensure_paramiko(self):
        if paramiko is None:
            raise SSHConnectorError(
                "Paramiko is not installed. Install optional requirements: attack_automation/requirements.txt"
            )

    def connect(self, timeout: int = 10) -> None:
        self._ensure_paramiko()
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_args = {
            "hostname": self.ip,
            "port": self.port,
            "username": self.user,
            "timeout": timeout,
        }

        if self.key_path and os.path.isfile(self.key_path):
            connect_args["key_filename"] = self.key_path
        elif self.password:
            connect_args["password"] = self.password

        try:
            self.client.connect(**connect_args)
        except Exception as exc:
            raise SSHConnectorError(f"SSH connection failed: {exc}") from exc

    def run_command(self, command: str, timeout: int = 120) -> Tuple[int, str, str]:
        if self.client is None:
            raise SSHConnectorError("SSH connection is not established")

        stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode(errors="ignore")
        err = stderr.read().decode(errors="ignore")
        return exit_status, out, err

    def close(self) -> None:
        if self.client:
            self.client.close()
            self.client = None
