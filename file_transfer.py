from json import loads,dumps
from upload_to_google import GSUObject_Resumable
from os import path
from socket import gethostbyname, create_connection

#TODO Incluir subida reanudable al programa, eso significa ademas de guardar nombre de archivo guardar llave de google para reanudar.

def check_internet_connection():
    #ping -q -c1 google.com &>/dev/null && echo online || echo offline
    try:
        host = gethostbyname("www.google.com")
        s = create_connection((host, 80), 2)
        return True
    except:
        pass
    return False 

def upload_files_from_json(jsonlog:str):
    with open(jsonlog,'r') as f:
        logf = loads(f.read())
    
    files_names = list(logf.keys())

    for file_path in files_names:
        if not logf[file_path]: # check if file was uploaded
            n = path.basename(file_path) #file name only
            with GSUObject_Resumable(n,file_path,"oak_video") as ru: # resumable google upload that can restart on network failure
                ru.transmit()
            print("Upload ended")
            logf[file_path] = True

    with open(jsonlog, "w") as jlog:
        jlog.write(dumps(logf))

