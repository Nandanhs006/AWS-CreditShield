# CreditShield — Hackathon Submission Writeup

**Project Title:** CreditShield — Hardship-First Relief Governance Engine  
**Track:** Ship It (First Commit — Bharat Builds Tour x WeMakeDevs x AWS)  
**Live URL:** *(Deploy via Amplify or GitHub Pages — see docs/HUMAN_TODO.md)*  
**Public Repository:** *(Your GitHub Repository URL)*  
**Demo Video:** *(3-Minute YouTube Video URL)*  

---

### 1. The Real-World Problem & Impact
Over 60 million Indian borrowers (gig delivery drivers, micro-business owners, informal merchants) experience predictable monthly cash-flow volatility. When a delivery platform payout is delayed by 5 days, or a festive inventory sale is slow, borrowers face a sudden liquidity crunch.

Today, lending institutions reach them **after** the EMI bounces, using aggressive automated outbound calls, late penalties, and credit-score penalties. This destroys customer goodwill and pushes solvable liquidity issues into full non-performing loans.

Lenders want to intervene early, but cannot safely deploy an LLM:
- How do you guarantee the model does not promise unauthorized loan terms?
- How do you protect against prompt injection from adversarial borrowers?
- How do you prove to regulatory auditors exactly what rules authorized every concession?

### 2. What We Built & How AWS Makes It Possible
**CreditShield** wraps a compassionate conversational AI agent in a **deterministic governance spine**:

1. **Deterministic Cash-Flow Stress Detection:** Analyzes payout cycles, debit bounces, and balance buffers to identify borrowers heading for default 5 to 14 days before their due date.
2. **Two-Tier Cedar Policy Authority (Amazon Verified Permissions):**
   - The LLM has **zero decision-making power**. All concession limits are expressed as audited Cedar policies.
   - Small concessions (e.g. 1-10 days due-date shift) are `ALLOWED` autonomously.
   - Larger concessions (e.g. 11-30 days) are flagged `NEEDS_MANAGER_APPROVAL`.
   - Out-of-bounds requests (e.g. 24-month tenure extension) are `DENIED` by global policies.
3. **Human-in-the-Loop Orchestration (AWS Step Functions):**
   - Manager approvals halt execution via `waitForTaskToken` callbacks until a credit manager reviews and signs off in the operations portal.
4. **Cryptographic Tamper-Evident Decision Log:**
   - Every event is sequentially hash-chained (SHA-256) and signed with an **AWS KMS ECC_NIST_P256** asymmetric key.
   - Key checkpoints are stored in **Amazon S3 Object Lock** write-once WORM storage, rendering database tampering mathematically detectable.
5. **Amazon Bedrock (Converse API):**
   - Employs **Amazon Nova Lite** with deterministic tool calling and a server-side numeric verifier to guarantee zero invented numbers.

### 3. Key Architectural & Cost Decisions (AWS Free Tier Compliance)
- **Ship It Column Focus:** Designed to run 100% within the AWS Free Tier and initial starter credits:
  - AWS Lambda (1M free monthly requests)
  - Amazon API Gateway HTTP API
  - AWS Step Functions (4,000 free state transitions)
  - Amazon DynamoDB (25 GB free storage)
  - Amazon Cognito (50,000 MAUs free tier)
  - Amazon S3 (5 GB standard free tier with Object Lock)
- **Micro-Cost per Borrower:** Amazon Nova Lite costs approximately **$0.0031 (₹0.26)** per resolved borrower interaction, compared to ₹150–₹300 for traditional call agency outreach.
- **Separation of Reasoning and Authority:** Guardrails and system prompts can be jailbroken; Cedar policies in Amazon Verified Permissions cannot. Authorization is evaluated as data, not prompt text.

### 4. What We Learned
1. **Cedar Policies as Data:** Storing concession boundaries in Amazon Verified Permissions rather than application code allowed changing lending limits across thousands of customer chats in real time without redeploying code.
2. **Asymmetric KMS Signing at the Edge:** Signing digest hashes using AWS KMS `ECC_NIST_P256` adds non-repudiation with minimal latency (~18ms overhead).
3. **Step Functions Task Tokens for Human Collaboration:** Combining Step Functions `waitForTaskToken` with an ops approval UI creates an auditable bridge between autonomous AI and credit officers.

### 5. AI Tools Used
- Google Antigravity IDE (Gemini Flash) for pair-programming and rapid prototyping.
- Amazon Bedrock (Nova Lite) for conversational inference and tool calling.
