# CreditShield — AWS Setup & Action Checklist

> **Track:** Ship It (First Commit — Bharat Builds Tour x WeMakeDevs x AWS)  
> **Cost Objective:** 100% AWS Free Tier Compliant ($0.00 Standby Bill)

---

## 🚀 Immediate AWS Actions for the Human (Ranked by Priority)

### 1. Amazon Bedrock Model Access (5 Minutes)
> *Why:* The agent uses Amazon Nova Lite for low-latency, lowest-cost inference covered by starter credits.
- [ ] Log into the [AWS Console](https://console.aws.amazon.com/).
- [ ] Set your region to **`ap-south-1` (Mumbai)** or **`us-east-1` (N. Virginia)**.
- [ ] Navigate to **Amazon Bedrock** $\rightarrow$ **Model catalog** (left sidebar).
- [ ] Search for **Amazon Nova Lite** (`amazon.nova-lite-v1:0`).
- [ ] Click **Request access** or **Enable** (Nova models usually enable instantly with zero review forms).
- [ ] Open Bedrock **Playgrounds** $\rightarrow$ Chat, select Amazon Nova Lite, and type: `"Hello"`. Verify you receive a response.

---

### 2. AWS CLI Setup & Credentials (10 Minutes)
> *Why:* Required if you wish to run `sam deploy` or use AWS CLI scripts locally.
- [ ] Open your terminal and check:
  ```powershell
  aws --version
  ```
- [ ] Configure your credentials (use an IAM user with programmatic access):
  ```powershell
  aws configure --profile hackathon
  ```
  - **AWS Access Key ID:** `[Your Access Key]`
  - **AWS Secret Access Key:** `[Your Secret Key]`
  - **Default region name:** `ap-south-1` (or `us-east-1`)
  - **Default output format:** `json`
- [ ] Verify access:
  ```powershell
  aws sts get-caller-identity --profile hackathon
  ```

---

### 3. Deploy Live URL via AWS Amplify (10 Minutes)
> *Why:* The **Ship It** track requires a live deployed HTTPS URL for judging.
- [ ] Push your local repository to a **public** GitHub repo:
  ```powershell
  git add .
  git commit -m "feat: complete CreditShield platform"
  git branch -M main
  git remote add origin https://github.com/<your-username>/CreditShield.git
  git push -u origin main
  ```
- [ ] Open the [AWS Amplify Console](https://console.aws.amazon.com/amplify).
- [ ] Click **Create new app** $\rightarrow$ choose **GitHub**.
- [ ] Authorize GitHub and select repository **`CreditShield`**, branch **`main`**.
- [ ] Check the box: **My app is a monorepo** and set app root to: **`frontend`**.
- [ ] Click **Save and Deploy**.
- [ ] Within ~2 minutes, Amplify will generate a live HTTPS URL:
  `https://main.d123456789.amplifyapp.com`
- [ ] *Alternative Fallback:* If Amplify setup is delayed, enable **GitHub Pages** in your repo Settings $\rightarrow$ Pages $\rightarrow$ source: branch `main` / folder `/frontend` for an immediate live URL!

---

### 4. Amazon Cognito User Setup (Optional / 5 Minutes)
> *Why:* Simulates role-based authorization for Operations Analysts (`ops`) vs Supervisors (`manager`).
- [ ] The local showpiece UI includes a simulated Cognito Auth switcher with pre-configured tokens.
- [ ] If deploying the real SAM stack (`template.yaml`), run:
  ```powershell
  python scripts/create_users.py
  ```
  This provisions:
  - `analyst@harbourfin.com` $\rightarrow$ Group: `ops`
  - `supervisor@harbourfin.com` $\rightarrow$ Group: `manager`

---

### 5. SAM Stack Backend Deployment (Optional / When Ready)
> *Why:* Only needed if connecting the live frontend to real deployed Lambdas and DynamoDB.
- [ ] Validate the SAM template:
  ```powershell
  sam validate --lint
  ```
- [ ] Build the serverless application:
  ```powershell
  sam build
  ```
- [ ] Deploy to AWS:
  ```powershell
  sam deploy --guided --profile hackathon
  ```
  - Stack Name: `CreditShield`
  - AWS Region: `ap-south-1`
  - Confirm changes before deploy: `Y`
  - Allow SAM CLI to create IAM roles: `Y`
  - Save arguments to configuration file: `Y`

---

### 6. Submission Checklist (Before Cut-off)
- [ ] Public GitHub repository link
- [ ] Live HTTPS URL (Amplify or GitHub Pages)
- [ ] 3-Minute YouTube demo video (Unlisted or Public — test in Incognito mode)
- [ ] Project writeup (copy directly from `docs/SUBMISSION.md`)
