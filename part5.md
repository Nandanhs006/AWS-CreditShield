---

## 17. HUMAN ACTIONS: everything the human must do

**Agent instruction:** copy this section into `docs/HUMAN_TODO.md` as a checkbox list at the start. When you reach an item (or need its result), print `HUMAN ACTION REQUIRED:` followed by the exact steps, wait for the human to confirm, then **verify with a command** where possible. Ask for values by telling the human exactly which command or screen shows them.

### Right now (about 5 minutes)

- [ ] **H0. Find the exact submission cut-off time.** Check the schedule page (`wemakedevs.org/aws/first-commit/schedule`), the WeMakeDevs Discord and WhatsApp channel, and your registration email. Tell the agent `HOURS_LEFT`. Plan to submit at least 60 to 90 minutes before the deadline.
- [ ] **H1. Confirm eligibility and check-in.** You are signed in to WeMakeDevs, registered for the tour, and **checked in to First Commit specifically** (the rules say to check in to each hackathon when it opens; other teams have flagged this as an easy miss). Confirm the team (1 to 4 people) and any Builder Center or student-verification requirement on the official rules page.

### AWS account (20 to 30 minutes; the agent scaffolds in parallel)

- [ ] **H2. AWS account.** Create a new account (or use the one made for this event). At sign-up you choose a Free plan or a Paid plan. Both start with credits ($100, plus up to $100 more for onboarding tasks; the hackathon says up to $200). A payment card is required for verification. The Free plan restricts some services and closes after 6 months or when credits run out; you can upgrade to the Paid plan at any time and remaining credits still apply. **If any service is blocked, upgrade.** Turn on MFA for the root user and do not use root for daily work.
- [ ] **H3. Earn the extra credits.** Billing, then Credits. Do only the cheap onboarding tasks (test a prompt in Bedrock, set a budget, create a Lambda with a function URL). Delete anything that costs money to leave running.
- [ ] **H4. Budget alert.** Billing, then Budgets: monthly cost budget of $10 with email alerts at 50% and 80%.
- [ ] **H5. Choose one region and use it everywhere.** Default `ap-south-1` (Mumbai). If the agent's preflight finds a service unavailable there, switch to `us-east-1` and update the model ID.
- [ ] **H6. Bedrock.** Console, Amazon Bedrock, in your region: open the model catalog and confirm Amazon Nova Lite is available. Open the Playground and send one test prompt (this confirms access and can earn credits). If a model asks for access or a first-time-use form, complete it. Send the agent the exact model or inference-profile ID (for example `apac.amazon.nova-lite-v1:0` in `ap-south-1`, `us.amazon.nova-lite-v1:0` in `us-east-1`). Prefer Nova: it needs no third-party form and credit coverage for third-party models is uncertain.
- [ ] **H7. CLI credentials (never paste them into chat or commit them).** Best: an IAM Identity Center user and `aws configure sso --profile hackathon`. Fast alternative: IAM, Users, create `hackathon-dev`, attach `AdministratorAccess` (acceptable for a short hackathon only), enable MFA, create an access key for CLI use, then run `aws configure --profile hackathon` and enter the key, secret, your region and `json`. Verify with `aws sts get-caller-identity --profile hackathon`. **Delete the access key after the event.**
- [ ] **H8. Install tools:** Git, Node.js 20 LTS or newer, Python 3.12, AWS CLI v2, AWS SAM CLI. Verify with `git --version`, `node --version`, `python --version`, `aws --version`, `sam --version`. Docker is optional (only for `sam build --use-container` if a build fails).

### GitHub and Antigravity (15 minutes)

- [ ] **H9. Create a new public GitHub repository** (for example `reprieve`) with a README, an MIT licence and a Node and Python `.gitignore`. Public is required for the submission. Clone it, set `git config user.name` and `user.email`, sign in to GitHub from git (credential manager or SSH key), and confirm `git push` works. Copy this file into the repo root as `PROJECT_SPEC.md` and commit it. The repo must contain only work made during the event.
- [ ] **H10.** Add teammates as collaborators if you have any.
- [ ] **H11. Open the repo in Antigravity** with Gemini Flash. Paste the kickoff prompt from Appendix B. Allow terminal commands but review anything destructive (deleting stacks or files). In the terminal set the profile: PowerShell `$env:AWS_PROFILE="hackathon"`, Bash `export AWS_PROFILE=hackathon`.

### During Phase 1 (first deploy)

- [ ] **H12. Approve the first deploy.** When the agent runs `sam deploy --guided`, answer: stack name `reprieve`, your region, allow IAM role creation `Y`, save arguments to `samconfig.toml` `Y`. If CloudFormation reports an error, paste the message to the agent.
- [ ] **H13. Create staff users.** Run `python scripts/create_users.py`. It asks for two emails and a password **in the terminal** (never in chat) and creates one user in group `ops` and one in group `manager`. Use two emails you can access. Keep the credentials for the demo and for `scripts/smoke.py`.
- [ ] **H14. Generate frontend settings.** Run `python scripts/write_env.py`. It writes `frontend/.env.local` and prints the values you will paste into Amplify.

### During Phases 3 and 4

- [ ] **H15. Push policies and seed data.** Run `python scripts/sync_policies.py`, then `python scripts/seed.py`. The agent tells you when.

### Amplify Hosting (15 minutes; do it during Phase 3, not at the end)

- [ ] **H16. Connect Amplify to GitHub.** AWS Console, AWS Amplify, **Create new app**, **GitHub**. Authorise the AWS Amplify GitHub app for the `reprieve` repo only. Choose branch `main`. Tick **My app is a monorepo** and enter `frontend` as the app root. Confirm the build settings come from `amplify.yml`. Under advanced settings add the environment variables printed in H14: `VITE_API_URL`, `VITE_USER_POOL_ID`, `VITE_USER_POOL_CLIENT_ID`, `VITE_AWS_REGION`, `VITE_LENDER_NAME`, `VITE_CURRENCY`. Save and deploy. Copy the `https://main.<id>.amplifyapp.com` URL and give it to the agent, which will redeploy the backend with `PublicAppUrl` set so borrower links point to the live site.
- [ ] **H17.** Every push to `main` redeploys the site. If the site does not update, open the build log in Amplify and paste errors to the agent.

### Ongoing

- [ ] **H18. Test on your phone over mobile data** (not your Wi-Fi): open a borrower link, chat, accept a plan.
- [ ] **H19. Optional (Tier 2):** for email, SES, Identities, create identity for your sender and recipient emails and click the confirmation links (SES starts in sandbox mode, which only sends to verified addresses). For approver alerts, subscribe your email to the SNS topic and confirm.
- [ ] **H20. Watch cost.** Billing, Cost Explorer: check once mid-way and once before you submit. Tell the agent if anything looks off.

### Submission (last 90 minutes)

- [ ] **H21. Writeup.** The agent drafts `docs/SUBMISSION.md`; you edit it in your own voice. It covers the problem, the build, where AWS fits, the AI tools you used (for example Google Antigravity with Gemini Flash, plus any assistant you used for planning), three concrete things you learned, and honest limitations.
- [ ] **H22. Record the video** (Section 19), upload to YouTube as public or unlisted, and open the link in a private window while signed out.
- [ ] **H23. Submit** on the hackathon's own submission page: repo URL, video URL, writeup and live URL. Screenshot the confirmation.
- [ ] **H24. Tag the release:** `git tag v1.0-submission` then `git push --tags`. After this, only critical fixes.
- [ ] **H25. Leave the AWS stack running** until judging is finished. Afterwards clean up: empty the checkpoint bucket (see Section 20), `sam delete`, delete IAM access keys, delete the Amplify app.

---

## 18. Testing

### 18.1 Unit tests (`pytest`, no AWS needed)

Stress scoring (hero scores 73, 87, 62, 74; tier boundaries; idempotent cohort assignment), plan arithmetic (`ceil` maths, date shifts), input validation for tools, the numeric verifier, `jsonutil.normalize`, the hash chain (11.9), and message and money formatting helpers.

### 18.2 Integration tests (real deployed stack)

The 15-row Cedar matrix (8.6), decision log append and verify against real KMS and DynamoDB, and a chat turn with a live Bedrock call asserting on structure (a tool was called, a plan exists) rather than on exact text.

### 18.3 Smoke test (`scripts/smoke.py`)

Reads `OPS_EMAIL`, `OPS_PASSWORD`, `MGR_EMAIL`, `MGR_PASSWORD`, `API_URL`, `USER_POOL_CLIENT_ID` from the environment, signs in through Cognito (`USER_PASSWORD_AUTH`), and runs:

1. `GET /health`. `POST /admin/reset-heroes`. `POST /admin/detect`.
2. Open a case for `ACC-1001`, send scripted borrower messages, assert a plan with outcome `ALLOWED`, accept, poll until `APPLIED`, verify the log is valid.
3. Open a case for `ACC-1002`, ask for 30 days, assert `NEEDS_MANAGER_APPROVAL`, accept, assert an approval is `PENDING`, assert the `ops` user gets 403 on approve, approve as `manager`, poll until `APPLIED`.
4. Tamper with one log entry, assert verify fails at that `seq`, restore, assert valid.
5. Print PASS or FAIL per step. Retry a chat step up to twice if the model does not propose (model output varies).

### 18.4 Manual QA before recording

Borrower link on a phone, slow network, expired token, message length limit, double-click on Accept, refresh mid-workflow, ops user vs manager user views, and every screen at 1440 and 390 pixels wide.

### 18.5 CI (Tier 2)

GitHub Actions on push: backend unit tests, frontend `tsc --noEmit` and `npm run build`. No AWS credentials in CI.

---

## 19. Demo video and submission package

### 19.1 Script (target 2:50, hard limit 3:00)

| Time | Show | Say (one idea per line) |
|---|---|---|
| 0:00 to 0:15 | Title text: "Meera delivers food for a living." Her payout is late and her EMI is due in 6 days | Lenders usually find out after the missed payment. Reprieve helps before it happens, and lenders can trust it because it cannot exceed the limits they set |
| 0:15 to 0:35 | Portfolio with detection, factors, treated and control cohorts. Open Meera's case | Deterministic cash-flow signals flag stress early and explain why |
| 0:35 to 1:10 | Phone-size borrower chat. Meera asks for time. Plan card. Press Accept. Then the case view with the policy envelope in the "assistant's limit" zone | The AI talks. A Cedar policy decides. Meera consents with a button |
| 1:10 to 1:45 | Arjun asks for 30 days. Envelope turns amber. Switch to the manager, Approvals, approve. Quick cutaway of the Step Functions execution graph | Bigger concessions need a human. Step Functions waits, then applies |
| 1:45 to 2:10 | Sana's jailbreak attempt. Denied. Quick cutaway of the Cedar policy in the Verified Permissions console | Limits are policy, not prompt. The model cannot talk its way past them |
| 2:10 to 2:40 | Verify integrity shows intact, tamper demo shows the broken entry, restore. Quick cutaways: KMS key, S3 Object Lock checkpoint | Every decision is hash-chained, signed with KMS and checkpointed in write-once storage |
| 2:40 to 2:55 | Impact screen with the "Simulated data" banner, then the architecture diagram naming each AWS service | Measured against a control group. Serverless on AWS, cost per case is tiny |
| 2:55 to 3:00 | Logo and live URL | One line: relief within limits, provable afterwards |

### 19.2 Recording tips

Reset heroes before every take (`POST /admin/reset-heroes`). Run one chat beforehand to warm the Lambdas. Record at 1080p with a clean desktop and notifications off, in scenes you can re-take, then stitch. Show AWS console cutaways for 4 to 6 seconds each (judges need to see where AWS fits). Add captions. Have a backup take if Bedrock is slow. Upload early to check processing and open the link signed out.

### 19.3 README outline (the judges' second look)

Title and one-line pitch, live URL, demo video link, screenshots or GIFs, **the problem and who is on the other side**, **how it works** (the mermaid diagram from Section 4), **where AWS fits** (table: service, role, why), **architecture decisions** (Section 4.3), **cost and cost per case** (with the price assumptions stated), **governance model** (two-tier Cedar, hash chain, KMS, Object Lock), **what we learned** (three concrete points), **honest limitations** (synthetic data, simulated outcomes, illustrative limits, not a credit model, not compliance advice), how to run and deploy, AI tools used, third-party libraries and licences.

### 19.4 Final checklist

- [ ] Live URL works signed out and on a phone
- [ ] Borrower link works from another network
- [ ] Video at most 3:00, on YouTube, opens in a private window
- [ ] Public repo with commit history across the event, no secrets, README complete
- [ ] Writeup lists the AI tools used
- [ ] Submitted on the hackathon's submission page before the cut-off, confirmation saved
- [ ] AWS stack left running

---

## 20. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Bedrock `AccessDeniedException` | Model not enabled, wrong region, or the IAM policy covers only the inference-profile ARN | Allow both the inference-profile ARN and the foundation-model ARNs in all destination regions (15.5). Confirm model access in the Bedrock console |
| Bedrock `ValidationException` about the model ID | Wrong or missing inference-profile prefix for the region | Use `apac.` in `ap-south-1`, `us.` in `us-east-1`. Check the console for the exact ID |
| Chat returns 504 or times out | Tool loop too slow (API Gateway caps at 30 s) | Lower `maxTokens`, use Nova Lite, cap loop iterations, set Lambda timeout 28 s, return the fallback message |
| Cognito `NEW_PASSWORD_REQUIRED` | Users created without a permanent password | Use `admin-set-user-password --permanent` (the create_users script does this) |
| Manager check always fails | Groups claim arrives as the string `[ops manager]` | Parse the string, do not treat it as a list |
| `Object of type Decimal is not JSON serializable`, or hash mismatch on verify | DynamoDB `Decimal` | Run everything through `jsonutil.normalize()` before encoding or hashing |
| Verified Permissions `ValidationException` on a policy | Namespace or attribute mismatch with the schema | Use `Relief::` prefixes, Long for numbers, Boolean for flags. Fetch the schema back and compare |
| Verified Permissions returns `DENY` with an error | Missing entity attribute or wrong type in the request | Send all required Loan attributes with the right value types (`long`, `boolean`) |
| Step Functions `States.Timeout` | Approval not decided in time | Handled by `HandoffToHuman`. Use a short `approval_timeout_seconds` while testing |
| Approval succeeds but nothing applies | Task token already used or wrong token stored | Approval must be `PENDING`; store the token exactly as received; make the endpoint idempotent |
| S3 `put_object` with Object Lock fails | Bucket was created without Object Lock, or missing `s3:PutObjectRetention` | Recreate the bucket with `ObjectLockEnabled: true`; add the permission |
| Cannot delete the stack or bucket after the event | Objects are under governance retention | Delete object versions with `--bypass-governance-retention` using a principal that has `s3:BypassGovernanceRetention`, then delete the bucket |
| KMS `sign` fails | Wrong `MessageType` or digest length | Sign the 32-byte SHA-256 digest with `MessageType="DIGEST"` and `ECDSA_SHA_256` |
| CloudFormation rejects the KMS key | Rotation enabled on an asymmetric key | Remove `EnableKeyRotation` |
| CORS error in the browser | Missing `Authorization` or `Content-Type` in allowed headers, or wrong API URL | Fix `CorsConfiguration`; check `VITE_API_URL` |
| Amplify build fails | Node version, missing lockfile, or wrong app root | `nvm use 20` in `preBuild`, commit `package-lock.json`, app root `frontend` |
| `sam build` fails on Windows | Native wheel or path issue | Keep Lambda dependencies pure Python; use `sam build --use-container` if Docker is available |
| Costs rising unexpectedly | Retry loops or a scheduled function | Disable the EventBridge schedule, check CloudWatch for looping invocations, keep `maxTokens` low |
