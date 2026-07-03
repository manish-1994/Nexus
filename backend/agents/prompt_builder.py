import datetime

class PromptBuilder:
    """Service to compose the final system prompt for an agent."""
    
    def __init__(self, agent):
        self.agent = agent
        self.variables = {
            "agent": agent.name if agent else "Assistant",
            "user": "User",  # Placeholder
            "conversation": "",  # Placeholder
            "workspace": "",  # Placeholder
            "memory": "",  # Placeholder
            "today": datetime.date.today().isoformat(),
            "files": "",  # Placeholder
        }

    def set_variable(self, key: str, value: str):
        self.variables[key] = value

    def build(self) -> str:
        """Renders the prompt template with current variables."""
        if not self.agent or not self.agent.prompt_template:
            template = "You are a helpful and friendly AI assistant.\n\nContext:\nToday is {{today}}."
        else:
            template = self.agent.prompt_template

        for key, value in self.variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        
        return template
