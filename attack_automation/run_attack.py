#!/usr/bin/env python3
"""Run the full attack automation flow using configured VPN, SSH, and LLM."""

import argparse
import json

from attack_automation.attack_manager import AttackManager, AttackManagerError


def main() -> None:
    parser = argparse.ArgumentParser(description="Run attack automation for a configured target")
    parser.add_argument("--config", default="attack_automation/config.yaml", help="Path to attack automation config")
    parser.add_argument("--llm-auto-enum", action="store_true", help="Ask the LLM to generate additional enumeration commands")
    parser.add_argument("--execute-llm", action="store_true", help="Execute the commands returned by the LLM")
    parser.add_argument("--local-llm", action="store_true", help="Execute LLM-generated commands locally instead of remotely")
    args = parser.parse_args()

    manager = None
    try:
        manager = AttackManager(args.config)
        results = manager.run_full_attack()

        if args.llm_auto_enum:
            results["llm_auto_enum"] = manager.run_llm_enumeration(
                context=results,
                execute=args.execute_llm,
                local=args.local_llm,
            )

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
