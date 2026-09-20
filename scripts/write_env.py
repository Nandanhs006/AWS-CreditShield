"""
CreditShield Environment Configuration Generator
Reads AWS CloudFormation outputs and writes frontend/.env.local.
"""
import os
import sys
import boto3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.src.common import config

FRONTEND_ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", ".env.local"))


def write_env(stack_name="creditshield-backend"):
    region = config.AWS_REGION
    outputs = {}

    try:
        cf = boto3.client("cloudformation", region_name=region)
        res = cf.describe_stacks(StackName=stack_name)
        for o in res["Stacks"][0].get("Outputs", []):
            outputs[o["OutputKey"]] = o["OutputValue"]
    except Exception as e:
        print(f"[!] Could not query CloudFormation stack '{stack_name}': {e}")
        print("[i] Using default fallback local configuration.")
        outputs = {
            "ApiUrl": "http://localhost:3000",
            "UserPoolId": "local-user-pool-id",
            "UserPoolClientId": "local-client-id",
            "PolicyStoreId": "local-policy-store-id"
        }

    env_lines = [
        f"VITE_API_URL={outputs.get('ApiUrl', 'http://localhost:3000')}",
        f"VITE_USER_POOL_ID={outputs.get('UserPoolId', '')}",
        f"VITE_USER_POOL_CLIENT_ID={outputs.get('UserPoolClientId', '')}",
        f"VITE_AWS_REGION={region}",
        f"VITE_LENDER_NAME={config.LENDER_NAME}",
        "VITE_CURRENCY=INR"
    ]

    with open(FRONTEND_ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(env_lines) + "\n")

    print(f"[+] Wrote environment settings to: {FRONTEND_ENV_PATH}")
    for line in env_lines:
        print(f"    {line}")


if __name__ == "__main__":
    stack = sys.argv[1] if len(sys.argv) > 1 else "creditshield-backend"
    write_env(stack)
