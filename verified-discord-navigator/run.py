import sys
import os
import argparse

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Fix python path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.decision_engine import DecisionEngine
from core.response_builder import ResponseBuilder


def run_demo():
    print("=" * 65)
    print("      VERIFIED DISCORD NAVIGATOR — HACKATHON DEMO (CP2)")
    print("=" * 65)

    engine = DecisionEngine()

    demo_cases = [
        ("CASE 1 — CÓ MỘT NGUỒN ĐÚNG", "Workshop tối nay lúc mấy giờ?"),
        ("CASE 2 — CÓ NHIỀU NGUỒN MÂU THUẪN", "Khóa 4 nộp Gate 1 khi nào?"),
        ("CASE 3 — KHÔNG ĐỦ NGUỒN", "Tuần sau có workshop đặc biệt không?")
    ]

    for title, question in demo_cases:
        print(f"\n-----------------------------------------------------------------")
        print(f"🔹 {title}")
        print(f"❓ User hỏi: \"{question}\"")
        print(f"-----------------------------------------------------------------")

        result = engine.process_query(question=question)
        embed_dict = ResponseBuilder.build_embed_dict(result)

        print(f"STATUS         : {result.status.value}")
        print(f"CONFIDENCE     : {result.confidence:.2f} ({result.confidence_level.upper()})")
        print(f"NEEDS MOD      : {result.needs_mod}")
        print(f"\n[DISCORD EMBED OUTPUT]")
        print(f"Title          : {embed_dict['title']}")
        print(f"Description    : {embed_dict['description']}")

        print("Fields         :")
        for f in embed_dict.get("fields", []):
            print(f"  • {f['name']}: {f['value']}")

        if result.rejected_sources:
            print("\n[CÁC NGUỒN ĐÃ LOẠI]")
            for rej in result.rejected_sources:
                print(f"  ❌ [{rej.source.id}] ({rej.source.posted_at[:10]} - #{rej.source.channel_name}): {rej.reason}")

    print("\n" + "=" * 65)
    print("Demo completed successfully!")
    print("=" * 65)


def run_cli():
    print("Verified Discord Navigator Interactive CLI (Type 'exit' or 'quit' to stop)\n")
    engine = DecisionEngine()
    while True:
        try:
            user_input = input("Hỏi bot: ").strip()
            if not user_input or user_input.lower() in ["exit", "quit"]:
                break
            result = engine.process_query(question=user_input)
            embed_dict = ResponseBuilder.build_embed_dict(result)
            print(f"\n--> STATUS: {result.status.value}")
            print(f"--> TITLE: {embed_dict['title']}")
            print(f"--> ANSWER: {embed_dict['description']}")
            if result.rejected_sources:
                print("--> REJECTED SOURCES:")
                for r in result.rejected_sources:
                    print(f"    - [{r.source.id}]: {r.reason}")
            print("\n" + "-" * 50)
        except KeyboardInterrupt:
            break


def main():
    parser = argparse.ArgumentParser(description="Verified Discord Navigator CP2 Prototype Runner")
    parser.add_argument("--demo", action="store_true", help="Run pre-packaged hackathon demo cases 1, 2, and 3")
    parser.add_argument("--cli", action="store_true", help="Interactive terminal query test mode")

    args = parser.parse_args()

    if args.demo:
        run_demo()
    elif args.cli:
        run_cli()
    else:
        # Default: attempt to start Discord bot
        from bot.main import main as start_bot
        start_bot()


if __name__ == "__main__":
    main()
