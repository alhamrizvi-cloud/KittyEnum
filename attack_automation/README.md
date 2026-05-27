# Attack Automation Scaffold

This folder contains the next-stage attack automation components for KittyEnum.
It is a structured starting point for connecting to a VPN, SSH host, and an LLM provider so you can orchestrate recon and privilege escalation workflows.

> Important: This code is a scaffold. It does not automatically attack targets by itself. Use only on systems you are authorized to test.

## What’s included

- `attack_manager.py` — orchestrates VPN, SSH, and LLM workflows
- `vpn_connector.py` — shell-based VPN process helper
- `ssh_connector.py` — remote SSH command execution using Paramiko
- `llm_client.py` — OpenAI-compatible LLM wrapper
- `config.yaml` — sample host, VPN, and model configuration
- `requirements.txt` — optional dependencies for attack automation

## Install optional dependencies

```bash
python3 -m pip install -r attack_automation/requirements.txt
```

## Configure the target and provider

Edit `attack_automation/config.yaml` with your host and provider details.

- `vpn.config_path`: path to an OpenVPN config file
- `vpn.command`: optional custom VPN command list
- `llm.api_key`: OpenAI API key or leave null to use `OPENAI_API_KEY`
- `host.ssh_key`: SSH private key path
- `host.ssh_password`: optional SSH password

## Example usage

```python
from attack_automation.attack_manager import AttackManager

manager = AttackManager("attack_automation/config.yaml")
manager.connect_vpn()
manager.connect_ssh()
print(manager.run_network_recon())
print(manager.run_recon())
print(manager.run_initial_access())
print(manager.run_privilege_escalation())
print(manager.fetch_attack_plan())
manager.close()
```

## Run the full attack flow

A convenience runner is included to connect VPN, run network recon, connect SSH, and execute host tasks:

```bash
python3 attack_automation/run_attack.py --config attack_automation/config.yaml
```

If you want the model to generate extra enumeration commands, add `--llm-auto-enum`:

```bash
python3 attack_automation/run_attack.py --config attack_automation/config.yaml --llm-auto-enum
```

To execute the commands returned by the model, add `--execute-llm`:

```bash
python3 attack_automation/run_attack.py --config attack_automation/config.yaml --llm-auto-enum --execute-llm
```

Use `--local-llm` to run the model-generated commands locally over the VPN instead of on the SSH host:

```bash
python3 attack_automation/run_attack.py --config attack_automation/config.yaml --llm-auto-enum --execute-llm --local-llm
```

This will:

1. connect VPN if configured
2. perform local network reconnaissance on the target IP
3. connect to the target via SSH
4. run remote host enumeration and initial access discovery
5. run privilege escalation enumeration
6. ask the model for additional enumeration commands
7. optionally execute those commands if requested

## Workflow

1. Connect to VPN (optional)
2. Connect to the target host via SSH
3. Run reconnaissance commands
4. Run initial access validation commands
5. Run privilege escalation enumeration commands
6. Ask the LLM for a recommended attack plan

## Limitations

- `vpn_connector.py` launches a VPN subprocess but does not validate route readiness or login.
- `ssh_connector.py` requires Paramiko and valid SSH credentials.
- `llm_client.py` requires the OpenAI library and a configured API key.
- Always use this framework only against authorized targets.
