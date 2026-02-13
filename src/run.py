import logging
import argparse
import sys
from agent.counsellor_agent import CounsellorAgent

logger = logging.getLogger("tnea_ai.cli")


def main():
    parser = argparse.ArgumentParser(description='TNEA AI Counsellor CLI')
    parser.add_argument('--mode', '-m', choices=['cli', 'api', 'batch'], default='cli',
                        help='Run mode: cli (interactive), api (server), batch (script)')
    args = parser.parse_args()

    logger.info("Initializing TNEA AI Counsellor... (Training models on startup)")
    try:
        agent = CounsellorAgent()
    except Exception as e:
        logger.error(f"Error initializing agent: {e}")
        return

    if args.mode == 'cli':
        run_cli_mode(agent)
    elif args.mode == 'api':
        run_api_mode(agent)
    elif args.mode == 'batch':
        run_batch_mode(agent)


def run_cli_mode(agent):
    """Run the application in interactive CLI mode"""
    print("\n" + "="*60)
    print("🎓 Welcome to TNEA AI Expert Counsellor - Advanced Edition!")
    print("I can help you with:")
    print("  • Percentile & Rank Prediction")
    print("  • College Suggestions based on location and preferences")
    print("  • Trend Analysis and cutoff predictions")
    print("  • Choice-Filling Strategy for counselling")
    print("  • Career Planning and Skill Guidance")
    print("  • Management Quota Information")
    print("="*60 + "\n")

    print("💡 Tip: You can enter your cutoff mark directly (e.g., '195') for instant rank prediction!")
    print("💡 Tip: Ask about colleges in specific districts (e.g., 'colleges in Coimbatore')")
    print("💡 Tip: Ask for choice-filling strategy (e.g., 'strategy for rank 5000')")

    while True:
        try:
            user_input = input("\n📝 You: ").strip()
            if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                print("🎓 TNEA AI: All the best for your counselling! Goodbye.")
                break
            
            if not user_input:
                continue

            print("🎓 TNEA AI: ", end="", flush=True)
            
            if hasattr(agent, 'process_query_stream'):
                for chunk in agent.process_query_stream(user_input):
                    print(chunk, end="", flush=True)
                print()
            else:
                response = agent.process_query(user_input)
                print(f"{response}")

        except KeyboardInterrupt:
            print("\n\n👋 Exiting gracefully...")
            break
        except EOFError:
            print("\n\n👋 Session ended.")
            break
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            print(f"\n⚠️ An error occurred: {e}")


def run_api_mode(agent):
    """Run the application in API server mode"""
    print("🔧 API mode not yet implemented. Starting CLI mode instead...")
    run_cli_mode(agent)


def run_batch_mode(agent):
    """Run the application in batch processing mode"""
    print("🔧 Batch mode not yet implemented. Starting CLI mode instead...")
    run_cli_mode(agent)


if __name__ == "__main__":
    main()
