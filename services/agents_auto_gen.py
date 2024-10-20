import autogen

class StrategyAnalysisAgent:
    def __init__(self):
        self.config_list = autogen.config_list_from_json(
            "OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
            },
        )
        self.assistant = autogen.AssistantAgent(
            name="Strategy_Analyst",
            llm_config={
                "config_list": self.config_list,
            },
        )
        self.user_proxy = autogen.UserProxyAgent(
            name="User_Proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config={"work_dir": "coding"},
        )

    async def analyze_strategy(self, strategy_data: dict) -> str:
        """
        Analyze the given strategy data and provide recommendations.
        """
        prompt = f"""
        Analyze the following options strategy data and provide recommendations:
        {strategy_data}
        
        Please consider:
        1. The potential profit and loss scenarios
        2. The break-even points
        3. The maximum risk and reward
        4. Any market conditions that would favor this strategy
        
        Provide a concise analysis and recommendation in 3-5 sentences.
        End your response with TERMINATE.
        """
        
        self.user_proxy.initiate_chat(self.assistant, message=prompt)
        
        # Extract the last message from the assistant
        last_message = self.user_proxy.chat_messages[self.assistant][-1]["content"]
        
        # Remove the TERMINATE string from the end of the message
        analysis = last_message.replace("TERMINATE", "").strip()
        
        return analysis
