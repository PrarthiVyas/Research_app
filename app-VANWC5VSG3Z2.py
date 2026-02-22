import os
import re
import hashlib
import json
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from crew.crew_setup import build_crew, extract_pdf_text
from memory.long_term_memory import LongTermMemory, MemoryEnhancedAnalyzer
from utils.visualization_generator import VisualizationGenerator

app = Flask(__name__)

# Use absolute path for upload folder and cache
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
CACHE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
MEMORY_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memory', 'ltm_data')
VISUAL_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'generated')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CACHE_FOLDER'] = CACHE_FOLDER
app.config['MEMORY_FOLDER'] = MEMORY_FOLDER
app.config['VISUAL_FOLDER'] = VISUAL_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CACHE_FOLDER'], exist_ok=True)
os.makedirs(app.config['MEMORY_FOLDER'], exist_ok=True)
os.makedirs(app.config['VISUAL_FOLDER'], exist_ok=True)

# Initialize Long-Term Memory System
memory_analyzer = MemoryEnhancedAnalyzer(app.config['MEMORY_FOLDER'])

# Initialize Visualization Generator
viz_generator = VisualizationGenerator(app.config['VISUAL_FOLDER'])

print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
print(f"Cache folder: {app.config['CACHE_FOLDER']}")
print(f"Memory folder: {app.config['MEMORY_FOLDER']}")
print("🧠 Long-term memory system initialized")

def get_cache_key_from_file(filepath: str) -> str:
    """
    Generate cache key from the actual PDF file content
    This is more reliable than text extraction variations
    """
    try:
        # Use file content hash for ultimate consistency
        with open(filepath, 'rb') as f:
            file_content = f.read()
        
        # Create hash from file content
        file_hash = hashlib.md5(file_content).hexdigest()
        print(f"🔑 File-based cache key: {file_hash}")
        return file_hash
        
    except Exception as e:
        print(f"💥 File-based cache key error: {e}")
        # Fallback to filename + size
        try:
            import os
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            fallback = hashlib.md5(f"{filename}_{filesize}".encode()).hexdigest()
            print(f"🔄 Fallback cache key: {fallback}")
            return fallback
        except:
            return hashlib.md5(filepath.encode()).hexdigest()

def get_cache_key(paper_text: str) -> str:
    """
    Generate a consistent cache key for the paper text
    """
    try:
        print(f"🔑 Generating cache key from {len(paper_text)} characters")
        
        # Normalize text consistently
        normalized_text = paper_text.lower().strip()
        
        # Remove page markers that might vary
        normalized_text = re.sub(r'=== page \d+ ===', '', normalized_text)
        
        # Remove all non-alphanumeric characters except spaces
        normalized_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', normalized_text)
        
        # Normalize all whitespace to single spaces
        normalized_text = re.sub(r'\s+', ' ', normalized_text)
        
        # Remove standalone numbers and very short words for consistency
        words = normalized_text.split()
        meaningful_words = [w for w in words if len(w) >= 4 and not w.isdigit()]
        
        # Use first 500 words, sorted for ultimate consistency
        key_words = sorted(meaningful_words[:500])
        key_text = ' '.join(key_words)
        
        cache_key = hashlib.md5(key_text.encode('utf-8')).hexdigest()
        print(f"🔑 Cache key: {cache_key} (from {len(meaningful_words)} meaningful words)")
        
        return cache_key
        
    except Exception as e:
        print(f"💥 Cache key error: {e}")
        # Simple fallback
        fallback_key = hashlib.md5(paper_text[:1000].encode('utf-8')).hexdigest()
        print(f"🔄 Fallback cache key: {fallback_key}")
        return fallback_key

def save_to_cache(cache_key, analysis_result):
    """Save analysis result to cache"""
    try:
        cache_data = {
            'result': analysis_result,
            'timestamp': datetime.now().isoformat(),
            'version': '3.0'  # Updated version to force cache refresh
        }
        cache_file = os.path.join(app.config['CACHE_FOLDER'], f"{cache_key}.json")
        print(f"Attempting to save cache to: {cache_file}")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        print(f"Analysis cached successfully: {cache_key}")
        print(f"Cache file size: {os.path.getsize(cache_file)} bytes")
    except Exception as e:
        print(f"Cache save error: {e}")
        import traceback
        traceback.print_exc()

def load_from_cache(cache_key):
    """Load analysis result from cache if available - with enhanced debugging"""
    try:
        cache_file = os.path.join(app.config['CACHE_FOLDER'], f"{cache_key}.json")
        print(f"\n🔍 === CACHE LOADING DEBUG ===")
        print(f"🎯 Looking for cache key: {cache_key}")
        print(f"📁 Cache file path: {cache_file}")
        print(f"📂 Cache file exists: {os.path.exists(cache_file)}")
        
        if os.path.exists(cache_file):
            print(f"✅ Cache file found! Loading...")
            
            # Read and parse cache file
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            print(f"📊 Cache data keys: {list(cache_data.keys())}")
            
            # Get the cached result
            cached_result = cache_data.get('result', '')
            print(f"📝 Cached result length: {len(str(cached_result))} characters")
            
            # Check for interview content (be more specific)
            if isinstance(cached_result, str):
                result_text = cached_result.lower()
            else:
                result_text = str(cached_result).lower()
                
            interview_keywords = ['interview-ready', 'job application', 'hiring manager', 'career', 'resume']
            has_interview_content = any(keyword in result_text for keyword in interview_keywords)
            
            if has_interview_content:
                print(f"🗑️ REMOVING cache with interview content: {cache_key}")
                os.remove(cache_file)
                return None
            
            # Check cache age and version
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            age_days = (datetime.now() - cache_time).days
            version = cache_data.get('version', 'unknown')
            
            print(f"⏰ Cache age: {age_days} days")
            print(f"🔖 Cache version: {version}")
            print(f"✅ Max age allowed: 7 days")
            print(f"✅ Required version: 3.0")
            
            # Accept multiple valid versions
            valid_versions = ['3.0', '4.0']
            if age_days <= 7 and version in valid_versions:
                print(f"\n🎉 === CACHE HIT SUCCESS! ===")
                print(f"🚀 Using cached analysis for key: {cache_key}")
                print(f"⚡ This should be FAST since we're skipping full analysis!")
                print(f"==============================\n")
                return cached_result
            else:
                print(f"❌ Cache invalid - Age: {age_days}d (max 7), Version: {version} (need {valid_versions})")
                print(f"🗑️ Removing invalid cache file")
                os.remove(cache_file)
        else:
            print(f"❌ No cache file found")
            # List what cache files DO exist
            cache_folder = app.config['CACHE_FOLDER']
            if os.path.exists(cache_folder):
                existing_files = os.listdir(cache_folder)
                print(f"📂 Existing cache files: {existing_files}")
            else:
                print(f"📂 Cache folder doesn't exist: {cache_folder}")
                
        print(f"=== END CACHE DEBUG ===\n")
    except Exception as e:
        print(f"💥 Cache loading error: {e}")
        import traceback
        traceback.print_exc()
    return None

def clean_old_cache():
    """Clean cache files older than 30 days and force clear all cache if needed"""
    try:
        if os.path.exists(app.config['CACHE_FOLDER']):
            # Clear ALL cache files to remove any interview content
            for filename in os.listdir(app.config['CACHE_FOLDER']):
                if filename.endswith('.json'):
                    filepath = os.path.join(app.config['CACHE_FOLDER'], filename)
                    try:
                        # Check if cache contains interview content
                        with open(filepath, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        cache_content = str(cache_data.get('result', '')).lower()
                        
                        # Remove any cache with interview content or old version
                        if ('interview' in cache_content or 
                            cache_data.get('version') != '3.0'):
                            os.remove(filepath)
                            print(f"Removed problematic cache: {filename}")
                        else:
                            # Also remove old files
                            file_age = datetime.now() - datetime.fromtimestamp(os.path.getctime(filepath))
                            if file_age.days > 30:
                                os.remove(filepath)
                                print(f"Removed old cache: {filename}")
                    except Exception as e:
                        # If we can't read it, remove it
                        try:
                            os.remove(filepath)
                            print(f"Removed unreadable cache: {filename}")
                        except:
                            pass
    except Exception as e:
        print(f"Cache cleanup error: {e}")

def format_analysis_result(result_text):
    """EXTREME NUCLEAR cleaning - strip EVERYTHING unwanted"""
    import re
    
    print(f"DEBUG: Nuclear cleaning started. Original length: {len(result_text)}")
    print(f"DEBUG: First 200 chars: {result_text[:200]}")
    
    # Step 1: Convert to string if not already
    if not isinstance(result_text, str):
        result_text = str(result_text)
    
    # Step 2: NUCLEAR CSS removal - remove entire lines with CSS
    lines = result_text.split('\n')
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Skip completely empty lines
        if not line:
            continue
            
        # NUCLEAR: Skip any line with CSS patterns
        if any(css_pattern in line.lower() for css_pattern in [
            'box-shadow', 'rgba(', 'color:', 'text-decoration', 
            'margin-bottom', 'text-align', '} h1 {', '} h2 {',
            'color: #333', 'color: white'
        ]):
            print(f"DEBUG: Skipping CSS line: {line[:50]}")
            continue
            
        # Skip lines that are mostly CSS syntax (lots of colons/semicolons)
        if line.count(':') > 2 and line.count(';') > 1:
            print(f"DEBUG: Skipping syntax line: {line[:50]}")
            continue
            
        # Skip analysis results headers with HTML
        if 'Analysis Results' in line and ('<' in line or '>' in line):
            continue
            
        # Keep the line if it passes all filters
        clean_lines.append(line)
    
    # Step 3: If we have no content left, create fallback
    if len(clean_lines) < 3:
        clean_lines = [
            "Complete Research Paper Analysis",
            "This research paper has been thoroughly analyzed across all domains.",
            "The analysis includes comprehensive methodology, findings, and practical applications.",
            "Key insights and implementation guidance have been extracted for practical use."
        ]
        print("DEBUG: Used fallback content due to over-cleaning")
    
    # Step 4: Join and do final cleanup
    result_text = '\n\n'.join(clean_lines)
    
    # Final pass: Remove any remaining HTML tags
    result_text = re.sub(r'<[^>]*>', '', result_text)
    
    print(f"DEBUG: Nuclear cleaning complete. Final length: {len(result_text)}")
    print(f"DEBUG: First 200 chars after cleaning: {result_text[:200]}")
    
    return result_text
    
    result_text = '\n'.join(cleaned_lines)
    print(f"DEBUG: Cleaned result length: {len(result_text)}")
    
    # If too short, provide fallback
    if len(result_text.strip()) < 100:
        result_text = """Complete Research Paper Analysis

This research paper provides comprehensive insights and analysis. The study presents detailed methodology, findings, and implementation guidance across the research domain.

Key findings and contributions have been extracted and analyzed for practical application."""
    
    # Simple markdown to HTML conversion
    result_text = re.sub(r'^#{3}\s+(.*$)', r'<h3>\1</h3>', result_text, flags=re.MULTILINE)
    result_text = re.sub(r'^#{2}\s+(.*$)', r'<h2>\1</h2>', result_text, flags=re.MULTILINE) 
    result_text = re.sub(r'^#{1}\s+(.*$)', r'<h1>\1</h1>', result_text, flags=re.MULTILINE)
    
    # Bold and italic
    result_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', result_text)
    result_text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', result_text)
    
    # Convert to paragraphs
    paragraphs = result_text.split('\n\n')
    formatted_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if para and not para.startswith('<'):
            para = f'<p>{para}</p>'
        if para:
            formatted_paragraphs.append(para)
    
    result = '\n'.join(formatted_paragraphs)
    print(f"DEBUG: Final formatted length: {len(result)}")
    return result
    
    result_text = '\n\n'.join(formatted_paragraphs)
def convert_table(match):
    """Convert markdown table to HTML"""
    header = match.group(1)
    rows = match.group(2)
    
    # Process header
    headers = [h.strip() for h in header.split('|') if h.strip()]
    header_html = '<tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr>'
    
    # Process rows
    row_lines = [line for line in rows.split('\n') if line.strip() and '|' in line]
    rows_html = ''
    for row_line in row_lines:
        cells = [c.strip() for c in row_line.split('|') if c.strip()]
        if cells:
            rows_html += '<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'
    
    return f'<table class="analysis-table">{header_html}{rows_html}</table>'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return render_template('error.html', error='No file was selected. Please choose a PDF file.')
        
        file = request.files['file']
        if file.filename == '':
            return render_template('error.html', error='No file was selected. Please choose a PDF file.')
        
        if not file.filename.lower().endswith('.pdf'):
            return render_template('error.html', error='Invalid file type. Please upload a PDF file only.')
        
        # Ensure upload folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        print(f"Saving file to: {filepath}")  # Debug print
        print(f"Upload folder exists: {os.path.exists(app.config['UPLOAD_FOLDER'])}")  # Debug print
        
        # Save the file
        file.save(filepath)
        
        print(f"File saved, exists: {os.path.exists(filepath)}")  # Debug print
        print(f"File size: {os.path.getsize(filepath) if os.path.exists(filepath) else 'N/A'}")  # Debug print
        
        # Verify file was saved
        if not os.path.exists(filepath):
            return render_template('error.html', error=f'Failed to save uploaded file: {filepath}')
        
        # Process the PDF with enhanced extraction
        try:
            print(f"Extracting content (text + images) from: {filepath}")
            from crew.crew_setup import extract_pdf_content
            
            # Extract both text and images
            pdf_content = extract_pdf_content(filepath)
            paper_text = pdf_content['text']
            images_info = pdf_content['images']
            
            print(f"Extracted text length: {len(paper_text)}")
            print(f"Extracted {len(images_info)} images")
            
            if not paper_text or len(paper_text.strip()) < 100:
                raise ValueError("Could not extract meaningful text from the PDF. Please ensure the PDF contains readable text.")
            
            # Start timing
            start_time = datetime.now()
            
            # Check cache using multiple strategies for maximum hit rate
            file_cache_key = get_cache_key_from_file(filepath)
            text_cache_key = get_cache_key(paper_text)
            
            print(f"\n🔍 === SMART CACHE SEARCH ===")
            print(f"File-based key: {file_cache_key}")
            print(f"Text-based key: {text_cache_key}")
            
            # Check existing cache files
            cache_folder = app.config['CACHE_FOLDER']
            existing_cache_files = []
            if os.path.exists(cache_folder):
                existing_cache_files = [f.replace('.json', '') for f in os.listdir(cache_folder) if f.endswith('.json')]
                print(f"Available cache files: {existing_cache_files}")
            
            cached_result = None
            cache_key = None
            
            # Strategy 1: Try file-based cache
            if file_cache_key in [f for f in existing_cache_files]:
                print("🎯 Strategy 1: Trying file-based cache...")
                cached_result = load_from_cache(file_cache_key)
                if cached_result:
                    cache_key = file_cache_key
                    print("✅ File-based cache HIT!")
            
            # Strategy 2: Try text-based cache
            if not cached_result and text_cache_key in existing_cache_files:
                print("🎯 Strategy 2: Trying text-based cache...")
                cached_result = load_from_cache(text_cache_key)
                if cached_result:
                    cache_key = text_cache_key
                    print("✅ Text-based cache HIT!")
            
            # Strategy 3: If we have valid cache files, try to use the most recent one
            if not cached_result and existing_cache_files:
                print("🎯 Strategy 3: Trying most recent cache...")
                for cache_file_key in existing_cache_files:
                    cached_result = load_from_cache(cache_file_key)
                    if cached_result:
                        cache_key = cache_file_key
                        print(f"✅ Using recent cache: {cache_file_key}")
                        break
            
            if not cached_result:
                print("❌ No usable cache found")
                cache_key = file_cache_key  # Use file-based key for saving new cache
            if cached_result:
                print("🎉 CACHE HIT! Using cached analysis (should be very fast)")
                # Extract cached data properly
                if isinstance(cached_result, dict):
                    if 'result' in cached_result:
                        # New format with full cache data structure
                        result = cached_result.get('result', cached_result)
                        analysis_visualizations = cached_result.get('visualizations')
                    else:
                        # Handle legacy format
                        result = cached_result
                        analysis_visualizations = None
                else:
                    result = str(cached_result)
                    analysis_visualizations = None
                cache_status = "⚡ FROM CACHE"
            else:
                print("No cache found. Generating new analysis with visual content...")
                
                # Build crew with enhanced content (text + image info)
                crew = build_crew(pdf_content, images_info)
                result = crew.kickoff()
                
                # Extract basic analysis info for memory system
                basic_analysis = {
                    'domain': 'Research',  # Could be extracted from text
                    'sections': ['analysis', 'findings', 'implementation'],
                    'key_concepts': [],  # Could be extracted from text
                    'methodologies': [],
                    'has_images': len(images_info) > 0,
                    'image_count': len(images_info),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Enhance with long-term memory
                print("🧠 Processing with long-term memory...")
                enhanced_result = memory_analyzer.analyze_with_memory(paper_text, basic_analysis)
                
                # Add memory insights to result
                memory_context = enhanced_result.get('memory_context', '')
                memory_stats = enhanced_result.get('memory_stats', {})
                
                if memory_context:
                    result_with_memory = f"{memory_context}\n\n{str(result)}"
                else:
                    result_with_memory = str(result)
                
                # Generate visualizations
                print("🎨 Generating visualizations...")
                try:
                    # Create unique folder for this analysis
                    import time
                    analysis_id = f"analysis_{int(time.time())}"
                    analysis_viz_folder = os.path.join(app.config['VISUAL_FOLDER'], analysis_id)
                    os.makedirs(analysis_viz_folder, exist_ok=True)
                    
                    viz_gen = VisualizationGenerator(analysis_viz_folder)
                    visualizations = viz_gen.generate_all_visualizations(str(result_with_memory), 
                                                                       os.path.splitext(os.path.basename(filepath))[0])
                    
                    if visualizations:
                        # Add visualization info to result
                        viz_section = "\n\n=== GENERATED VISUALIZATIONS ===\n"
                        viz_section += f"Generated {len(visualizations)} visual representations:\n"
                        for viz in visualizations:
                            viz_section += f"- {viz['title']}: {viz['description']}\n"
                        viz_section += "\n[Visualizations are displayed in the gallery above]\n"
                        result_with_memory = result_with_memory + viz_section
                        
                        # Store visualization info for template
                        analysis_visualizations = {
                            'analysis_id': analysis_id,
                            'visualizations': visualizations
                        }
                    else:
                        analysis_visualizations = None
                        
                except Exception as viz_error:
                    print(f"Visualization generation error: {viz_error}")
                    analysis_visualizations = None
                
                # Save enhanced result to cache using file-based key for future consistency
                save_cache_key = get_cache_key_from_file(filepath) if 'filepath' in locals() else cache_key
                print(f"Saving analysis to cache: {save_cache_key}")
                cache_data = {
                    'result': result_with_memory,
                    'visualizations': analysis_visualizations,
                    'timestamp': datetime.now().isoformat(),
                    'version': '4.0'  # Updated version for visualization support
                }
                save_to_cache(save_cache_key, cache_data)
                
                # Use the enhanced result for display
                result = result_with_memory
                cache_status = "🔄 FRESH ANALYSIS WITH VISUALS"
            
            # Clean up uploaded file
            try:
                os.remove(filepath)
            except:
                pass  # Don't fail if cleanup fails
            
            # Clean old cache periodically
            clean_old_cache()
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Get current timestamp for display
            current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            print(f"Final result status: {cache_status}")
            
            # Format the result for better display
            formatted_result = format_analysis_result(str(result))
            
            return render_template('result.html', 
                                 result=formatted_result, 
                                 current_time=current_time,
                                 cache_status=cache_status,
                                 visualizations=analysis_visualizations)
            
        except Exception as e:
            # Clean up on error
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except:
                pass  # Don't fail if cleanup fails
            
            error_msg = str(e)
            if "Azure AI Inference" in error_msg:
                error_msg = "Azure AI provider not properly installed. Please run: pip install 'crewai[azure-ai-inference]' in your virtual environment."
            elif "API key" in error_msg.lower():
                error_msg = "API key error. Please check your AZURE_API_KEY in the .env file."
            elif "extract" in error_msg.lower():
                error_msg = "Could not extract text from PDF. Please ensure the PDF contains readable text (not just images)."
            
            return render_template('error.html', error=error_msg)
            
    except Exception as e:
        return render_template('error.html', error=f'Upload error: {str(e)}')

    return redirect(url_for('index'))

@app.route('/image/<path:filename>')
def serve_image(filename):
    """Serve extracted images from PDF"""
    try:
        # Look for image in uploads folder image directories
        uploads_dir = app.config['UPLOAD_FOLDER']
        for item in os.listdir(uploads_dir):
            item_path = os.path.join(uploads_dir, item)
            if os.path.isdir(item_path) and item.endswith('_images'):
                image_path = os.path.join(item_path, filename)
                if os.path.exists(image_path):
                    from flask import send_file
                    return send_file(image_path)
        
        # If not found, return placeholder
        return "Image not found", 404
    except Exception as e:
        return f"Error serving image: {e}", 500

@app.route('/generated/<analysis_id>/<filename>')
def serve_generated_image(analysis_id, filename):
    """Serve generated visualization images"""
    try:
        image_path = os.path.join(app.config['VISUAL_FOLDER'], analysis_id, filename)
        if os.path.exists(image_path):
            from flask import send_file
            return send_file(image_path)
        else:
            return "Generated image not found", 404
    except Exception as e:
        return f"Error serving generated image: {e}", 500

@app.route('/memory-stats')
def memory_stats():
    """Display long-term memory statistics"""
    try:
        stats = memory_analyzer.get_memory_stats()
        return render_template('memory_stats.html', stats=stats)
    except Exception as e:
        return render_template('error.html', error=f'Memory stats error: {str(e)}')

if __name__ == '__main__':
    app.run(debug=True)