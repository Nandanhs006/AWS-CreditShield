# CreditShield — Human Action Checklist

> **Target:** First Commit (Bharat Builds Tour x WeMakeDevs x AWS) — Ship It Track
> **Submission Package:** Public GitHub Repo + 3-Minute YouTube Video + Live Deployed URL + Short Writeup

---

## ⚡ What You Need To Do Right Now

### 1. View & Demo Your CreditShield Showpiece (Live!)
Your showpiece web application is currently live and running locally at:
👉 **[http://localhost:3000/](http://localhost:3000/)**

Open it in your browser to verify:
- **Left Phone Screen**: Interactive Borrower Terminal (Meera, Arjun, Sana, Vikram).
- **Hero Buttons (Top Bar)**: Switch between the 4 demo accounts with 1 click.
- **Top Right Tabs**:
  - **[01] Portfolio Radar**: Filter by High Stress, Watch Tier, or Cohort.
  - **[02] Policy Envelope & Tools**: See the mechanical gauge (1-10d Agent, 11-30d Manager, >30d Denied) and Cedar code.
  - **[03] Step Functions Queue**: Click *Approve Concession* for Arjun and watch the workflow advance.
  - **[04] Decision Log & Tamper Demo**: Click *Simulate DB Tampering* (turns red) then *Restore from S3 Lock* (turns green).
  - **[05] A/B Impact & Economics**: Shows cure rate uplift (+27.4pp) and Bedrock Nova Lite cost ($0.0031/case).
  - **[06] AWS Free Tier Topology**: Review the complete Ship It compliant architecture.

---

## 📋 Hackathon Submission Roadmap (Step-by-Step)

### Step 1: Git & GitHub Repository Setup (10 Mins)
1. Initialize or push your local `c:\digitals\aws hackathon` folder to a new **public** GitHub repository named `CreditShield`:
   ```bash
   git add .
   git commit -m "feat: complete CreditShield brutalist governance showpiece"
   git remote add origin https://github.com/<your-username>/CreditShield.git
   git push -u origin main
   ```
2. Ensure the repository is set to **Public** (required for judges).

---

### Step 2: One-Click AWS Amplify Hosting (10 Mins)
To give judges a live HTTPS link on AWS:
1. Log into the [AWS Amplify Console](https://console.aws.amazon.com/amplify).
2. Click **Host web app** & select **GitHub**.
3. Select your `CreditShield` repository and branch `main`.
4. Set the app directory to `frontend`.
5. Click **Deploy**. Within 2 minutes you will have a live URL like `https://main.d12345678.amplifyapp.com`.
6. *(Alternative)*: You can also enable **GitHub Pages** directly in your repo settings pointing to the `/frontend` folder for an instant live URL.

---

### Step 3: Record the 3-Minute Demo Video (45 Mins)
Judges score based on the 3-minute video. Follow the exact script in [`docs/DEMO_SCRIPT.md`](file:///c:/digitals/aws%20hackathon/docs/DEMO_SCRIPT.md).

---

### Step 4: Final Submission Checklist (Before Cut-off)
- [ ] Public GitHub repository link (`CreditShield`)
- [ ] 3-Minute YouTube video link (Public or Unlisted — test in private window)
- [ ] Live URL (AWS Amplify or GitHub Pages)
- [ ] Short writeup (You can copy directly from `docs/SUBMISSION.md` and `README.md`)
