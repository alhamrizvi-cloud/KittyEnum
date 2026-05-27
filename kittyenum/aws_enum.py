#!/usr/bin/env python3
"""KittyEnum AWS enumeration module.
This module performs AWS reconnaissance using AWS CLI or boto3 when available.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime

MAGENTA = "\033[95m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def info(msg):
    print(f"{MAGENTA}{BOLD}[AWS]{RESET} {msg}")


def ok(msg):
    print(f"{GREEN}{BOLD}[OK]{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}{BOLD}[WARN]{RESET} {msg}")


def write_output(path, title, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n# Generated: {datetime.utcnow().isoformat()}Z\n\n")
        if isinstance(content, (dict, list)):
            f.write(json.dumps(content, indent=2, sort_keys=True))
        else:
            f.write(str(content))
        f.write("\n")


def run_cmd(cmd, env=None):
    info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    return result.returncode, result.stdout


def aws_cli_available():
    return shutil.which("aws") is not None


def boto3_available():
    try:
        import boto3  # noqa: F401
        return True
    except ImportError:
        return False


def aws_env(args):
    env = os.environ.copy()
    if args.profile:
        env["AWS_PROFILE"] = args.profile
    if args.region:
        env["AWS_REGION"] = args.region
    if args.access_key:
        env["AWS_ACCESS_KEY_ID"] = args.access_key
    if args.secret_key:
        env["AWS_SECRET_ACCESS_KEY"] = args.secret_key
    if args.session_token:
        env["AWS_SESSION_TOKEN"] = args.session_token
    return env


def build_aws_command(args, service, operation, extra=None):
    cmd = ["aws", service, operation, "--output", "json"]
    if extra:
        cmd += extra
    if args.region:
        cmd += ["--region", args.region]
    if args.profile:
        cmd += ["--profile", args.profile]
    return cmd


def aws_cli_run(args, outdir):
    commands = [
        ("sts", ["get-caller-identity"], "STS Caller Identity"),
        ("iam", ["get-account-summary"], "IAM Account Summary"),
        ("iam", ["list-account-aliases"], "IAM Account Aliases"),
        ("iam", ["list-users"], "IAM Users"),
        ("iam", ["list-roles"], "IAM Roles"),
        ("iam", ["list-policies", "--scope", "Local"], "IAM Customer-managed Policies"),
        ("ec2", ["describe-instances"], "EC2 Instances"),
        ("ec2", ["describe-security-groups"], "EC2 Security Groups"),
        ("ec2", ["describe-vpcs"], "EC2 VPCs"),
        ("s3", ["ls"], "S3 Buckets"),
        ("s3api", ["list-buckets"], "S3 Bucket List"),
        ("lambda", ["list-functions"], "Lambda Functions"),
        ("secretsmanager", ["list-secrets"], "Secrets Manager Secrets"),
        ("ssm", ["describe-parameters"], "SSM Parameters"),
        ("rds", ["describe-db-instances"], "RDS Instances"),
        ("ecs", ["list-clusters"], "ECS Clusters"),
        ("cloudtrail", ["describe-trails"], "CloudTrail Trails"),
        ("kms", ["list-keys"], "KMS Keys"),
        ("ecr", ["describe-repositories"], "ECR Repositories"),
    ]

    env = aws_env(args)
    for service, params, label in commands:
        outfile = os.path.join(outdir, f"aws_{service}_{params[0]}.json")
        cmd = build_aws_command(args, service, params[0], params[1:])
        rc, output = run_cmd(cmd, env=env)
        write_output(outfile, label, output)
        if rc == 0:
            ok(label)
        else:
            warn(f"{label} failed; saved output")

    if args.bucket:
        bucket_path = os.path.join(outdir, "aws_s3_bucket_listing.txt")
        cmd = build_aws_command(args, "s3", "ls", [f"s3://{args.bucket}", "--no-sign-request"])
        rc, output = run_cmd(cmd, env=env)
        write_output(bucket_path, f"S3 bucket listing for {args.bucket}", output)
        if rc == 0:
            ok(f"S3 bucket listing for {args.bucket}")
        else:
            warn(f"S3 bucket listing for {args.bucket} failed; saved output")

    ecs_cluster_file = os.path.join(outdir, "aws_ecs_cluster_tasks.json")
    cmd = build_aws_command(args, "ecs", "list-clusters")
    rc, output = run_cmd(cmd)
    if rc == 0:
        try:
            data = json.loads(output)
            clusters = data.get("clusterArns", [])
            cluster_tasks = {}
            for cluster in clusters[:10]:
                task_cmd = build_aws_command(args, "ecs", "list-tasks", ["--cluster", cluster])
                t_rc, t_output = run_cmd(task_cmd)
                if t_rc == 0:
                    cluster_tasks[cluster] = json.loads(t_output)
                else:
                    cluster_tasks[cluster] = {"error": t_output}
            write_output(ecs_cluster_file, "ECS cluster tasks", cluster_tasks)
            ok("ECS cluster task enumeration")
        except json.JSONDecodeError:
            warn("Could not parse ECS cluster list output")
            write_output(ecs_cluster_file, "ECS cluster tasks", output)
    else:
        warn("ECS cluster list failed; skipping task enumeration")


def boto3_run(args, outdir):
    try:
        import boto3
    except ImportError:
        warn("boto3 is not installed")
        return

    session_kwargs = {}
    if args.profile:
        session_kwargs["profile_name"] = args.profile
    if args.region:
        session_kwargs["region_name"] = args.region
    if args.access_key:
        session_kwargs["aws_access_key_id"] = args.access_key
    if args.secret_key:
        session_kwargs["aws_secret_access_key"] = args.secret_key
    if args.session_token:
        session_kwargs["aws_session_token"] = args.session_token

    session = boto3.Session(**session_kwargs)
    services = {
        "sts": ("get_caller_identity", {}),
        "iam": ("get_account_summary", {}),
        "iam_aliases": ("list_account_aliases", {}),
        "iam_users": ("list_users", {}),
        "iam_roles": ("list_roles", {}),
        "ec2_instances": ("describe_instances", {}),
        "ec2_sgs": ("describe_security_groups", {}),
        "ec2_vpcs": ("describe_vpcs", {}),
        "s3_buckets": ("list_buckets", {}),
        "lambda_funcs": ("list_functions", {}),
        "secrets": ("list_secrets", {}),
        "ssm_params": ("describe_parameters", {}),
        "rds_instances": ("describe_db_instances", {}),
        "ecs_clusters": ("list_clusters", {}),
        "cloudtrail": ("describe_trails", {}),
        "kms_keys": ("list_keys", {}),
        "ecr_repos": ("describe_repositories", {}),
    }

    for name, (action, params) in services.items():
        service_name = name.split("_")[0]
        client = session.client(service_name)
        outfile = os.path.join(outdir, f"aws_{name}.json")
        try:
            data = getattr(client, action)(**params)
            write_output(outfile, f"{service_name} {action}", data)
            ok(f"{service_name} {action}")
        except Exception as exc:
            warn(f"{service_name} {action} failed: {exc}")
            write_output(outfile, f"{service_name} {action} error", str(exc))

    if args.bucket:
        bucket_path = os.path.join(outdir, "aws_s3_bucket_listing.json")
        s3 = session.client("s3")
        try:
            data = s3.list_objects_v2(Bucket=args.bucket, MaxKeys=50)
            write_output(bucket_path, f"S3 bucket listing for {args.bucket}", data)
            ok(f"S3 bucket listing for {args.bucket}")
        except Exception as exc:
            warn(f"S3 bucket listing failed: {exc}")
            write_output(bucket_path, f"S3 bucket listing error", str(exc))


def main():
    parser = argparse.ArgumentParser(description="KittyEnum AWS enumeration module")
    parser.add_argument("--outdir", default="./recon-output")
    parser.add_argument("--profile", help="AWS CLI profile to use")
    parser.add_argument("--region", help="AWS region to use")
    parser.add_argument("--access-key", help="AWS access key ID")
    parser.add_argument("--secret-key", help="AWS secret access key")
    parser.add_argument("--session-token", help="AWS session token")
    parser.add_argument("--bucket", help="Optional S3 bucket name for bucket enumeration")
    args = parser.parse_args()

    outdir = os.path.join(args.outdir, "aws")
    os.makedirs(outdir, exist_ok=True)

    info("AWS enumeration module started")
    if aws_cli_available():
        aws_cli_run(args, outdir)
    elif boto3_available():
        warn("AWS CLI not installed; falling back to boto3")
        boto3_run(args, outdir)
    else:
        warn("Neither AWS CLI nor boto3 is available. Install awscli or boto3 to use AWS enumeration.")

    ok("AWS enumeration module complete")


if __name__ == "__main__":
    main()
