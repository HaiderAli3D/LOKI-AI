"""
AWS configuration for OCR A-Level Computer Science AI Tutor
"""
import os
import boto3
from botocore.exceptions import ClientError

class AWSConfig:
    """AWS configuration class"""
    
    def __init__(self, app=None):
        """Initialize AWS configuration"""
        self.app = app
        
        # AWS credentials
        self.access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        self.secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.region = os.environ.get('AWS_REGION', 'eu-west-2')
        
        # S3 configuration
        self.s3_bucket_name = os.environ.get('S3_BUCKET_NAME')
        self.s3_location = os.environ.get('S3_LOCATION', f'https://{self.s3_bucket_name}.s3.{self.region}.amazonaws.com/')
        
        # AWS clients
        self.s3_client = None
        self.s3_resource = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize AWS with Flask app"""
        self.app = app
        
        # Initialize AWS clients
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region
        )
        
        self.s3_resource = boto3.resource(
            's3',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region
        )
        
        # Add AWS to Flask app context
        app.extensions['aws'] = self
        
        return self
    
    def upload_file_to_s3(self, file, folder='', acl='public-read'):
        """Upload a file to S3 bucket"""
        try:
            # Generate file path
            file_path = f"{folder}/{file.filename}" if folder else file.filename
            
            # Upload file
            self.s3_client.upload_fileobj(
                file,
                self.s3_bucket_name,
                file_path,
                ExtraArgs={
                    'ACL': acl,
                    'ContentType': file.content_type
                }
            )
            
            # Return file URL
            return f"{self.s3_location}{file_path}"
        except Exception as e:
            self.app.logger.error(f"Error uploading file to S3: {e}")
            return None
    
    def delete_file_from_s3(self, file_path):
        """Delete a file from S3 bucket"""
        try:
            self.s3_client.delete_object(
                Bucket=self.s3_bucket_name,
                Key=file_path
            )
            return True
        except Exception as e:
            self.app.logger.error(f"Error deleting file from S3: {e}")
            return False
    
    def get_file_from_s3(self, file_path):
        """Get a file from S3 bucket"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.s3_bucket_name,
                Key=file_path
            )
            return response['Body'].read()
        except Exception as e:
            self.app.logger.error(f"Error getting file from S3: {e}")
            return None
    
    def list_files_in_s3(self, folder=''):
        """List files in S3 bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket_name,
                Prefix=folder
            )
            
            if 'Contents' in response:
                return [item['Key'] for item in response['Contents']]
            return []
        except Exception as e:
            self.app.logger.error(f"Error listing files in S3: {e}")
            return []
    
    def generate_presigned_url(self, file_path, expiration=3600):
        """Generate a presigned URL for a file in S3 bucket"""
        try:
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.s3_bucket_name,
                    'Key': file_path
                },
                ExpiresIn=expiration
            )
        except Exception as e:
            self.app.logger.error(f"Error generating presigned URL: {e}")
            return None
    
    def create_bucket(self, bucket_name=None):
        """Create an S3 bucket"""
        bucket_name = bucket_name or self.s3_bucket_name
        
        try:
            self.s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': self.region
                }
            )
            return True
        except Exception as e:
            self.app.logger.error(f"Error creating S3 bucket: {e}")
            return False
    
    def bucket_exists(self, bucket_name=None):
        """Check if an S3 bucket exists"""
        bucket_name = bucket_name or self.s3_bucket_name
        
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False
            self.app.logger.error(f"Error checking if S3 bucket exists: {e}")
            return False

# Create AWS configuration instance
aws_config = AWSConfig()
