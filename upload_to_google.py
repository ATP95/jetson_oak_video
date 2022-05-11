import os
from google.cloud import storage
from google.resumable_media.requests import ResumableUpload
import google.auth.transport.requests as tr_requests
from io import BytesIO
from google.resumable_media.common import InvalidResponse 

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(),"oak-storage-347821-6afa46c62dab.json")

# storage_client = storage.Client()

bucket_name = "oak_video"


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
        with open(self.file_path,"rb") as f:
            data = f.read()
        url = (
            f'https://www.googleapis.com/upload/storage/v1/b/'
            f'{self._bucket.name}/o?uploadType=resumable'
        )
        self._upload = ResumableUpload(upload_url=url, chunk_size=self._chunk_size)

        self._upload.initiate(self._transport,
                        stream=BytesIO(data),
                        metadata={"name":self._blob.name},
                        stream_final=True,
                        content_type="video/stream")

    def stop(self):
        print("Uploaded: ",self._upload.total_bytes, " bytes")
    #TODO ver si hay alguna forma de usar tell para reanudar desde un apagon
    def transmit(self):
        print("Starting Upload")
        while not self._upload.finished:
            try:
                self._upload.transmit_next_chunk(self._transport)
            except InvalidResponse as caught_exc:
                print("Error: ", caught_exc)
                self._upload.recover(self._transport)


# -------------Resumable---------------- 
# with GSUObject_Resumable("video_test4.MJPEG","/home/jetsoak/Desktop/PythonScripts/OAK-D-POE_rbg.MJPEG", bucket_name) as ru:
#     ru.transmit()

