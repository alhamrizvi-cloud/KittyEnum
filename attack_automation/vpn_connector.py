#!/usr/bin/env python3
"""VPN connector helper for shell-based VPN clients."""

import subprocess
from typing import List, Optional


class VPNConnectorError(Exception):
    pass


class VPNConnector:
    def __init__(self, command: Optional[List[str]] = None, config_path: Optional[str] = None):
        self.command = command
        self.config_path = config_path
        self.process = None

    def connect(self) -> None:
        if self.command:
            cmd = self.command
        elif self.config_path:
            cmd = ["openvpn", "--config", self.config_path]
        else:
            raise VPNConnectorError("No VPN command or config path provided")

        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except Exception as exc:
            raise VPNConnectorError(f"Failed to start VPN connection: {exc}") from exc

    def disconnect(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process = None
