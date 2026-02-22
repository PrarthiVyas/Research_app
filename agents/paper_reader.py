from crewai import Agent
from llm.gemini_llm import get_gemini_llm

def paper_reader_agent():
    return Agent(
        role="Machine Learning Research Analyst",
        goal="Extract the true intent and contributions of the research paper without interpretation or opinion.",
        backstory="You are an experienced ML researcher who regularly reviews papers for top-tier conferences like NeurIPS, ICML, and ICLR.Your strength lies in quickly identifying a paper’s problem statement, key contributions, architecture, and evaluation setup — without oversimplifying or hallucinating details.",
        verbose=True,
        llm=get_gemini_llm(),
        max_iter=2,
        allow_delegation=False
    )
