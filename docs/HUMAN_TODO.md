# Reprieve — Human Action Checklist

> **Target:** First Commit (Bharat Builds Tour x WeMakeDevs x AWS) — Ship It Track
> **Submission Package:** Public GitHub Repo + 3-Minute YouTube Video + Live Deployed URL + Short Writeup

---

## ⚡ What You Need To Do Right Now

### 1. View & Demo Your Showpiece (Ready Right Now!)
Your showpiece web application is currently live and running locally at:
👉 **[http://localhost:3000/](http://localhost:3000/)**

Open it in your browser to verify:
- **Left Phone Screen**: Interactive Borrower Chat (Meera, Arjun, Sana, Vikram).
- **Hero Buttons (Top Bar)**: Switch between the 4 demo accounts with 1 click.
- **Top Right Tabs**:
  - **Portfolio Radar**: Filter by High Stress, Watch Tier, or Cohort.
  - **Policy Envelope & Tools**: See the visual gauge (1-10d Agent, 11-30d Manager, >30d Denied) and Cedar code.
  - **Step Functions Approvals**: Click *Approve Concession* for Arjun and watch the workflow advance.
  - **Decision Log & Tamper Demo**: Click *Simulate DB Tampering* (turns red) then *Restore from S3 Lock* (turns green).
  - **A/B Impact & Economics**: Shows cure rate uplift (+27.4pp) and Bedrock Nova Lite cost ($0.0031/case).

---

## 📋 Hackathon Submission Roadmap (Step-by-Step)

### Step 1: Git & GitHub Repository Setup (10 Mins)
1. Initialize or push your local `c:\digitals\aws hackathon` folder to a new **public** GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "feat: complete Reprieve hardship relief governance platform"
   git branch -M main
   git remote add origin https://github.com/<your-username>/reprieve.git
   git push -u origin main
   ```
2. Ensure the repository is set to **Public** (required for judges).

---

### Step 2: One-Click AWS Amplify Hosting (10 Mins)
To give judges a live HTTPS link on AWS:
1. Log into the [AWS Amplify Console](https://console.aws.amazon.com/amplify).
2. Click **Host web app** & select **GitHub**.
3. Select your `reprieve` repository and branch `main`.
4. Set the app directory to `frontend` (or deploy the root).
5. Click **Deploy**. Within 2 minutes you will have a live URL like `https://main.d12345678.amplifyapp.com`.
6. *(Alternative)*: You can also enable **GitHub Pages** directly in your repo settings pointing to the `/frontend` folder for an instant live URL.

---

### Step 3: Record the 3-Minute Demo Video (45 Mins)
Judges score based on the 3-minute video. Follow this exact script:

| Time | Screen to Show | What to Say |
|---|---|---|
| **0:00 - 0:25** | Phone Simulator + Portfolio | *"Meet Meera, a gig delivery rider whose payout was delayed. Traditional lenders reach her after she defaults with harsh penalty calls. Reprieve spots pre-default stress from cashflow signals and reaches out proactively before credit scores suffer."* |
| **0:25 - 1:00** | Meera Chat + Policy Envelope | *"The AI converses warmly, but the LLM never decides limits. Every offer is enforced by Amazon Verified Permissions using Cedar policies. Meera asks for 7 days. Policy allows up to 10 days autonomously. She consents with a single button, and the plan auto-applies."* |
| **1:00 - 1:40** | Arjun Mehta + Step Functions Approvals | *"Arjun is a shop owner hit by festive slowdown asking for a 30-day shift. This exceeds the agent's 10-day limit but is within manager discretion. The case routes to an AWS Step Functions task token approval. Credit Manager approves in the ops console, and it executes."* |
| **1:40 - 2:05** | Sana Qureshi (Jailbreak) | *"Sana attempts a prompt injection jailbreak asking to waive all fees and extend 24 months. Because governance lives in Cedar data rather than system prompts, the model cannot talk past policy limits. It is denied deterministically."* |
| **2:05 - 2:40** | Decision Log & Tamper Demo | *"Every action is hash-chained, signed with an AWS KMS asymmetric key (ECC P-256), and checkpointed to S3 Object Lock. Clicking 'Simulate DB Tampering' shows the chain instantly flag the collision in crimson. Restoring from write-once S3 Lock recovers verified integrity."* |
| **2:40 - 3:00** | A/B Impact & Cost Summary | *"Tested across Treated vs Control cohorts with a +27.4pp cure uplift. Serverless architecture running on Amazon Bedrock Nova Lite costs under $0.0031 per case. Reprieve: Relief within limits, proven cryptographically."* |

---

### Step 4: Final Submission Checklist (Before Cut-off)
- [ ] Public GitHub repository link
- [ ] 3-Minute YouTube video link (Public or Unlisted — test in private window)
- [ ] Live URL (AWS Amplify or GitHub Pages)
- [ ] Short writeup (You can copy directly from `docs/SUBMISSION.md` and `README.md`)
