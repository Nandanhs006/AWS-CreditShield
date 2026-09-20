"""
CreditShield Configuration & Environment Variables
"""
import os

TABLE_ACCOUNTS = os.environ.get("TABLE_ACCOUNTS", "creditshield-accounts")
TABLE_CASES = os.environ.get("TABLE_CASES", "creditshield-cases")
TABLE_MESSAGES = os.environ.get("TABLE_MESSAGES", "creditshield-messages")
TABLE_APPROVALS = os.environ.get("TABLE_APPROVALS", "creditshield-approvals")
TABLE_LOG = os.environ.get("TABLE_LOG", "creditshield-decisionlog")

SIGNING_KEY_ID = os.environ.get("SIGNING_KEY_ID", "")
CHECKPOINTS_BUCKET = os.environ.get("CHECKPOINTS_BUCKET", "")
POLICY_STORE_ID = os.environ.get("POLICY_STORE_ID", "")
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN", "")

MANAGER_APPROVAL_TOPIC_ARN = os.environ.get("MANAGER_APPROVAL_TOPIC_ARN", "")
RELIEF_EVENTS_TOPIC_ARN = os.environ.get("RELIEF_EVENTS_TOPIC_ARN", "")
TELEMETRY_QUEUE_URL = os.environ.get("TELEMETRY_QUEUE_URL", "")
CORE_BANKING_SYNC_QUEUE_URL = os.environ.get("CORE_BANKING_SYNC_QUEUE_URL", "")

BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "apac.amazon.nova-lite-v1:0")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "bedrock")  # "bedrock" or "gemini"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL_ID = os.environ.get("GEMINI_MODEL_ID", "gemini-2.5-flash")

LENDER_NAME = os.environ.get("LENDER_NAME", "Harbour Finance")
PUBLIC_APP_URL = os.environ.get("PUBLIC_APP_URL", "http://localhost:3000")
ENABLE_TAMPER_DEMO = os.environ.get("ENABLE_TAMPER_DEMO", "true").lower() in ("true", "1", "yes")

AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
APPROVAL_TIMEOUT_SECONDS = int(os.environ.get("APPROVAL_TIMEOUT_SECONDS", "86400"))
MAX_MESSAGES_PER_CASE = int(os.environ.get("MAX_MESSAGES_PER_CASE", "40"))
MAX_MESSAGE_CHAR_LENGTH = int(os.environ.get("MAX_MESSAGE_CHAR_LENGTH", "600"))

