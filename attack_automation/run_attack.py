#!/usr/bin/env python3
"""Run the full attack automation flow using configured VPN, SSH, and LLM."""

import argparse
import json

from attack_automation.attack_manager import AttackManager, AttackManagerError


def main() -> None:
    parser = argparse.ArgumentParser(description="Run attack automation for a configured target")
    parser.add_argument("--config", default="attack_automation/config.yaml", help="Path to attack automation config")
    args = parser.parse_args()

    manager = None
    try:
        manager = AttackManager(args.config)
        results = manager.run_full_attack()
        print(json.dumps(results, indent=2))
    except AttackManagerError as exc:
        print(f"[ERROR] {exc}")
    finally:
        if manager is not None:
            try:
                manager.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
