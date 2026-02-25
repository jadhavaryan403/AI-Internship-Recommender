import fitz 
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF using block-based extraction to handle multi-column layouts.
    Args:
        pdf_path (str): Path to the PDF file   
    Returns:
        str: Extracted text from all pages
    """
    try:
        doc = fitz.open(pdf_path)
        full_text = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("blocks")
            
            sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
            
            page_text = []
            for block in sorted_blocks:
                text = block[4].strip()
                if text:
                    page_text.append(text)
            
            full_text.append("\n".join(page_text))
        
        doc.close()
        
        extracted_text = "\n\n".join(full_text)
        logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF")
        
        return extracted_text
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise


def clean_extracted_text(text):
    """
    Clean extracted text by removing excessive whitespace and normalizing line breaks.
    Args:
        text (str): Raw extracted text  
    Returns:
        str: Cleaned text
    """
    import re
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    return text.strip()


