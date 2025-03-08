"""
AWS service for OCR A-Level Computer Science AI Tutor
"""
from flask import current_app, g
from config.aws_config import aws_config
import os
import uuid
from werkzeug.utils import secure_filename

class AWSService:
    """AWS service class"""
    
    @staticmethod
    def get_aws():
        """Get AWS instance"""
        if 'aws' not in g:
            g.aws = aws_config
        return g.aws
    
    @staticmethod
    def upload_file(file, folder='', public=True):
        """Upload a file to S3 bucket"""
        aws_instance = AWSService.get_aws()
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        
        # Add random prefix to avoid filename collisions
        prefix = str(uuid.uuid4())[:8]
        filename = f"{prefix}_{filename}"
        
        # Set ACL
        acl = 'public-read' if public else 'private'
        
        # Upload file
        file_url = aws_instance.upload_file_to_s3(file, folder, acl)
        
        if not file_url:
            current_app.logger.error(f"Error uploading file to S3: {filename}")
            return None
        
        return {
            'filename': filename,
            'url': file_url,
            'path': f"{folder}/{filename}" if folder else filename
        }
    
    @staticmethod
    def upload_resource(file, topic_id=None):
        """Upload a resource file to S3 bucket"""
        # Determine folder based on topic_id
        folder = f"resources/{topic_id}" if topic_id else "resources"
        
        # Upload file
        return AWSService.upload_file(file, folder)
    
    @staticmethod
    def delete_file(file_path):
        """Delete a file from S3 bucket"""
        aws_instance = AWSService.get_aws()
        return aws_instance.delete_file_from_s3(file_path)
    
    @staticmethod
    def get_file(file_path):
        """Get a file from S3 bucket"""
        aws_instance = AWSService.get_aws()
        return aws_instance.get_file_from_s3(file_path)
    
    @staticmethod
    def generate_presigned_url(file_path, expiration=3600):
        """Generate a presigned URL for a file in S3 bucket"""
        aws_instance = AWSService.get_aws()
        return aws_instance.generate_presigned_url(file_path, expiration)
    
    @staticmethod
    def list_resources(topic_id=None):
        """List resources in S3 bucket"""
        aws_instance = AWSService.get_aws()
        
        # Determine folder based on topic_id
        folder = f"resources/{topic_id}" if topic_id else "resources"
        
        # List files
        files = aws_instance.list_files_in_s3(folder)
        
        # Filter out directories
        files = [f for f in files if not f.endswith('/')]
        
        return files
    
    @staticmethod
    def get_file_extension(filename):
        """Get file extension"""
        return os.path.splitext(filename)[1].lower()
    
    @staticmethod
    def is_allowed_file(filename, allowed_extensions=None):
        """Check if file is allowed"""
        if not allowed_extensions:
            allowed_extensions = {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.csv', '.jpg', '.jpeg', '.png', '.gif'}
        
        return AWSService.get_file_extension(filename) in allowed_extensions
    
    @staticmethod
    def create_bucket_if_not_exists():
        """Create S3 bucket if it doesn't exist"""
        aws_instance = AWSService.get_aws()
        
        # Check if bucket exists
        if not aws_instance.bucket_exists():
            # Create bucket
            if aws_instance.create_bucket():
                current_app.logger.info(f"Created S3 bucket: {aws_instance.s3_bucket_name}")
                return True
            else:
                current_app.logger.error(f"Error creating S3 bucket: {aws_instance.s3_bucket_name}")
                return False
        
        return True
