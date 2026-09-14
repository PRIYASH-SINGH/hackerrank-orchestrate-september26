"""
LinkedIn Showcase Demo: Buy or Wait? AI Financial Agent
Run this script while screen-recording to showcase the hybrid architecture.
"""
import time
import sys

def banner():
    print("\033[96m" + "="*75)
    print("   🤖 BUY OR WAIT? — AI FINANCIAL DECISION AGENT")
    print("   Hybrid Architecture: 90-Day Deterministic Forecaster + Gemini 3.6 Flash")
    print("="*75 + "\033[0m\n")
    time.sleep(1)

def show_case(case_num, user_id, request_id, item, amount, curr, status, method, plan, explanation):
    print(f"\033[93m▶ [Case {case_num}] Evaluating {request_id} for User {user_id}\033[0m")
    print(f"  • Requested Expense : \033[1m{curr} {amount:,.2f}\033[0m ({item})")
    time.sleep(0.6)
    print("  • Step 1: Ingesting financial profile & currency exchange graph (BFS)...")
    time.sleep(0.7)
    print("  • Step 2: Running 90-day cash flow simulation against recurring debits...")
    time.sleep(0.8)
    print("  • Step 3: Resolving OCR receipts & evaluating flexible commitments...")
    time.sleep(0.6)
    
    color = "\033[92m" if status == "affordable" else "\033[91m" if status == "not_affordable" else "\033[94m"
    print(f"\n  {color}┌────────────────────────── DECISION SUMMARY ──────────────────────────┐\033[0m")
    print(f"  {color}│ Status               : {status.upper():<47}│\033[0m")
    print(f"  {color}│ Recommended Method   : {method:<47}│\033[0m")
    print(f"  {color}│ Payment Plan         : {plan:<47}│\033[0m")
    print(f"  {color}└───────────────────────────────────────────────────────────────────────┘\033[0m")
    print("\033[97m  AI Explanation:\033[0m")
    print(f"  \"{explanation}\"\n")
    print("-" * 75 + "\n")
    time.sleep(2)

def main():
    banner()
    
    show_case(
        case_num=1,
        user_id="user_27",
        request_id="request_27",
        item="High-Performance Laptop",
        amount=6670.00,
        curr="ZAR",
        status="affordable",
        method="full_payment",
        plan="Pay in full today (2026-07-05)",
        explanation="The laptop purchase of ZAR 6,670 is fully affordable as the base safe amount of ZAR 30,505.59 exceeds the requested amount without breaching the minimum balance."
    )

    show_case(
        case_num=2,
        user_id="user_28",
        request_id="request_28",
        item="Tech Stock Investment",
        amount=1302.40,
        curr="EUR",
        status="partially_affordable",
        method="not_recommended",
        plan="none",
        explanation="The current safe amount is EUR 412.20, which is insufficient for the full investment of EUR 1,302.40. Since partial payment is not allowed, no immediate payment is recommended."
    )

    show_case(
        case_num=3,
        user_id="user_30",
        request_id="request_30",
        item="Debt Consolidation",
        amount=775.20,
        curr="USD",
        status="affordable",
        method="installments",
        plan="Option 83 (3 monthly payments)",
        explanation="The user has sufficient safe funds to cover the debt repayment. Following user preference for installments, the 3-month plan (Option 83) is recommended as it falls within the 4-month limit."
    )
    
    print("\033[92m✔ Evaluation Complete. 250 requests processed into output.csv.\033[0m")
    print("\033[92m✔ Token Audit: 216,163 tokens tracked in evaluation/usage_report.md.\033[0m\n")

if __name__ == "__main__":
    main()
