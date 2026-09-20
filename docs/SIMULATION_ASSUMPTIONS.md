# Reprieve — Simulation & Economic Assumptions

### 1. Synthetic Data Disclaimer
All borrower names, loan accounts, and cash-flow signals are fictional, synthetic data generated for hackathon benchmarking purposes.

### 2. A/B Clinical Cure Probability Model
- **Control Arm (No Pre-Default Outreach):**
  - High Stress Tier: $P(\text{Cure}) = 0.35$
  - Watch Tier: $P(\text{Cure}) = 0.60$
- **Treated Arm (Reprieve AI Outreach):**
  - High Stress with Plan Applied: $P(\text{Cure}) = 0.55$ (+20pp lift)
  - Watch Tier with Plan Applied: $P(\text{Cure}) = 0.72$ (+12pp lift)
  - Case Opened but No Plan: $+0.03$ courtesy lift

### 3. Unit Economics Assumptions
- Average Bad Debt Loss per Default: ₹16,500
- Average Concession Cost per Relieved Borrower: ₹480 (temporary interest waiver / shift deferral cost)
- Bedrock Nova Lite Token Pricing:
  - Input: $0.06 per 1M tokens
  - Output: $0.24 per 1M tokens
  - Average tokens per resolution: 1,420 tokens $\approx \$0.0031$ (₹0.26)
