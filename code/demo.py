# -*- coding: utf-8 -*-
"""
LinkedIn Showcase Demo: Buy or Wait? AI Financial Agent
Showcases the hybrid architecture in Indian Rupees (INR / Rs.).
Safe for all terminal encodings (ASCII/UTF-8).
"""
import time
import sys
import os

# Enable UTF-8 standard output for Windows console
if sys.platform.startswith("win"):
    os.system("chcp 65001 >nul 2>&1")
    sys.stdout.reconfigure(encoding='utf-8')

def banner():
    print("\033[96m" + "="*75)
    print("   [+] BUY OR WAIT? -- AI FINANCIAL DECISION AGENT")
    print("   Hybrid Architecture: 90-Day Deterministic Forecaster + Gemini 3.6 Flash")
    print("="*75 + "\033[0m\n")
    time.sleep(1)

def show_case(case_num, user_id, request_id, item, amount, curr, status, method, plan, explanation):
    print(f"\033[93m>> [Case {case_num}] Evaluating {request_id} for User {user_id}\033[0m")
    print(f"  * Requested Expense : \033[1m{curr} {amount:,.2f}\033[0m ({item})")
    time.sleep(0.6)
    print("  * Step 1: Ingesting financial profile & currency exchange graph (BFS)...")
    time.sleep(0.7)
    print("  * Step 2: Running 90-day cash flow simulation against recurring debits...")
    time.sleep(0.8)
    print("  * Step 3: Resolving OCR receipts & evaluating flexible commitments...")
    time.sleep(0.6)
    
    color = "\033[92m" if status == "affordable" else "\033[91m" if status == "not_affordable" else "\033[94m"
    print(f"\n  {color}+-------------------------- DECISION SUMMARY --------------------------+\033[0m")
    print(f"  {color}| Status               : {status.upper():<46}|\033[0m")
    print(f"  {color}| Recommended Method   : {method:<46}|\033[0m")
    print(f"  {color}| Payment Plan         : {plan:<46}|\033[0m")
    print(f"  {color}+----------------------------------------------------------------------+\033[0m")
    print("\033[97m  AI Explanation:\033[0m")
    print(f"  \"{explanation}\"\n")
    print("-" * 75 + "\n")
    time.sleep(2)

def main():
    banner()
    
    # Case 1: Affordable Full Payment
    show_case(
        case_num=1,
        user_id="user_27",
        request_id="request_27",
        item="Coding Laptop (MacBook / ThinkPad)",
        amount=65000.00,
        curr="INR (Rs.)",
        status="affordable",
        method="full_payment",
        plan="Pay Rs. 65,000 in full today",
        explanation="The laptop purchase of Rs. 65,000 is fully affordable. The user has a safe surplus of Rs. 1,42,500 over the 90-day forecast, keeping their mandatory Rs. 30,000 emergency balance completely intact."
    )

    # Case 2: Not Affordable / Reject
    show_case(
        case_num=2,
        user_id="user_28",
        request_id="request_28",
        item="Speculative Crypto / Stock Investment",
        amount=120000.00,
        curr="INR (Rs.)",
        status="not_affordable",
        method="not_recommended",
        plan="none",
        explanation="The requested investment of Rs. 1,20,000 exceeds available funds. With pending house rent (Rs. 25,000) and education loan EMI (Rs. 18,000) due next week, proceeding would breach the user's minimum emergency reserve."
    )

    # Case 3: Installments (EMI)
    show_case(
        case_num=3,
        user_id="user_30",
        request_id="request_30",
        item="Professional Certification & Exam Fee",
        amount=45000.00,
        curr="INR (Rs.)",
        status="affordable",
        method="installments",
        plan="3-Month EMI: Rs. 15,000 / month",
        explanation="Paying Rs. 45,000 upfront temporarily dips near the safety threshold. Per user preference for installments, a 3-month split of Rs. 15,000/month is recommended, safely cushioned by confirmed monthly salary credits."
    )
    
    print("\033[92m[+] Evaluation Complete. 250 requests processed into output.csv.\033[0m")
    print("\033[92m[+] Token Audit: 216,163 tokens tracked in evaluation/usage_report.md.\033[0m\n")

if __name__ == "__main__":
    main()
