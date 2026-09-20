"""
CreditShield Database Seeder
Seeds 4 Hero Accounts + 36 realistic filler accounts into DynamoDB.
"""
import os
import sys
import argparse
import random
from datetime import datetime, date

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.src.common import config
from backend.src.common import ddb
from backend.src.domain import stress

HERO_ACCOUNTS = [
    {
        "account_id": "ACC-1001",
        "name": "Meera Iyer",
        "first_name": "Meera",
        "segment": "GIG",
        "product": "TWO_WHEELER",
        "emi": 6200,
        "outstanding": 88000,
        "dpd": 0,
        "prior_reliefs": 0,
        "legal_hold": False,
        "late_fee_due": 350,
        "next_due_date": "2026-09-26",
        "days_to_emi": 6,
        "cashflow": {
            "income_prior_avg": 28000,
            "income_last30": 12500,
            "bounced_60d": 1,
            "avg_balance_7d": 2100
        },
        "cohort": "TREATED"
    },
    {
        "account_id": "ACC-1002",
        "name": "Arjun Mehta",
        "first_name": "Arjun",
        "segment": "SHOP_OWNER",
        "product": "MICRO_BUSINESS",
        "emi": 14500,
        "outstanding": 310000,
        "dpd": 9,
        "prior_reliefs": 1,
        "legal_hold": False,
        "late_fee_due": 1200,
        "next_due_date": "2026-09-23",
        "days_to_emi": 3,
        "cashflow": {
            "income_prior_avg": 62000,
            "income_last30": 31000,
            "bounced_60d": 2,
            "avg_balance_7d": 3800
        },
        "cohort": "TREATED"
    },
    {
        "account_id": "ACC-1003",
        "name": "Sana Qureshi",
        "first_name": "Sana",
        "segment": "SALARIED",
        "product": "PERSONAL_LOAN",
        "emi": 9800,
        "outstanding": 210000,
        "dpd": 35,
        "prior_reliefs": 2,
        "legal_hold": False,
        "late_fee_due": 800,
        "next_due_date": "2026-10-10",
        "days_to_emi": 20,
        "cashflow": {
            "income_prior_avg": 45000,
            "income_last30": 31500,
            "bounced_60d": 2,
            "avg_balance_7d": 5000
        },
        "cohort": "TREATED"
    },
    {
        "account_id": "ACC-1004",
        "name": "Vikram Rao",
        "first_name": "Vikram",
        "segment": "SALARIED",
        "product": "PERSONAL_LOAN",
        "emi": 11000,
        "outstanding": 260000,
        "dpd": 20,
        "prior_reliefs": 1,
        "legal_hold": True,
        "late_fee_due": 600,
        "next_due_date": "2026-09-25",
        "days_to_emi": 5,
        "cashflow": {
            "income_prior_avg": 52000,
            "income_last30": 30000,
            "bounced_60d": 1,
            "avg_balance_7d": 4000
        },
        "cohort": "TREATED"
    }
]

FILLER_NAMES = [
    ("Kavita Patel", "GIG", "TWO_WHEELER", 5400),
    ("Rajesh Sharma", "SHOP_OWNER", "MICRO_BUSINESS", 18000),
    ("Anita Deshmukh", "SALARIED", "PERSONAL_LOAN", 8200),
    ("Rohan Verma", "GIG", "TWO_WHEELER", 6100),
    ("Sunita Roy", "SHOP_OWNER", "MICRO_BUSINESS", 12500),
    ("Devendra Joshi", "SALARIED", "PERSONAL_LOAN", 15000),
    ("Pooja Kulkarni", "GIG", "TWO_WHEELER", 4800),
    ("Manoj Tiwari", "SHOP_OWNER", "MICRO_BUSINESS", 22000),
    ("Deepa Nambiar", "SALARIED", "PERSONAL_LOAN", 7500),
    ("Karthik Subramanian", "SALARIED", "PERSONAL_LOAN", 19500),
    ("Farhan Ali", "GIG", "TWO_WHEELER", 5800),
    ("Geeta Bansal", "SHOP_OWNER", "MICRO_BUSINESS", 16000),
    ("Nitin Gadkari", "SALARIED", "PERSONAL_LOAN", 10200),
    ("Shreya Ghoshal", "GIG", "TWO_WHEELER", 4900),
    ("Aakash Mittal", "SHOP_OWNER", "MICRO_BUSINESS", 25000),
    ("Priya Sen", "SALARIED", "PERSONAL_LOAN", 11500),
    ("Vikrant Massey", "GIG", "TWO_WHEELER", 6400),
    ("Alka Yagnik", "SALARIED", "PERSONAL_LOAN", 8900),
    ("Chetan Bhagat", "SHOP_OWNER", "MICRO_BUSINESS", 13800),
    ("Ananya Pandey", "GIG", "TWO_WHEELER", 5100),
    ("Siddharth Roy", "SALARIED", "PERSONAL_LOAN", 17200),
    ("Kareena Kapoor", "SHOP_OWNER", "MICRO_BUSINESS", 21500),
    ("Ranbir Das", "GIG", "TWO_WHEELER", 5600),
    ("Dia Mirza", "SALARIED", "PERSONAL_LOAN", 9400),
    ("Ayushmann Khurrana", "SHOP_OWNER", "MICRO_BUSINESS", 19800),
    ("Radhika Apte", "GIG", "TWO_WHEELER", 4700),
    ("Varun Dhawan", "SALARIED", "PERSONAL_LOAN", 14200),
    ("Taapsee Pannu", "SHOP_OWNER", "MICRO_BUSINESS", 16500),
    ("Ishaan Khatter", "GIG", "TWO_WHEELER", 6800),
    ("Tabu Nair", "SALARIED", "PERSONAL_LOAN", 12300),
    ("Boman Irani", "SHOP_OWNER", "MICRO_BUSINESS", 23400),
    ("Sanya Malhotra", "GIG", "TWO_WHEELER", 5300),
    ("Pankaj Tripathi", "SALARIED", "PERSONAL_LOAN", 15800),
    ("Richa Chadha", "SHOP_OWNER", "MICRO_BUSINESS", 17900),
    ("Ali Fazal", "GIG", "TWO_WHEELER", 6100),
    ("Neena Gupta", "SALARIED", "PERSONAL_LOAN", 8800)
]


def generate_accounts():
    accounts = []
    # 1. Hero accounts
    for hero in HERO_ACCOUNTS:
        score, tier, factors = stress.calculate_stress_score(hero)
        hero["stress_score"] = score
        hero["stress_tier"] = tier
        hero["stress_factors"] = factors
        accounts.append(hero)

    # 2. 36 Filler accounts
    random.seed(42)
    for idx, (name, segment, product, emi) in enumerate(FILLER_NAMES, start=2005):
        acc_id = f"ACC-{idx}"
        first_name = name.split()[0]
        income = emi * random.randint(3, 6)
        
        # 60% healthy, 25% watch, 15% high stress
        dice = random.random()
        if dice < 0.60:
            income_last30 = income
            bounces = 0
            balance = emi * 2
            dpd = 0
            days = random.randint(10, 25)
        elif dice < 0.85:
            income_last30 = int(income * 0.75)
            bounces = 1
            balance = int(emi * 0.4)
            dpd = random.randint(0, 10)
            days = random.randint(4, 15)
        else:
            income_last30 = int(income * 0.45)
            bounces = 2
            balance = int(emi * 0.15)
            dpd = random.randint(5, 25)
            days = random.randint(2, 7)

        acc = {
            "account_id": acc_id,
            "name": name,
            "first_name": first_name,
            "segment": segment,
            "product": product,
            "emi": emi,
            "outstanding": emi * random.randint(12, 36),
            "dpd": dpd,
            "prior_reliefs": 0 if dpd == 0 else 1,
            "legal_hold": False,
            "late_fee_due": 0 if dpd == 0 else 500,
            "next_due_date": "2026-09-28",
            "days_to_emi": days,
            "cashflow": {
                "income_prior_avg": income,
                "income_last30": income_last30,
                "bounced_60d": bounces,
                "avg_balance_7d": balance
            }
        }
        score, tier, factors = stress.calculate_stress_score(acc)
        acc["stress_score"] = score
        acc["stress_tier"] = tier
        acc["stress_factors"] = factors
        acc["cohort"] = "TREATED" if (hash(acc_id) % 2 == 0) else "CONTROL"
        accounts.append(acc)

    return accounts


def main():
    parser = argparse.ArgumentParser(description="CreditShield DynamoDB Seeder")
    parser.add_argument("--reset-heroes", action="store_true", help="Restore hero accounts to baseline")
    parser.add_argument("--dry-run", action="store_true", help="Print accounts without writing to DynamoDB")
    args = parser.parse_args()

    accounts = generate_accounts()
    print(f"Generated {len(accounts)} accounts ({len(HERO_ACCOUNTS)} heroes + {len(FILLER_NAMES)} filler).")

    if args.dry_run:
        for acc in accounts[:4]:
            print(f"Hero: {acc['name']} ({acc['account_id']}) -> Score: {acc['stress_score']} ({acc['stress_tier']})")
        return

    print("Seeding into DynamoDB Table:", config.TABLE_ACCOUNTS)
    for acc in accounts:
        try:
            ddb.save_account(acc)
            print(f"  [+] Saved {acc['account_id']}: {acc['name']} (Score: {acc['stress_score']})")
        except Exception as e:
            print(f"  [!] Offline / Error saving {acc['account_id']}: {e}")
            break

    print("Seed complete.")


if __name__ == "__main__":
    main()
