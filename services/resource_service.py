"""
Resource service for OCR A-Level Computer Science AI Tutor
"""
from flask import current_app
from models.resource import Resource
from models.knowledge_base import KnowledgeBase
from services.aws_service import AWSService
from config.database_config import db
import os
import PyPDF2
import io
import docx
import re

class ResourceService:
    """Resource service class"""
    
    @staticmethod
    def create_resource(title, file, file_type, description=None, topic_id=None, is_public=True, created_by=None):
        """Create a resource"""
        # Upload file to S3
        upload_result = AWSService.upload_resource(file, topic_id)
        if not upload_result:
            current_app.logger.error(f"Error uploading resource file: {title}")
            return None
        
        # Create resource
        resource = Resource(
            title=title,
            file_type=file_type,
            description=description,
            file_url=upload_result['url'],
            file_path=upload_result['path'],
            topic_id=topic_id,
            is_public=is_public,
            created_by=created_by
        )
        
        db.session.add(resource)
        db.session.commit()
        
        # Extract content and create knowledge base entry if applicable
        if file_type in ['pdf', 'doc', 'docx', 'txt']:
            content = ResourceService.extract_content(file, file_type)
            if content:
                knowledge_base = KnowledgeBase(
                    topic_id=topic_id or 'general',
                    title=title,
                    content=content,
                    source=upload_result['url'],
                    resource_id=resource.id,
                    created_by=created_by
                )
                db.session.add(knowledge_base)
                db.session.commit()
        
        return resource
    
    @staticmethod
    def update_resource(resource_id, title=None, description=None, topic_id=None, is_public=None):
        """Update a resource"""
        resource = Resource.query.get(resource_id)
        if not resource:
            current_app.logger.error(f"Resource not found: {resource_id}")
            return None
        
        if title:
            resource.title = title
        
        if description is not None:
            resource.description = description
        
        if topic_id is not None:
            resource.topic_id = topic_id
        
        if is_public is not None:
            resource.is_public = is_public
        
        db.session.commit()
        
        # Update knowledge base entry if it exists
        knowledge_base = KnowledgeBase.query.filter_by(resource_id=resource_id).first()
        if knowledge_base:
            if title:
                knowledge_base.title = title
            
            if topic_id is not None:
                knowledge_base.topic_id = topic_id
            
            db.session.commit()
        
        return resource
    
    @staticmethod
    def delete_resource(resource_id):
        """Delete a resource"""
        resource = Resource.query.get(resource_id)
        if not resource:
            current_app.logger.error(f"Resource not found: {resource_id}")
            return False
        
        # Delete file from S3
        if resource.file_path:
            AWSService.delete_file(resource.file_path)
        
        # Delete knowledge base entry if it exists
        knowledge_base = KnowledgeBase.query.filter_by(resource_id=resource_id).first()
        if knowledge_base:
            db.session.delete(knowledge_base)
        
        # Delete resource
        db.session.delete(resource)
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_resources(topic_id=None, file_type=None, is_public=True):
        """Get resources"""
        query = Resource.query
        
        if topic_id:
            query = query.filter_by(topic_id=topic_id)
        
        if file_type:
            query = query.filter_by(file_type=file_type)
        
        if is_public is not None:
            query = query.filter_by(is_public=is_public)
        
        return query.all()
    
    @staticmethod
    def search_resources(query_string, is_public=True):
        """Search resources"""
        return Resource.search_resources(query_string, is_public)
    
    @staticmethod
    def extract_content(file, file_type):
        """Extract content from a file"""
        try:
            if file_type == 'pdf':
                return ResourceService.extract_pdf_content(file)
            elif file_type in ['doc', 'docx']:
                return ResourceService.extract_docx_content(file)
            elif file_type == 'txt':
                return file.read().decode('utf-8')
            else:
                return None
        except Exception as e:
            current_app.logger.error(f"Error extracting content from file: {e}")
            return None
    
    @staticmethod
    def extract_pdf_content(file):
        """Extract content from a PDF file"""
        try:
            # Reset file pointer to beginning
            file.seek(0)
            
            # Read PDF
            pdf_reader = PyPDF2.PdfReader(file)
            content = ""
            
            # Extract text from each page
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                content += page.extract_text() + "\n\n"
            
            # Clean up content
            content = ResourceService.clean_content(content)
            
            return content
        except Exception as e:
            current_app.logger.error(f"Error extracting content from PDF: {e}")
            return None
    
    @staticmethod
    def extract_docx_content(file):
        """Extract content from a DOCX file"""
        try:
            # Reset file pointer to beginning
            file.seek(0)
            
            # Read DOCX
            doc = docx.Document(file)
            content = ""
            
            # Extract text from each paragraph
            for para in doc.paragraphs:
                content += para.text + "\n"
            
            # Clean up content
            content = ResourceService.clean_content(content)
            
            return content
        except Exception as e:
            current_app.logger.error(f"Error extracting content from DOCX: {e}")
            return None
    
    @staticmethod
    def clean_content(content):
        """Clean up extracted content"""
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove non-printable characters
        content = re.sub(r'[^\x20-\x7E\n]', '', content)
        
        # Remove very long lines (likely garbage)
        lines = content.split('\n')
        cleaned_lines = [line for line in lines if len(line) < 1000]
        content = '\n'.join(cleaned_lines)
        
        return content
    
    @staticmethod
    def generate_presigned_url(resource_id, expiration=3600):
        """Generate a presigned URL for a resource"""
        resource = Resource.query.get(resource_id)
        if not resource or not resource.file_path:
            current_app.logger.error(f"Resource not found or has no file path: {resource_id}")
            return None
        
        return AWSService.generate_presigned_url(resource.file_path, expiration)
