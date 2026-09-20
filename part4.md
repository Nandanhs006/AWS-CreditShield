---

## 13. API specification

Base URL is the HTTP API stage URL (output `ApiUrl`). JSON in and out. Errors: `{"error": "<code>", "message": "<human readable>"}` with a correct HTTP status. Lambda proxy payload format 2.0: use `event["requestContext"]["http"]["method"]`, `event["rawPath"]`, `event["pathParameters"]`, `event["body"]` (JSON string), and `event["requestContext"]["authorizer"]["jwt"]["claims"]`.

### 13.1 Public (no auth, throttled, token-scoped)

| Method and path | Purpose |
|---|---|
| `GET /health` | `{ "ok": true, "version": "..." }` |
| `GET /public/chat/{token}` | Case view for the borrower: lender name, first name, messages, current plan (with `can_accept`), case status. Never returns internal IDs, policy IDs or log data |
| `POST /public/chat/{token}` | Body `{message}`. Runs one agent turn (Section 9.1). Returns new messages, plan, status |
| `POST /public/chat/{token}/accept` | Body `{plan_id}`. Starts the workflow (Section 10.1) |
| `POST /public/chat/{token}/decline` | Marks the current plan `DECLINED` and logs it |
| `POST /public/chat/{token}/handoff` | Borrower asks for a person. Sets `ESCALATED` |

### 13.2 Staff (Cognito JWT; group in brackets)

| Method and path | Group | Purpose |
|---|---|---|
| `GET /me` | any | Email and groups |
| `GET /accounts?tier=&cohort=` | any | Portfolio list with score, tier, factors, cohort, latest case status |
| `GET /accounts/{id}` | any | One account with full factors |
| `POST /admin/detect` | ops | Run stress detection (Section 7) |
| `POST /cases` | ops | Body `{account_id}`. Opens a case if none is open. Only `TREATED` accounts unless `force: true`. Returns `{case_id, borrower_link}` where the link is `<PUBLIC_APP_URL>/#/b/<token>` |
| `GET /cases` | any | List of cases |
| `GET /cases/{id}` | any | Case, account, messages with tool traces, plan, approvals |
| `GET /cases/{id}/log` | any | Log entries with a server-generated one-line `summary` each |
| `GET /cases/{id}/log/verify` | any | Section 11.6 |
| `GET /approvals?status=PENDING` | any | Approval queue |
| `POST /approvals/{id}/decision` | manager | Section 10.3 |
| `GET /metrics/impact` | any | Section 12.2 |
| `POST /admin/simulate/outcomes` | ops | Section 12.1 |
| `POST /admin/simulate/borrower` | ops | Section 9.7 |
| `POST /admin/demo/tamper`, `POST /admin/demo/restore` | ops | Section 11.8 |
| `POST /admin/reset-heroes` | ops | Restore hero accounts, archive their earlier cases |

### 13.3 Cross-cutting rules

- API Gateway stage throttling: burst 20, rate 10 requests per second (verify the property names in SAM).
- Public routes use `Auth: Authorizer: NONE` on the SAM event; every other route uses the Cognito JWT authorizer (use the **ID token**, which carries `cognito:groups`).
- CORS: allow origin `*` for now (bearer tokens, no cookies), headers `Authorization` and `Content-Type`. Tighten to the Amplify origin at the end if time allows.
- JSON encoding must handle `Decimal` (shared `jsonutil`).
- Log one structured JSON line per request (route, status, duration, case_id if present). Never log message text or tokens.

---

## 14. Frontend specification

### 14.1 Screens

Routing uses `HashRouter`. Staff routes require login; the borrower route is public.

| Route | Screen | Contents |
|---|---|---|
| `#/login` | Sign in | Email and password via Cognito. Show clear errors |
| `#/` | Portfolio | KPI strip (accounts, flagged, high, open cases, pending approvals). Table of flagged accounts: name, product, score bar, top two factor chips, cohort, case status, action. Buttons: **Run detection**, **Open case** (treated only) and **Copy borrower link** |
| `#/cases/:id` | Case | Left: conversation transcript, with a collapsible "How the agent got here" (tool calls). Right (sticky): **Policy envelope** for the current plan and the decision, then the **Decision log rail** with **Verify integrity**. Tier 1: **Run simulated borrower** with persona select. Demo-only tamper controls (feature flag) |
| `#/approvals` | Approvals | Cards for pending requests: borrower name, what was asked, the reason the borrower gave, the policy envelope, who may approve. **Approve** and **Reject** with a note. Manager only (others see a read-only view) |
| `#/impact` | Impact (Tier 1) | Persistent banner "Simulated data". Cure rate treated vs control with interval bars, uplift, concession cost, autonomous-resolution rate, average tokens and estimated cost per case. Button **Advance 30 days** (runs outcome simulation) |
| `#/audit` | Audit | List of cases with chain status badges and a **Verify all** action |
| `#/b/:token` | Borrower chat (public) | See 14.3 |

### 14.2 Signature components

- **Policy envelope:** a horizontal track for numeric options (shift days, tenure months, fee amount). Three zones: allowed for the agent alone (`allow` colour), needs a manager (`review` colour), not allowed for anyone (`deny` colour). A marker shows the requested value and a label states the outcome in words ("Within the assistant's limit", "Needs a manager", "Outside every limit"). Partial plans show the two values as chips with the same outcome label. Below it, show the determining policy descriptions.
- **Decision log rail:** a vertical chain of squares connected by lines, one per entry, with a short summary and the first 8 characters of the hash in monospace. After **Verify integrity**, every node shows sealed (`seal` colour). If verification fails, draw the broken link in `deny` colour with the reason ("Entry 7 was changed after it was signed").
- Everything else stays quiet. Spend the visual effort on those two elements.

### 14.3 Borrower chat (mobile first, single column, max width 480px)

- Header: lender name and a line "You are chatting with an AI assistant. A person can join any time." plus a **Talk to a person** button.
- Message bubbles; a typing indicator while waiting. Handle slow replies (up to 28 seconds) with a calm "Still thinking" state, and errors with a clear retry.
- When a plan exists: a **plan card** above the input showing the plain-language summary, an outcome note ("This can be confirmed now" or "A colleague will review this after you accept, it is not guaranteed"), and **Accept** and **Decline** buttons. Disable buttons after pressing and poll the case status.
- After acceptance show status: "Sent for review", "Confirmed: new due date 3 Oct", or "We could not grant this. Here are other options".
- Never show internal IDs, policy names or hashes to the borrower.

### 14.4 Design direction (apply the `frontend-design` skill guidance if available)

The product is about care within limits. The feel is **calm, clear and humane**, closer to a well-run clinic desk than a trading terminal. Avoid the generic fintech look: no dark mode with neon accents, no gradient washes, no identical rounded cards everywhere, no ALL-CAPS eyebrow labels, no numbered section markers, no monospace for ordinary labels.

| Token | Value | Use |
|---|---|---|
| `--bg` | `#EEF1F0` | App background |
| `--surface` | `#FFFFFF` | Panels |
| `--ink` | `#16232B` | Text |
| `--ink-2` | `#56666E` | Secondary text |
| `--line` | `#D5DDDF` | Borders |
| `--allow` | `#1E7B62` | Allowed, success |
| `--review` | `#B7791F` | Needs review |
| `--deny` | `#B42318` | Denied, error, broken chain |
| `--seal` | `#3F51B5` | Verified and sealed states |

Type: Public Sans for everything (weights 400, 500, 600), JetBrains Mono only for hashes and policy IDs. Scale 13, 14, 16, 20, 28 px. Sentence case everywhere. One border radius (6px) and hairline borders instead of shadows. Left navigation rail 220px wide; content max width 1200px. Meet 4.5:1 contrast, visible keyboard focus, respect `prefers-reduced-motion`. The single memorable moment: the policy envelope reacting when the agent proposes something.

Microcopy: plain verbs, describe outcomes ("Confirmed", "Sent for review"), errors say what happened and what to do.

### 14.4 Auth and data

- `aws-amplify` v6: `Amplify.configure({ Auth: { Cognito: { userPoolId, userPoolClientId } } })` using `VITE_USER_POOL_ID` and `VITE_USER_POOL_CLIENT_ID`. Use `signIn`, `signOut`, `fetchAuthSession` and send `session.tokens.idToken.toString()` as `Authorization: Bearer ...`.
- API base from `VITE_API_URL`. TanStack Query for fetching. Poll `GET /cases/{id}` every 3 seconds while a workflow is running; poll `GET /approvals` every 5 seconds on the Approvals screen.
- Other env vars: `VITE_AWS_REGION`, `VITE_LENDER_NAME` (default "Harbour Finance", fictional), `VITE_CURRENCY` (default `INR`, format with `Intl.NumberFormat("en-IN")`).
- Include a footer note on staff screens: "All data is synthetic."

---

## 15. Infrastructure (AWS SAM)

One `template.yaml`. Stack name `reprieve`.

### 15.1 Parameters

`BedrockModelId` (default `apac.amazon.nova-lite-v1:0`), `LenderName`, `PublicAppUrl` (Amplify URL once known, default `http://localhost:5173`), `EnableTamperDemo` (`true`), `ApprovalTimeoutSeconds` (`86400`), `MaxMessagesPerCase` (`40`).

### 15.2 Globals

Runtime `python3.12`, architecture `arm64`, memory 512 MB, timeout 15 s (chat function 28 s), `CodeUri: backend/src/`, log retention 14 days, environment variables from 15.4.

### 15.3 Resources

| Resource | Notes |
|---|---|
| 5 DynamoDB tables | `PAY_PER_REQUEST`. GSIs from Section 6 |
| `AWS::Cognito::UserPool` | Email as username, `AdminCreateUserConfig.AllowAdminCreateUserOnly: true` |
| Two `AWS::Cognito::UserPoolGroup` | `ops`, `manager` |
| `AWS::Cognito::UserPoolClient` | No secret. Auth flows `ALLOW_USER_SRP_AUTH`, `ALLOW_USER_PASSWORD_AUTH`, `ALLOW_REFRESH_TOKEN_AUTH` |
| `AWS::Serverless::HttpApi` | JWT authorizer (issuer and audience from the pool and client), CORS, throttling |
| Functions | `PublicApiFn` (28 s), `StaffApiFn`, `DetectFn`, and workflow tasks `WfRecheckFn`, `WfRequestApprovalFn`, `WfApplyFn`, `WfRejectFn`, `WfNotifyFn`, `WfCloseFn`, `WfHandoffFn` |
| `AWS::Serverless::StateMachine` | Type `STANDARD`, definition from the ASL file with substitutions, logging to CloudWatch |
| `AWS::KMS::Key` and `AWS::KMS::Alias` | `KeySpec: ECC_NIST_P256`, `KeyUsage: SIGN_VERIFY`, default key policy for the account root. **No rotation** |
| `AWS::S3::Bucket` (checkpoints) | `ObjectLockEnabled: true`, versioning enabled, all public access blocked, `DeletionPolicy: Retain` |
| `AWS::VerifiedPermissions::PolicyStore` | `ValidationSettings.Mode: STRICT`, schema from Appendix A. Policies are pushed by script |
| Optional (Tier 2) | EventBridge schedule on `DetectFn` (`rate(1 hour)`), SNS topic for approver alerts |

### 15.4 Environment variables for Lambdas

`TABLE_ACCOUNTS`, `TABLE_CASES`, `TABLE_MESSAGES`, `TABLE_APPROVALS`, `TABLE_LOG`, `POLICY_STORE_ID`, `SIGNING_KEY_ID`, `CHECKPOINT_BUCKET`, `BEDROCK_MODEL_ID`, `STATE_MACHINE_ARN`, `ENABLE_TAMPER_DEMO`, `LENDER_NAME`, `PUBLIC_APP_URL`, `MAX_MESSAGES_PER_CASE`, `APPROVAL_TIMEOUT_SECONDS`, `PROMPT_VERSION`, `PRICE_IN_PER_1M`, `PRICE_OUT_PER_1M`.

### 15.5 Least-privilege IAM by function

- **PublicApiFn:** DynamoDB on `cases`, `messages`, `accounts` (read), `approvals` none, `decisionlog` (read and write); `states:StartExecution` on the state machine; `bedrock:InvokeModel` and `bedrock:Converse`-related actions on the inference profile and the foundation models (see below); `verifiedpermissions:IsAuthorized`, `BatchIsAuthorized`, `GetPolicy`; `kms:Sign` on the key.
- **StaffApiFn:** DynamoDB on all tables; `states:SendTaskSuccess` and `SendTaskFailure`; `verifiedpermissions:IsAuthorized`, `BatchIsAuthorized`, `GetPolicy`; `kms:Sign`, `kms:Verify`; `s3:PutObject` and `s3:GetObject`, `s3:ListBucket` on the checkpoint bucket; `bedrock` (for the simulated borrower).
- **Workflow functions:** only what each needs (tables, `kms:Sign`, Verified Permissions, S3 put for `WfCloseFn`).
- **Bedrock with cross-region inference profiles:** the IAM policy must allow `bedrock:InvokeModel*` on **both** the inference-profile ARN (`arn:aws:bedrock:<region>:<account>:inference-profile/*`) **and** the underlying foundation-model ARNs in every destination region (`arn:aws:bedrock:*::foundation-model/amazon.nova-*`). Missing the second is the most common `AccessDeniedException`.

### 15.6 Deploy commands (run by the agent, confirmed by the human)

```
sam validate --lint
sam build
sam deploy --guided --profile hackathon
```

Guided answers: stack name `reprieve`, the chosen region, allow IAM role creation (`CAPABILITY_IAM`), save arguments to `samconfig.toml`. Later deploys: `sam build` then `sam deploy --profile hackathon`.

### 15.7 Amplify build file (`amplify.yml`, repo root)

Appendix A has the file. In the Amplify console, tick the monorepo option and set the app root to `frontend`. Amplify environment variables: `VITE_API_URL`, `VITE_USER_POOL_ID`, `VITE_USER_POOL_CLIENT_ID`, `VITE_AWS_REGION`, `VITE_LENDER_NAME`, `VITE_CURRENCY`.

---

## 16. Build phases and acceptance criteria

Time boxes are for a fast pace with an AI coding agent. Every phase ends **deployed and committed**. Phases marked **[spine]** survive the "spine cut" from Section 3.2.

| Phase | Time box | Build | Done when |
|---|---|---|---|
| **1. Foundation and first deploy** [spine] | 1.5 h | Repo, `.gitignore`, LICENSE, README stub. `template.yaml` with tables, Cognito, HTTP API, KMS key, checkpoint bucket, Verified Permissions store and schema. `scripts/preflight.py`, `write_env.py`, `create_users.py`. Frontend scaffold with login and a call to `/me`. First `sam deploy` | Preflight prints PASS for credentials, DynamoDB, Cognito, KMS, Step Functions, Verified Permissions and a real Bedrock call. `/health` returns 200. Staff can sign in locally and see their groups |
| **2. Decision log library** [spine] | 1 h | `governance/decisionlog.py`, `jsonutil`, verify endpoint, tests from 11.9 | All log tests pass. A deployed test call appends entries and verifies as intact |
| **3. Data, stress and portfolio** | 1.25 h | `domain/stress.py` with tests, `seed.py`, `POST /admin/detect`, `GET /accounts`, Portfolio screen | Hero scores are 73, 87, 62, 74. Portfolio renders factors and tier. Cases can be opened and a borrower link copied |
| **4. Cedar policies and authorization** [spine] | 1 h | Policy files, `sync_policies.py`, `authorize.py` with probing, integration tests | All 15 matrix rows pass against the real store |
| **5. Agent and chat** [spine] | 2.5 h | Bedrock client, tools, loop, prompt, public chat endpoints, borrower page with plan card, case view with transcript and policy envelope | Meera flow works from the borrower link: plan card appears, envelope shows `ALLOWED`. Arjun's 30-day ask shows `NEEDS_MANAGER_APPROVAL`. Log entries appear for every step |
| **6. Workflow and approvals** | 1.5 h | State machine, workflow Lambdas, accept/decline/handoff, approvals API and screen, `apply_plan` | Meera acceptance applies automatically. Arjun's request waits, a `manager` approves, it applies. An `ops`-only user gets 403 on approve |
| **7. Verify UI, tamper demo and log rail** [spine] | 1 h | Decision log rail, Verify integrity, tamper and restore controls | Verify shows intact; tamper then verify shows the broken entry; restore heals it |
| **8. Ship the Tier 0 build** | 0.75 h | Amplify connected and deploying from `main`, environment variables set, phone test of the borrower link, README first pass | Live HTTPS URL works from a phone. Borrower link works from a different network |
| **9. Tier 1 loop** | up to 3 h | In the order given in Section 3.1 | Each item deployed before starting the next |
| **10. Video and submission** | 1.5 h reserved | Rehearse, record, upload, submit | Section 19 checklist complete |

**Code freeze:** stop feature work 2 hours before the cut-off. After that, only fix bugs, finish the README, record and submit.

**Cut order if you are behind:** drop, in this order, Tier 2, Impact screen, simulated personas, Object Lock checkpoints, verifier, then approvals via Step Functions (use the DynamoDB-only fallback). Never drop Cedar, the decision log or the deployed URL.
