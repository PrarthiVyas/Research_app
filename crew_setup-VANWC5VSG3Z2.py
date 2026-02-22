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
import os
import base64
from PIL import Image
import io
import re

def normalize_pdf_text(text: str) -> str:
    """Normalize PDF text for consistent extraction"""
    if not text:
        return ""
    
    # Convert to lowercase and strip
    text = text.lower().strip()
    
    # Normalize unicode characters
    import unicodedata
    text = unicodedata.normalize('NFKD', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page breaks and form feeds
    text = re.sub(r'[\f\r\v\x0c]', ' ', text)
    
    # Standardize quotes
    text = re.sub(r'[""''`]', '"', text)
    
    # Standardize dashes
    text = re.sub(r'[–—―]', '-', text)
    
    return text.strip()

def extract_pdf_content(pdf_path: str) -> dict:
    """
    Extract both text and images from PDF
    Returns dict with 'text' and 'images' keys
    """
    try:
        reader = PdfReader(pdf_path)
        text = []
        images = []
        
        # Create images folder if it doesn't exist
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        images_dir = os.path.join(os.path.dirname(pdf_path), f"{pdf_name}_images")
        os.makedirs(images_dir, exist_ok=True)

        for page_num, page in enumerate(reader.pages):
            # Extract text with normalization
            page_text = page.extract_text()
            if page_text:
                normalized_text = normalize_pdf_text(page_text)
                if normalized_text:  # Only add if we have meaningful text after normalization
                    text.append(f"\n=== Page {page_num + 1} ===\n{normalized_text}")
            
            # Extract images
            if '/XObject' in page.get('/Resources', {}):
                xObject = page['/Resources']['/XObject'].get_object()
                
                for obj in xObject:
                    if xObject[obj]['/Subtype'] == '/Image':
                        try:
                            # Get image data
                            image_obj = xObject[obj]
                            image_data = image_obj.get_data()
                            
                            # Convert to PIL Image
                            image = Image.open(io.BytesIO(image_data))
                            
                            # Save image
                            image_filename = f"page_{page_num + 1}_image_{len(images) + 1}.png"
                            image_path = os.path.join(images_dir, image_filename)
                            image.save(image_path)
                            
                            # Store image info
                            images.append({
                                'filename': image_filename,
                                'path': image_path,
                                'page': page_num + 1,
                                'size': image.size,
                                'description': f"Figure from page {page_num + 1}"
                            })
                            
                        except Exception as img_error:
                            print(f"Error extracting image from page {page_num + 1}: {img_error}")
                            continue

        if not text:
            raise ValueError("No text could be extracted from the PDF.")

        # Join and do final normalization
        full_text = "\n".join(text)
        normalized_full_text = normalize_pdf_text(full_text)

        return {
            'text': normalized_full_text,
            'images': images,
            'images_dir': images_dir
        }
        
    except FileNotFoundError:
        raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")


def extract_pdf_text(pdf_path: str) -> str:
    """
    Backward compatibility function - extracts only text
    """
    content = extract_pdf_content(pdf_path)
    return content['text']

def build_crew(paper_content, images_info=None) -> Crew:
    """
    Build crew with enhanced image support
    paper_content: can be string (text only) or dict (text + images)
    images_info: list of image information for visual analysis
    """
    
    # Handle both old and new formats
    if isinstance(paper_content, str):
        paper_text = paper_content
        visual_context = ""
    else:
        paper_text = paper_content.get('text', '')
        images = paper_content.get('images', [])
        visual_context = f"\n\n=== VISUAL CONTENT AVAILABLE ===\n"
        if images:
            visual_context += f"This paper contains {len(images)} figures/diagrams:\n"
            for i, img in enumerate(images, 1):
                visual_context += f"- Figure {i}: {img['description']} (Page {img['page']})\n"
            visual_context += "\nPlease reference these visual elements in your analysis when relevant.\n"

    # Agents
    reader = paper_reader_agent()
    math = math_simplifier_agent()
    implementation = implementation_agent()
    summary = summary_agent()

    # Tasks with enhanced visual context
    enhanced_paper_text = paper_text + visual_context
    
    task1 = paper_reader_task(reader, enhanced_paper_text)
    task2 = math_simplifier_task(math, enhanced_paper_text)
    task3 = implementation_task(implementation, enhanced_paper_text)
    task4 = summary_task(summary, enhanced_paper_text)

    return Crew(
        agents=[reader, math, implementation, summary],
        tasks=[task1, task2, task3, task4],
        process=Process.sequential,
        memory=False,  # Disable memory to save API calls
        verbose=True
    )
    

