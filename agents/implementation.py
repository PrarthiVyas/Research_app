from crewai import Agent
from llm.gemini_llm import get_gemini_llm

def implementation_agent():
    return Agent(
        role="Senior Machine Learning Engineer",
        goal="Translate theory into practical implementation guidance suitable for real-world systems.",
        backstory="You are a senior ML engineer who has implemented multiple research papers into production systems.You understand common implementation pitfalls, performance tradeoffs, and best practices in PyTorch and TensorFlow.",
        verbose=True,
        llm=get_gemini_llm(),
        max_iter=2,
        allow_delegation=False
    )
