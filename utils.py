import os
import logging
from datetime import datetime
from typing import List
import requests
from PIL import Image
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

logger = logging.getLogger(__name__)

def create_pdf_report(content: str, image_urls: List[str], language: str, output_path: str):
    """Create PDF report with images"""
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        doc = SimpleDocDocument(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        title = f"Financial Market Summary - {datetime.now().strftime('%Y-%m-%d')} ({language})"
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Content - Clean up HTML-like formatting
        cleaned_content = content.replace('<br>', '\n').replace('<p>', '').replace('</p>', '\n\n')
        
        for paragraph in cleaned_content.split('\n\n'):
            if paragraph.strip():
                story.append(Paragraph(paragraph.strip(), styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Add images
        for i, img_url in enumerate(image_urls[:2]):
            try:
                response = requests.get(img_url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content))
                    
                    # Resize image if too large
                    img.thumbnail((400, 300), Image.Resampling.LANCZOS)
                    
                    img_path = f"temp_chart_{i}_{datetime.now().strftime('%H%M%S')}.png"
                    img.save(img_path)
                    
                    # Add image to PDF
                    story.append(Spacer(1, 12))
                    story.append(RLImage(img_path, width=min(400, img.width), height=min(300, img.height)))
                    story.append(Spacer(1, 12))
                    
                    # Clean up temp file
                    os.remove(img_path)
            except Exception as e:
                logger.error(f"Error adding image to PDF: {e}")
        
        doc.build(story)
        logger.info(f"PDF report created: {output_path}")
        
    except Exception as e:
        logger.error(f"Error creating PDF report: {e}")

def extract_image_urls_from_text(text: str) -> List[str]:
    """Extract image URLs from text using regex"""
    import re
    urls = re.findall(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\.(?:jpg|jpeg|png|gif|webp)', 
        str(text)
    )
    return urls

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for cross-platform compatibility"""
    import re
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def ensure_directory_exists(directory: str):
    """Ensure directory exists, create if not"""
    os.makedirs(directory, exist_ok=True)
