#!/usr/bin/env python3
"""
LaTeX Compiler Module for APOLLO AI
Compiles LaTeX content to PDF files for display in the web app.
"""

import os
import platform
import shutil
import subprocess
import uuid
from pathlib import Path
from datetime import datetime

def compile_latex_to_pdf(latex_content, user_id, topic_code, title="OCR A-Level Computer Science Practice Paper"):
    """
    Compiles LaTeX content to PDF and saves it in a user-specific directory.
    Returns the path to the generated PDF, relative to the 'static' directory.
    
    Args:
        latex_content (str): The LaTeX code to compile
        user_id (int): User ID for organizing PDFs by user
        topic_code (str): Topic code for file naming
        title (str, optional): Paper title for file naming
    
    Returns:
        str: Path to the generated PDF relative to 'static' directory, or None if compilation failed
    """
    # Print verbose debugging information
    print(f"Starting LaTeX compilation for user {user_id}, topic {topic_code}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Platform: {platform.system()} {platform.release()}")
    # Sanitize inputs for filenames
    user_id_str = str(user_id)
    topic_code_str = topic_code.replace(".", "_").replace(" ", "")
    
    # Create a base directory for storing PDFs
    pdf_base_dir = Path("static/generated_pdfs")
    pdf_base_dir.mkdir(exist_ok=True)
    
    # Create user-specific directory
    user_dir = pdf_base_dir / user_id_str
    user_dir.mkdir(exist_ok=True)
    
    # Create unique filename based on topic and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    pdf_filename = f"{topic_code_str}_{timestamp}_{unique_id}.pdf"
    final_pdf_path = user_dir / pdf_filename
    
    # Create a temporary directory for compilation
    temp_dir = Path(f"latex_temp_{unique_id}")
    temp_dir.mkdir(exist_ok=True)
    tex_file_path = temp_dir / "temp.tex"
    
    try:
        # Process LaTeX content to handle missing images
        processed_content = latex_content
        
        # Check for image includes that might be missing
        if "\\includegraphics" in processed_content and "OCR_logo.jpg" in processed_content:
            print("Found image reference to OCR_logo.jpg - replacing with workaround")
            
            # Option 1: Comment out the problematic line
            processed_content = processed_content.replace(
                "\\includegraphics[width=0.5\\textwidth]{OCR_logo.jpg}",
                "% Image removed: OCR_logo.jpg not available\n\\vspace{2cm}"
            )
            
            # Option 2: If there are other image references, we could use a more general regex approach here
        
        # Write processed LaTeX content to file
        with tex_file_path.open("w", encoding="utf-8") as tex_file:
            tex_file.write(processed_content)
        
        # Compile LaTeX to PDF
        compile_command = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "temp.tex"
        ]
        
        # Store original directory
        original_dir = os.getcwd()
        
        # Change to the temp directory for compilation
        os.chdir(str(temp_dir))
        
        # First run
        result = subprocess.run(
            compile_command,
            capture_output=True,
            text=True,
            check=False  # Don't raise exception on error
        )
        
        if result.returncode != 0:
            print(f"LaTeX compilation error (first pass): {result.stderr}")
            # Check if the error is just the MiKTeX update warning
            if "So far, you have not checked for MiKTeX updates" in result.stderr and not "Fatal error" in result.stderr:
                print("Ignoring MiKTeX update warning and continuing compilation")
            else:
                # Continue anyway, sometimes the second pass resolves issues
                print("Continuing to second pass despite errors")
        
        # Second run for references
        result = subprocess.run(
            compile_command,
            capture_output=True,
            text=True,
            check=False  # Don't raise exception on error
        )
        
        if result.returncode != 0:
            print(f"LaTeX compilation error (second pass): {result.stderr}")
            # Check if the error is just the MiKTeX update warning
            if "So far, you have not checked for MiKTeX updates" in result.stderr and not "Fatal error" in result.stderr:
                print("Ignoring MiKTeX update warning")
        
        # Return to original directory
        os.chdir(original_dir)
        
        # Check if PDF was generated
        compiled_pdf_path = temp_dir / "temp.pdf"
        if not compiled_pdf_path.exists():
            print("No PDF was produced")
            # Try to run a direct check with the OS to ensure the file really doesn't exist
            # Sometimes file system operations can be asynchronous
            if os.path.isfile(str(compiled_pdf_path)):
                print("PDF found with direct OS check")
            else:
                return None
        
        # Move PDF to final location
        shutil.copy(str(compiled_pdf_path), str(final_pdf_path))
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        # Return the relative path for storage in database
        # This path should be relative to the static folder for use with url_for
        return f"generated_pdfs/{user_id_str}/{pdf_filename}"
    
    except Exception as e:
        print(f"Error in LaTeX compilation: {str(e)}")
        if temp_dir.exists():
            try:
                # Try to return to original directory if we're still in the temp dir
                if os.getcwd() != original_dir:
                    os.chdir(original_dir)
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(f"Error cleaning up: {str(cleanup_error)}")
        return None
