from crewai import Task

def implementation_task(agent, paper_text: str):
    return Task(
        description=f"""
        You are given the raw text of a research paper on ChatGPT and LLMs, along with the analyses from the paper reader and math simplifier tasks.

        Your task is to translate the paper's ideas into practical implementation for using LLMs in various domains.

        Specifically:
        1. Identify main components/modules needed to build applications using ChatGPT/LLMs (e.g., API integration, prompt engineering)
        2. Explain how data flows in LLM-based systems (input prompts, responses, fine-tuning if applicable)
        3. Describe how key concepts (e.g., bias mitigation, ethical use) map to code practices
        4. Provide high-level pseudocode or simplified code snippets for domain applications (health, education, etc.)
        5. Highlight common implementation pitfalls and performance considerations for LLM apps

        Do NOT summarize the paper.
        Do NOT focus on training LLMs from scratch.
        Focus on practical application development using existing LLMs.

        Research Paper Text:
        -------------------
        {paper_text}
        """,
        expected_output="""
        An implementation-focused explanation containing:
        - Component/module breakdown
        - Training and inference flow
        - Mapping from theory to code
        - Pseudocode or simplified code snippets
        - Common implementation pitfalls and optimizations
        """,
        agent=agent
    )
