class CustomServiceAgent:
    def __init__(self, agent_provider):
        self.agent_provider = agent_provider

    def chat(self, chat_request):
         agent_provider.message.create(
            model="deepseek-v4-flash",
#           max_tokens=1024,
            user_message=chat_request.user_message)