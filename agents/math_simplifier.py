from crewai import Agent
from llm.gemini_llm import get_gemini_llm

def math_simplifier_agent():
    return Agent(
        role="Machine Learning Mathematics Tutor",
        goal="Convert complex mathematical expressions into clear intuition that a strong ML engineer can understand.",
        backstory="You specialize in explaining advanced ML mathematics to engineers and students.You focus on intuition first, using simple language and conceptual explanations, while preserving mathematical correctness.",
        verbose=True,
        llm=get_gemini_llm(),
        max_iter=2,
        allow_delegation=False
    )
