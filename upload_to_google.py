import os
from google.cloud import storage
from google.resumable_media.requests import ResumableUpload
import google.auth.transport.requests as tr_requests
from io import BytesIO
from google.resumable_media.common import InvalidResponse 

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(),"oak-storage-347821-3e7a28e22c99.json")

# storage_client = storage.Client()

bucket_name = "oak_video"


def list_blobs(bucket_name):
    """Lists all the blobs in the bucket."""
    # bucket_name = "your-bucket-name"

    storage_client = storage.Client()

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name)

    for blob in blobs:
        print(blob.name)

# Subir a google directamente 
class GSUObject_Direct():

    def __init__(self,blob_name,file_path,bucket_name) -> None:
        self.client = storage.Client()
        self.blob_name = blob_name
        self.file_path = file_path
        self.bucket_name = bucket_name
    def upload_to_bucket(self):
        try:
            bucket = self.client.get_bucket(self.bucket_name)
            blob = bucket.blob(self.blob_name)
            blob.upload_from_filename(self.file_path)
            return True

        except Exception as e:
            print(e)
            return False

#subir a google con una carga reanudable
class GSUObject_Resumable():
    

    def __init__(self,blob_name:str,file_path:str,bucket_name:str, chunk_size: int=1024*1024) -> None:
        self.client = storage.Client()
        self._bucket = self.client.bucket(bucket_name)
        self._blob = self._bucket.blob(blob_name)
        self.file_path = file_path
        self._upload = None
        self._chunk_size = chunk_size
        self._transport = tr_requests.AuthorizedSession(credentials=self.client._credentials)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, *_):
        if exc_type is None:
            self.stop()

    def start(self):
        print(f"Creating resumable upload for {self.file_path}.")
        self.data_buffer =  open(self.file_path,"rb")
        url = (
            f'https://www.googleapis.com/upload/storage/v1/b/'
            f'{self._bucket.name}/o?uploadType=resumable'
        )
        self._upload = ResumableUpload(upload_url=url, chunk_size=self._chunk_size)

        self._upload.initiate(self._transport,
                        stream= self.data_buffer,
                        metadata={"name":self._blob.name},
                        stream_final=True,
                        content_type="video/stream")

    def stop(self):
        print("Uploaded: ",self._upload.total_bytes, " bytes")
        self.data_buffer.close()
    #TODO ver si hay alguna forma de usar tell para reanudar desde un apagon
    def transmit(self):
        print("Starting Upload")
        while not self._upload.finished:
            try:
                self._upload.transmit_next_chunk(self._transport)
            except InvalidResponse as caught_exc:
                print("Error: ", caught_exc)
                self._upload.recover(self._transport)

class GCSObjectStreamUpload():
    "example from https://dev.to/sethmlarson/python-data-streaming-to-google-cloud-storage-with-resumable-uploads-458h"
    def __init__(
            self,
            bucket_name: str,
            blob_name: str,
            chunk_size: int=256 * 1024
        ):
        self._client = storage.Client()
        self._bucket = self._client.bucket(bucket_name)
        self._blob = self._bucket.blob(blob_name)

        self._buffer = b''
        self._buffer_size = 0
        self._chunk_size = chunk_size
        self._read = 0

        self._transport = tr_requests.AuthorizedSession(
            credentials=self._client._credentials
        )
        
        self._request = None # type: ResumableUpload

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, *_):
        if exc_type is None:
            self.stop()

    def start(self):
        url = (
            f'https://www.googleapis.com/upload/storage/v1/b/'
            f'{self._bucket.name}/o?uploadType=resumable'
        )
        self._request = ResumableUpload(
            upload_url=url, chunk_size=self._chunk_size
        )
        self._request.initiate(
            transport=self._transport,
            content_type='application/octet-stream',
            stream=self,
            stream_final=False,
            metadata={'name': self._blob.name},
        )

    def stop(self):
        self._request.transmit_next_chunk(self._transport)

    def write(self, data: bytes) -> int:
        data_len = len(data)
        self._buffer_size += data_len
        self._buffer += data
        del data
        while self._buffer_size >= self._chunk_size:
            try:
                self._request.transmit_next_chunk(self._transport)
            except InvalidResponse:
                self._request.recover(self._transport)
        return data_len

    def read(self, chunk_size: int) -> bytes:
        # I'm not good with efficient no-copy buffering so if this is
        # wrong or there's a better way to do this let me know! :-)
        to_read = min(chunk_size, self._buffer_size)
        memview = memoryview(self._buffer)
        self._buffer = memview[to_read:].tobytes()
        self._read += to_read
        self._buffer_size -= to_read
        return memview[:to_read].tobytes()

    def tell(self) -> int:
        return self._read

# -------------Resumable---------------- 
# with GSUObject_Resumable("git.exe",r"D:\Downloads\git.exe", bucket_name) as ru:
#     ru.transmit()

