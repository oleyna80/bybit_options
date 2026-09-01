#!/usr/bin/env python3
"""
Скрипт-генератор промптов для работы AI-агентов (Cursor, Claude, ChatGpt) с Bybit Trading Skill.
Считывает последний сгенерированный Risk Report (reports/latest_analysis.md)
и добавляет к нему директиву на инициализацию навыка Bybit.

Использование:
    python scripts/ai_hedge_assistant.py
    (Текст будет выведен в консоль. Скопируйте его и отправьте вашему ИИ-ассистенту)
"""

import os
import sys

def get_latest_report():
    # Resolve the project root dynamically based on script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    report_path = os.path.join(project_root, "reports", "latest_analysis.md")
    
    if not os.path.exists(report_path):
        print(f"Error: {report_path} not found. Please run 'python main.py' from the project root first.", file=sys.stderr)
        return None
    
    with open(report_path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    report_content = get_latest_report()
    if not report_content:
        sys.exit(1)

    prompt = f"""Please read https://raw.githubusercontent.com/bybit-exchange/skills/main/SKILL.md, save it as a skill, and help me trade on Bybit.

I need you to act as a Trading Expert. Below is the latest portfolio risk analysis report from my Bybit Options risk engine.

Please:
1. Review my current Delta, Margin, and Theta exposures.
2. Formulate a hedging strategy if my Delta is too high or if there are any critical warnings.
3. Use the Bybit skill to check the current market prices (orderbox or option board).
4. Propose the exact trades (limit orders) to execute, and EXPLICITLY ask for my confirmation before executing them via the skill.

=== LATEST ANALYSIS REPORT ===
{report_content}
=============================
"""
    
    # Выводим с визуальным разделителем для удобства копирования
    print("\n" + "="*80)
    print("COPY THE TEXT BELOW AND PASTE IT TO YOUR AI ASSISTANT (CURSOR / CLAUDE / CHATGPT):")
    print("="*80 + "\n")
    print(prompt)
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
