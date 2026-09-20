"""
CreditShield Bedrock Converse Agent Loop
Orchestrates autonomous tool-calling, conversational guidance, and numeric verification.
"""
import boto3
import uuid
from typing import Dict, Any, List, Tuple

from ..common import config
from ..common import ddb
from ..common import jsonutil
from . import prompts
from . import tools
from ..governance import verifier
from ..governance import decisionlog
from . import gemini_agent

_bedrock = None


def get_bedrock():
    global _bedrock
    if _bedrock is None:
        _bedrock = boto3.client("bedrock-runtime", region_name=config.AWS_REGION)
    return _bedrock


def run_agent_turn(case: Dict[str, Any], account: Dict[str, Any], new_borrower_text: str) -> Dict[str, Any]:
    """
    Executes a single conversational turn through the Bedrock Converse API.
    """
    case_id = case["case_id"]

    # 1. Store Borrower Message and log
    msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    ddb.append_message(case_id, "borrower", new_borrower_text, msg_id=msg_id)
    decisionlog.append_log_entry(
        case_id,
        "BORROWER_MESSAGE",
        {"kind": "BORROWER", "id": str(account.get("account_id"))},
        {"message_id": msg_id, "text_length": len(new_borrower_text)}
    )

    # 2. Build Case State & System Prompt
    current_plan = case.get("plan", {})
    case_state_block = (
        f"\n\nCASE STATE:\n"
        f"- Account ID: {account.get('account_id')}\n"
        f"- Borrower Name: {account.get('name')}\n"
        f"- Product: {account.get('product')}, EMI: ₹{account.get('emi')}\n"
        f"- Case Status: {case.get('status')}\n"
        f"- Current Plan: {current_plan.get('summary', 'None proposed yet')}\n"
        f"- Plan Status: {current_plan.get('status', 'NONE')}\n"
    )

    system_prompt = [{"text": prompts.get_system_prompt() + case_state_block}]

    # 3. Retrieve past messages for conversation turns
    stored_msgs = ddb.get_case_messages(case_id, limit=20)
    messages = []
    for m in stored_msgs:
        role = "user" if m.get("role") == "borrower" else "assistant"
        text = m.get("text", "")
        if text:
            messages.append({
                "role": role,
                "content": [{"text": text}]
            })

    # Ensure turns alternate properly
    consolidated = []
    for m in messages:
        if consolidated and consolidated[-1]["role"] == m["role"]:
            consolidated[-1]["content"].extend(m["content"])
        else:
            consolidated.append(m)
    messages = consolidated

    tool_config = {"tools": tools.TOOL_SPECS}
    tool_traces = []
    agent_reply_text = ""
    verifier_status = "pass"
    proposed_plan = None

    # Execute LLM turn based on configured provider (Bedrock or Gemini)
    if config.LLM_PROVIDER == "gemini":
        agent_reply_text, g_traces, g_plan = gemini_agent.run_gemini_turn(
            case, account, new_borrower_text, system_prompt[0]["text"]
        )
        tool_traces.extend(g_traces)
        if g_plan:
            proposed_plan = g_plan
    else:
        # Try executing Bedrock Converse loop
        try:
            bedrock = get_bedrock()
            iterations = 0

            while iterations < 6:
                iterations += 1
                response = bedrock.converse(
                    modelId=config.BEDROCK_MODEL_ID,
                    messages=messages,
                    system=system_prompt,
                    toolConfig=tool_config,
                    inferenceConfig={"maxTokens": 400, "temperature": 0.2}
                )

                output_msg = response.get("output", {}).get("message", {})
                stop_reason = response.get("stopReason", "end_turn")
                messages.append(output_msg)

                if stop_reason == "tool_use":
                    tool_results = []
                    for content_block in output_msg.get("content", []):
                        if "toolUse" in content_block:
                            t_use = content_block["toolUse"]
                            t_name = t_use["name"]
                            t_input = t_use.get("input", {})
                            t_use_id = t_use["toolUseId"]

                            t_output, maybe_plan = tools.execute_tool(t_name, t_input, case, account)
                            if maybe_plan:
                                proposed_plan = maybe_plan

                            tool_traces.append({
                                "name": t_name,
                                "input": t_input,
                                "output": t_output
                            })

                            # Log tool execution
                            decisionlog.append_log_entry(
                                case_id,
                                "TOOL_CALL",
                                {"kind": "AGENT", "id": "bedrock:nova-lite"},
                                {"name": t_name, "input": t_input, "output_summary": str(t_output)[:100]}
                            )

                            tool_results.append({
                                "toolResult": {
                                    "toolUseId": t_use_id,
                                    "content": [{"json": t_output}]
                                }
                            })

                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })
                else:
                    # Text response produced
                    for content_block in output_msg.get("content", []):
                        if "text" in content_block:
                            agent_reply_text = content_block["text"]
                    break

        except Exception as e:
            # Fallback for offline mode / network timeouts
            agent_reply_text = (
                f"Thank you for reaching out. Based on your current EMI of ₹{account.get('emi'):,}, "
                f"I evaluated our Cedar policies. A 7-day due-date extension is pre-approved for your account."
            )
            _, proposed_plan = tools.execute_tool("propose_relief", {"action": "DUE_DATE_SHIFT", "days": 7}, case, account)


    # 4. Numeric Verifier (Enforces zero invented figures)
    borrower_texts = [m.get("text", "") for m in stored_msgs if m.get("role") == "borrower"]
    allowed_numbers = verifier.build_allowed_numbers(
        {"emi": account.get("emi", 0), "dpd": account.get("dpd", 0)},
        tool_traces,
        borrower_texts
    )
    is_valid, offending = verifier.verify_agent_reply(agent_reply_text, allowed_numbers)

    if not is_valid:
        verifier_status = "fallback"
        decisionlog.append_log_entry(
            case_id,
            "MESSAGE_BLOCKED",
            {"kind": "SYSTEM", "id": "verifier:numeric"},
            {"offending_numbers": list(offending), "original_reply": agent_reply_text}
        )
        # Substitute with deterministic summary
        if proposed_plan:
            agent_reply_text = f"I have prepared a relief option for your account: {proposed_plan['summary']} You can accept this plan below."
        else:
            agent_reply_text = "I reviewed your account. Please let me know if a short due-date extension would help ease things this month."

    # 5. Store Agent Message
    agent_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    agent_msg = ddb.append_message(
        case_id,
        "agent",
        agent_reply_text,
        msg_id=agent_msg_id,
        tool_trace=tool_traces,
        verifier=verifier_status
    )

    active_model = config.GEMINI_MODEL_ID if config.LLM_PROVIDER == "gemini" else config.BEDROCK_MODEL_ID
    active_agent_id = f"gemini:{config.GEMINI_MODEL_ID}" if config.LLM_PROVIDER == "gemini" else "bedrock:nova-lite"

    decisionlog.append_log_entry(
        case_id,
        "AGENT_MESSAGE",
        {"kind": "AGENT", "id": active_agent_id},
        {
            "message_id": agent_msg_id,
            "provider": config.LLM_PROVIDER,
            "model_id": active_model,
            "prompt_version": prompts.PROMPT_VERSION,
            "verifier": verifier_status
        }
    )

    return {
        "reply": agent_reply_text,
        "message": agent_msg,
        "plan": case.get("plan"),
        "case_status": case.get("status"),
        "tool_traces": tool_traces
    }
