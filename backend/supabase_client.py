"""
Supabase Integration Module
Handles file storage operations using Supabase Storage
Provides fallback to local filesystem for backward compatibility
"""
import os
from typing import Optional, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "lab-reports")

# Initialize Supabase client (only if credentials are provided)
supabase_client: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
else:
    logger.warning("Supabase credentials not found. File storage will use local filesystem only.")


def is_supabase_enabled() -> bool:
    """Check if Supabase is configured and available."""
    return supabase_client is not None


def upload_file_to_supabase(file_path: str, file_name: str, user_id: int) -> Tuple[bool, Optional[str]]:
    """
    Upload a file to Supabase Storage.
    
    Args:
        file_path: Local path to the file
        file_name: Name to store the file as
        user_id: ID of the user uploading the file (for organizing storage)
        
    Returns:
        Tuple of (success: bool, storage_url: Optional[str])
    """
    if not is_supabase_enabled():
        logger.warning("Supabase not enabled. Skipping upload.")
        return False, None
    
    try:
        # Create path with user_id prefix for organization
        storage_path = f"{user_id}/{file_name}"
        
        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Upload to Supabase Storage
        response = supabase_client.storage.from_(SUPABASE_BUCKET_NAME).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": "application/pdf"}
        )
        
        # Get public URL
        storage_url = supabase_client.storage.from_(SUPABASE_BUCKET_NAME).get_public_url(storage_path)
        
        logger.info(f"File uploaded successfully to Supabase: {storage_path}")
        return True, storage_url
        
    except Exception as e:
        logger.error(f"Failed to upload file to Supabase: {e}")
        return False, None


def download_file_from_supabase(storage_path: str) -> Tuple[bool, Optional[bytes]]:
    """
    Download a file from Supabase Storage.
    
    Args:
        storage_path: Path in Supabase Storage (e.g., "123/report.pdf")
        
    Returns:
        Tuple of (success: bool, file_content: Optional[bytes])
    """
    if not is_supabase_enabled():
        logger.warning("Supabase not enabled. Cannot download.")
        return False, None
    
    try:
        response = supabase_client.storage.from_(SUPABASE_BUCKET_NAME).download(storage_path)
        logger.info(f"File downloaded successfully from Supabase: {storage_path}")
        return True, response
        
    except Exception as e:
        logger.error(f"Failed to download file from Supabase: {e}")
        return False, None


def delete_file_from_supabase(storage_path: str) -> bool:
    """
    Delete a file from Supabase Storage.
    
    Args:
        storage_path: Path in Supabase Storage (e.g., "123/report.pdf")
        
    Returns:
        True if deletion was successful, False otherwise
    """
    if not is_supabase_enabled():
        logger.warning("Supabase not enabled. Cannot delete.")
        return False
    
    try:
        supabase_client.storage.from_(SUPABASE_BUCKET_NAME).remove([storage_path])
        logger.info(f"File deleted successfully from Supabase: {storage_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete file from Supabase: {e}")
        return False


def get_file_url(storage_path: str) -> Optional[str]:
    """
    Get public URL for a file in Supabase Storage.
    
    Args:
        storage_path: Path in Supabase Storage (e.g., "123/report.pdf")
        
    Returns:
        Public URL or None if not available
    """
    if not is_supabase_enabled():
        return None
    
    try:
        url = supabase_client.storage.from_(SUPABASE_BUCKET_NAME).get_public_url(storage_path)
        return url
    except Exception as e:
        logger.error(f"Failed to get file URL from Supabase: {e}")
        return None
