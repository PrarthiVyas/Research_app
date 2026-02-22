from dotenv import load_dotenv
load_dotenv()

from crew.crew_setup import build_crew
from crew.crew_setup import extract_pdf_text
JOB_DESCRIPTION = """
We are looking for a Python developer with experience in AI, NLP,
vector databases, and REST APIs.
"""

RESUME_TEXT = """
Software Engineer with experience in Python, machine learning,
and backend development.
"""

if __name__ == "__main__":
    paper_text = extract_pdf_text("C:/Users/vyasp/OneDrive - Vantiva/Documents/Flask_learning/crewAI_research/Contribution_and_performance_of_ChatGPT.pdf")
    crew = build_crew(paper_text)
    result = crew.kickoff()

    print("\nFINAL OUTPUT\n")
    print(result)
    
    # Save to file
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("CREWAI JOB APPLICATION ASSISTANT - FINAL OUTPUT\n")
        f.write("=" * 80 + "\n\n")
        f.write(str(result))
    
    print("\n✅ Output saved to output.txt")
