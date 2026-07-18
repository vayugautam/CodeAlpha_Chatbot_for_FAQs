from chatbot import FAQChatbot

def run_cli():
    print("Loading FAQ Chatbot...")
    bot = FAQChatbot()
    print("Chatbot is ready!")
    print("Type 'exit' or 'quit' to end the conversation.\n")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            
            if not user_input.strip():
                continue
                
            response = bot.get_best_answer(user_input)
            print(f"Bot: {response}\n")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    run_cli()
