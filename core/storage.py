import os
import uuid
from io import BytesIO
from minio import Minio
from minio.error import S3Error

from config import Config

class StorageError(Exception):
    """Base exception for storage-related errors."""
    pass

class StorageConnectionError(StorageError):
    """Exception raised for connection errors."""
    pass

class StorageOperationError(StorageError):
    """Exception raised for operation errors."""
    pass

class StorageService:
    """Service for handling file storage operations using MinIO."""
    
    def __init__(self):
        """Initialize the storage service with MinIO connection."""
        try:
            self.client = Minio(
                endpoint=Config.MINIO_ENDPOINT,
                access_key=Config.MINIO_ACCESS_KEY,
                secret_key=Config.MINIO_SECRET_KEY,
                secure=Config.MINIO_SECURE
            )
            self.bucket_name = Config.MINIO_BUCKET
            
            # Ensure bucket exists
            self._ensure_bucket_exists()
        except S3Error as e:
            raise StorageConnectionError(f"Failed to connect to MinIO: {str(e)}")
        except Exception as e:
            raise StorageConnectionError(f"Unexpected error initializing storage: {str(e)}")
    
    def _ensure_bucket_exists(self):
        """Ensure the configured bucket exists, create it if it doesn't."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise StorageOperationError(f"Failed to ensure bucket exists: {str(e)}")
    
    def upload_file(self, file_data, content_type=None):
        """
        Upload a file to storage.
        
        Args:
            file_data: The file data to upload
            content_type: Optional MIME type
            
        Returns:
            dict: Information about the uploaded file
        """
        try:
            # Generate a unique ID for the file
            file_id = str(uuid.uuid4())
            
            # Get file details
            if hasattr(file_data, 'read'):
                # It's a file-like object (from request.files)
                file_content = file_data.read()
                original_filename = file_data.filename
                content_type = content_type or file_data.content_type or 'application/octet-stream'
            else:
                # It's raw data
                file_content = file_data
                original_filename = "file_" + file_id
                content_type = content_type or 'application/octet-stream'
            
            # Create a BytesIO object from the file content
            file_stream = BytesIO(file_content)
            file_size = len(file_content)
            
            # Upload to MinIO
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_id,
                data=file_stream,
                length=file_size,
                content_type=content_type
            )
            
            # Return file information
            return {
                "id": file_id,
                "original_filename": original_filename,
                "content_type": content_type,
                "size": file_size,
                "data": file_content  # Include raw data for immediate use
            }
        except S3Error as e:
            raise StorageOperationError(f"Failed to upload file: {str(e)}")
        except Exception as e:
            raise StorageOperationError(f"Unexpected error uploading file: {str(e)}")
    
    def download_file(self, file_id):
        """
        Download a file from storage.
        
        Args:
            file_id: ID of the file to download
            
        Returns:
            BytesIO: File data as a BytesIO object
        """
        try:
            response = self.client.get_object(self.bucket_name, file_id)
            return response
        except S3Error as e:
            raise StorageOperationError(f"Failed to download file {file_id}: {str(e)}")
    
    def delete_file(self, file_id):
        """
        Delete a file from storage.
        
        Args:
            file_id: ID of the file to delete
            
        Returns:
            bool: True if successful
        """
        try:
            self.client.remove_object(self.bucket_name, file_id)
            return True
        except S3Error as e:
            raise StorageOperationError(f"Failed to delete file {file_id}: {str(e)}")
        except Exception as e:
            raise StorageOperationError(f"Unexpected error deleting file: {str(e)}")
    
    def get_file_info(self, file_id):
        """
        Get information about a file.
        
        Args:
            file_id: ID of the file
            
        Returns:
            dict: File metadata
        """
        try:
            # Get object stats
            stat = self.client.stat_object(self.bucket_name, file_id)
            
            # Extract metadata
            metadata = {
                "id": file_id,
                "size": stat.size,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified.isoformat(),
                "etag": stat.etag
            }
            
            # Extract custom metadata if available
            if hasattr(stat, 'metadata') and stat.metadata:
                if 'X-Amz-Meta-Original-Filename' in stat.metadata:
                    metadata["original_filename"] = stat.metadata['X-Amz-Meta-Original-Filename']
                
            return metadata
        except S3Error as e:
            raise StorageOperationError(f"Failed to get info for file {file_id}: {str(e)}")
    
    def list_files(self, prefix=None):
        """
        List files in storage.
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            list: List of file metadata
        """
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True)
            result = []
            
            for obj in objects:
                # Get basic info from the list response
                file_info = {
                    "id": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified.isoformat()
                }
                
                # Try to get detailed info
                try:
                    full_info = self.get_file_info(obj.object_name)
                    file_info.update(full_info)
                except Exception:
                    # If detailed info retrieval fails, use what we have
                    pass
                
                result.append(file_info)
                
            return result
        except S3Error as e:
            raise StorageOperationError(f"Failed to list files: {str(e)}")

# Singleton instance
_storage_service_instance = None

def get_storage_service():
    """Get the singleton storage service instance."""
    global _storage_service_instance
    if _storage_service_instance is None:
        _storage_service_instance = StorageService()
    return _storage_service_instance
