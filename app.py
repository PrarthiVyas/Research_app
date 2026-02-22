from flask import Flask, request, render_template, redirect, url_for
import os
from werkzeug.utils import secure_filename
from crew.crew_setup import build_crew, extract_pdf_text

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the PDF
        try:
            paper_text = extract_pdf_text(filepath)
            crew = build_crew(paper_text)
            result = crew.kickoff()
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return render_template('result.html', result=str(result))
        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            return render_template('error.html', error=str(e))
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Disable the auto-reloader to avoid restarts triggered by system file changes
    # (useful on Windows where antivirus/OS updates touch Python stdlib files).
    app.run(debug=True, use_reloader=False)