"""
CreditShield Cognito Staff User Creation Script
Creates 'ops' and 'manager' staff users in the Cognito User Pool.
"""
import os
import sys
import boto3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.src.common import config


def create_users():
    user_pool_id = os.environ.get("USER_POOL_ID")
    if not user_pool_id:
        print("[!] USER_POOL_ID environment variable not set. Pass USER_POOL_ID or deploy SAM first.")
        print("[i] Demo Persona Credentials:")
        print("  1. AI Operations: analyst@harbourfin.com / CreditShield2026! (Group: ops)")
        print("  2. Senior Supervisor: menon.supervisor@harbourfin.com / CreditShield2026! (Group: manager)")
        return

    cognito = boto3.client("cognito-idp", region_name=config.AWS_REGION)

    users = [
        {"email": "analyst@harbourfin.com", "group": "ops"},
        {"email": "menon.supervisor@harbourfin.com", "group": "manager"}
    ]
    password = "CreditShield2026!"

    for u in users:
        email = u["email"]
        group = u["group"]
        try:
            cognito.admin_create_user(
                UserPoolId=user_pool_id,
                Username=email,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "email_verified", "Value": "true"}
                ],
                TemporaryPassword=password,
                MessageAction="SUPPRESS"
            )
            print(f"  [+] Created user: {email}")
        except Exception as e:
            print(f"  [!] Note creating user {email}: {e}")

        # Set permanent password
        try:
            cognito.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=email,
                Password=password,
                Permanent=True
            )
            print(f"  [+] Set permanent password for: {email}")
        except Exception as e:
            print(f"  [!] Note setting password: {e}")

        # Add to group
        try:
            cognito.admin_add_user_to_group(
                UserPoolId=user_pool_id,
                Username=email,
                GroupName=group
            )
            print(f"  [+] Added {email} to group: {group}")
        except Exception as e:
            print(f"  [!] Note adding to group: {e}")

    print("Cognito staff provisioning complete.")


if __name__ == "__main__":
    create_users()
