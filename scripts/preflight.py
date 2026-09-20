"""
CreditShield Preflight Health Check Script
Verifies AWS STS identity, active region, and core service availability.
"""
import os
import sys
import boto3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.src.common import config


def run_preflight():
    print("=" * 65)
    print(" CREDITSHIELD PREFLIGHT DIAGNOSTICS (AWS FREE TIER)")
    print("=" * 65)

    region = os.environ.get("AWS_REGION", "ap-south-1")
    print(f"Target Region: {region}")

    # 1. Check STS Identity
    try:
        sts = boto3.client("sts", region_name=region)
        identity = sts.get_caller_identity()
        print(f"[PASS] AWS Account: {identity.get('Account')} | ARN: {identity.get('Arn')}")
    except Exception as e:
        print(f"[FAIL] STS Caller Identity failed: {e}")
        print("       Run: aws configure (or set AWS_PROFILE)")

    # 2. Check DynamoDB
    try:
        ddb = boto3.client("dynamodb", region_name=region)
        tables = ddb.list_tables().get("TableNames", [])
        print(f"[PASS] DynamoDB accessible. Active tables in region: {len(tables)}")
    except Exception as e:
        print(f"[FAIL] DynamoDB unreachable: {e}")

    # 3. Check Bedrock
    try:
        bedrock = boto3.client("bedrock", region_name=region)
        models = bedrock.list_foundation_models()
        nova_found = any("nova" in m.get("modelId", "").lower() for m in models.get("modelSummaries", []))
        print(f"[PASS] Amazon Bedrock accessible. Nova models available: {nova_found}")
    except Exception as e:
        print(f"[WARN] Bedrock API check: {e}")

    # 4. Check KMS
    try:
        kms = boto3.client("kms", region_name=region)
        keys = kms.list_keys(Limit=5).get("Keys", [])
        print(f"[PASS] AWS KMS accessible. Sample keys count: {len(keys)}")
    except Exception as e:
        print(f"[FAIL] KMS unreachable: {e}")

    print("=" * 65)
    print(" Preflight check finished.")
    print("=" * 65)


if __name__ == "__main__":
    run_preflight()
