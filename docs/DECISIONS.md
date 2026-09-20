# CreditShield — Key Architectural Decisions

1. **Two-Tier Cedar Policy Authorization**  
   - First ask Cedar: *"May the AI agent offer this alone?"*  
   - If not, ask Cedar: *"May a human credit manager approve this?"*  
   - If not, nobody may grant it (`DENIED`).  
   - *Rationale:* Eliminates policy duplication and maps cleanly to lending governance hierarchies.

2. **Limits as Audited Data, Not System Prompts**  
   - Concession boundaries live in Amazon Verified Permissions Cedar policies.  
   - *Rationale:* Protects against LLM hallucinations, prompt injections, and allows risk officers to adjust lending rules dynamically without code deployments.

3. **Cryptographic Non-Repudiation (KMS + Hash Chain + S3 Object Lock)**  
   - Every event is sequentially hash-chained (SHA-256) and signed with an asymmetric AWS KMS key (`ECC_NIST_P256`).  
   - Checkpoints are saved to Amazon S3 with `ObjectLockMode="GOVERNANCE"`.  
   - *Rationale:* Prevents database administrators or rogue insiders from modifying the audit trail retroactively. Amazon QLDB was avoided as it has been sunset.

4. **Human-in-the-Loop Callback via AWS Step Functions**  
   - When a concession requires manager approval, the workflow pauses via `waitForTaskToken`.  
   - *Rationale:* Eliminates polling loops, handles automatic timeouts (24h), and provides a visual execution graph for compliance review.

5. **Serverless & AWS Free Tier ("Ship It" Track) Compliance**  
   - Architecture runs on DynamoDB on-demand (25GB free tier), AWS Lambda arm64 (1M free calls), Amazon Cognito (50,000 MAUs free), and Amazon Nova Lite.  
   - *Rationale:* Zero idle costs ($0.00/month standby) and micro-cost scaling ($0.0031 per borrower resolution).
