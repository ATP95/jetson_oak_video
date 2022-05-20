import os
import requests
from google.cloud import storage
from google.resumable_media.requests import ResumableUpload
import google.auth.transport.requests as tr_requests
from io import BytesIO
from google.resumable_media.common import InvalidResponse 

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(),"oak-storage-347821-3e7a28e22c99.json")

# storage_client = storage.Client()

# bucket_name = "oak_video"


# Subir a google directamente 
class GSUObject_Direct():

    def __init__(self,blob_name:str,file_path:str,bucket_name:str) -> None:
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
    

    def __init__(self,blob_name:str,file_path:str,bucket_name:str, chunk_size: int=8388608) -> None: #8388608 recomended bytes for chunk upload (8 megabytes)
        self.client = storage.Client()
        self._bucket = self.client.bucket(bucket_name)
        self._bucket.cors = [
    {
        "origin": ["*"],
        "responseHeader": [
            "Content-Type",
            "Access-Control-Allow-Origin",
            "x-goog-resumable"],
        "method": ["GET", "HEAD", "DELETE", "POST", "OPTIONS"],
        "maxAgeSeconds": 3600
    }]
        self._bucket.patch()
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
        print(f"Starting....\nCreating resumable upload for {self.file_path}.")
        self.data_buffer =  open(self.file_path,"rb")
        url = (
            f'https://www.googleapis.com/upload/storage/v1/b/'
            f'{self._bucket.name}/o?uploadType=resumable'
        )
        
        self._upload = ResumableUpload(upload_url=url, chunk_size=self._chunk_size,)
        #TODO crear hasta aqui pero despues usar self._upload.recover para recuperar usando url de subida
        self._upload.initiate(self._transport,
                        stream= self.data_buffer,
                        metadata={"name":self._blob.name},
                        stream_final=True,
                        content_type="video/stream")
        print(f"Upload at {self._upload.resumable_url}")

    def stop(self):
        print("Stoping...")
        PARAMS ={"Content-Length":0,"Content-Range":"bytes * "}
        req = requests.request("PUT",self._upload.resumable_url,params=PARAMS)
        print(f"status: {req}")
        self.data_buffer.close()
    def transmit(self):
        print("Uploading...")
        while not self._upload.finished:
            try:
                self._upload.transmit_next_chunk(self._transport)
            except InvalidResponse as caught_exc:
                print("Error: ", caught_exc)
                self._upload.recover(self._transport)

#subir utilizando url de una descarga a medias
class GSUObject_fromResumableUrl():
    def __init__(self,url:str,file_path:str,chunck_size:int=8388608) -> None:
        self.resumable_url = url
        self.file = open(file_path,'rb')
        self.size = os.path.getsize(file_path)
        self.chunk = chunck_size

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, *_):
        self.file.close()

    def start(self): 
        if self.status() != 308:
            raise Exception(f"Link no valido para reanudar descarga.\n Response: {self.response.status_code}")
            
    def transmit(self):        
        try:
            range = [int(x) for x in self.response.headers["Range"].split(" ")[1].split("-")] #range of bytes already transmited (chuncks of 8388608 bytes)
        except IndexError:
            range = [int(x) for x in self.response.headers["Range"].split("=")[1].split("-")]
        NEXT_BYTE = range[1]+1
        self.file.seek(NEXT_BYTE,0)
        data = self.file.read(self.chunk)
        UPLOAD_SIZE_REMAINING = self.size-(range[1]-range[0]+1)
        LAST_BYTE = range[1]+ self.chunk
        PARAMS ={"Content-Length":f"{UPLOAD_SIZE_REMAINING}","Content-Range":f"bytes {NEXT_BYTE}-{LAST_BYTE}/{self.size}"}
        requests.put(self.resumable_url,data=BytesIO(data),params=PARAMS)


    def status(self):
        PARAMS ={"Content-Length":"0",f"Content-Range":"bytes */{self.size}"}
        self.response = requests.put(self.resumable_url,params=PARAMS)
        return self.response.status_code


# -------------Resumable---------------- 
# with GSUObject_Resumable("resumable_file_test.ipynb",r"resumable_file_test.ipynb", "oak_video") as ru:
#     ru.transmit()

