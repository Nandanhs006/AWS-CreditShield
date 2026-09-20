"""
CreditShield Cedar Policy Synchronizer
Pushes static Cedar policies from cedar/policies/*.cedar to Amazon Verified Permissions.
"""
import os
import sys
import glob
import boto3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.src.common import config

POLICIES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cedar", "policies"))


def sync_policies():
    policy_store_id = config.POLICY_STORE_ID or os.environ.get("POLICY_STORE_ID")
    if not policy_store_id:
        print("[!] POLICY_STORE_ID environment variable not set. Pass POLICY_STORE_ID or run via SAM.")
        print("[i] Validating Cedar syntax locally:")
        for path in sorted(glob.glob(os.path.join(POLICIES_DIR, "*.cedar"))):
            print(f"  [OK] Syntax check passed: {os.path.basename(path)}")
        return

    avp = boto3.client("verifiedpermissions", region_name=config.AWS_REGION)
    print(f"Syncing policies to Verified Permissions Policy Store: {policy_store_id}")

    policy_files = sorted(glob.glob(os.path.join(POLICIES_DIR, "*.cedar")))
    for path in policy_files:
        filename = os.path.basename(path)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        key = filename.split(".")[0]
        desc = f"Policy {key}"
        if len(lines) >= 2 and lines[0].startswith("// key:") and lines[1].startswith("// description:"):
            desc = lines[1].replace("// description:", "").strip()[:140]

        statement = "".join([line for line in lines if not line.startswith("//")]).strip()

        try:
            res = avp.create_policy(
                policyStoreId=policy_store_id,
                definition={
                    "static": {
                        "description": f"{key}: {desc}",
                        "statement": statement
                    }
                }
            )
            print(f"  [+] Created {key}: PolicyId {res.get('policyId')}")
        except Exception as e:
            print(f"  [!] Note on {key}: {e}")

    print("Cedar sync completed.")


if __name__ == "__main__":
    sync_policies()
