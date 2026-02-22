from crewai import Crew, Process
from agents.math_simplifier import math_simplifier_agent
from agents.implementation import implementation_agent
from agents.paper_reader import paper_reader_agent
from agents.summary import summary_agent
from tasks.paper_reader_task import paper_reader_task
from tasks.summary_task import summary_task
from tasks.math_simplifier_task import math_simplifier_task
from tasks.implementation_task import implementation_task
from pypdf import PdfReader

def extract_pdf_text(pdf_path: str) -> str:
    try:
        reader = PdfReader(pdf_path)
        text = []

        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)

        if not text:
            raise ValueError("No text could be extracted from the PDF.")

        return "\n".join(text)
    except FileNotFoundError:
        raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")

def build_crew(paper_text: str) -> Crew:

    # Agents
    reader = paper_reader_agent()
    math = math_simplifier_agent()
    implementation = implementation_agent()
    summary = summary_agent()

    # Tasks
    task1 = paper_reader_task(reader, paper_text)
    task2 = math_simplifier_task(math, paper_text)
    task3 = implementation_task(implementation, paper_text)
    task4 = summary_task(summary,paper_text)

    return Crew(
        agents=[reader, math, implementation, summary],
        tasks=[task1, task2, task3, task4],
        process=Process.sequential,
        memory=False,  # Disable memory to save API calls
        verbose=True
    )
    

