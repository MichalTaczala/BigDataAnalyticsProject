from google.cloud import storage
import io
import tempfile
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GCSLoader:
    def __init__(self, bucket_name: str) -> None:
        """
        Initialize GCS loader with bucket name

        Args:
            bucket_name (str): GCS bucket name
        """

        logging.info("Initializing GCS Loader")
        self.client = storage.Client(project="regal-extension-418520")
        self.bucket = self.client.bucket(bucket_name)
        logging.info("GCS Loader initialized")

    def load_to_memory(self, blob_path: str) -> io.BytesIO:
        """
        Load file directly to memory buffer

        Args:
            blob_path (str): Path to file in bucket

        Returns:
            io.BytesIO: Memory buffer with file contents
        """
        blob = self.bucket.blob(blob_path)
        buffer = io.BytesIO()
        blob.download_to_file(buffer)
        buffer.seek(0)
        return buffer

    def load_to_temp(self, blob_path: str) -> str:
        """
        Load file to temporary file and return path

        Args:
            blob_path (str): Path to file in bucket

        Returns:
            str: Path to temporary file
        """
        blob = self.bucket.blob(blob_path)
        # Create temp file with same extension as original
        suffix = Path(blob_path).suffix
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        blob.download_to_filename(temp_file.name)
        return temp_file.name

    def load_to_path(self, blob_path: str, local_path: str) -> None:
        """
        Load file to specified local path

        Args:
            blob_path (str): Path to file in bucket
            local_path (str): Local path to save file
        """

        blob = self.bucket.blob(blob_path)
        blob.download_to_filename(local_path)

    def list_files(self, prefix: str | None = None) -> list[str]:
        """
        List all files in bucket/prefix

        Args:
            prefix (str, optional): Prefix to filter files

        Returns:
            list: List of file paths
        """
        return [blob.name for blob in self.bucket.list_blobs(prefix=prefix)]
