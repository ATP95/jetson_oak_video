import depthai as dai
import time,os
from shutil import rmtree
from datetime import datetime
from pathlib import Path
from json import dumps
from sys import exit,argv,executable
from file_transfer import upload_files_from_json
from send_mail import send_public_ip

send_public_ip()

# oak-d poe stereo MxId = 14442C10511330D700, ip= 192.168.1.2
# oak-d poe rgb only MxId= 14442C1011B53FD700, ip= 192.168.1.3
# utilizar para convertir a mp4 los archivos: "ffmpeg -framerate 30 -i {archivo_original.mjpeg} -c copy {nuevo.mp4}"

# Check/create directories to store data

dirParent = Path(__file__).parent # desde donde se ejecuta este script
os.chdir(dirParent)
dirName = ["stereo","rgb"]
Path(dirName[0]).mkdir(parents=True, exist_ok=True)
Path(dirName[1]).mkdir(parents=True, exist_ok=True)
dtp = datetime.now().strftime("%d%m_%H%M%S") # fecha y hora para crear nuevos archivos unicos

# revisar si existen videos previos y subir si no estan confirmados.
if os.path.exists(dirParent /"video_transfer.json"):
    if os.path.exist(dirParent/"stereo") and os.path.exists(dirParent/"rgb"):
        upload_files_from_json(dirParent /"video_transfer.json")
        

try:
    found_stereo, stereo_info = dai.Device.getDeviceByMxId("192.168.1.3")
    found_rgb, rgb_info = dai.Device.getDeviceByMxId("192.168.1.2")
    #logging.debug("Asserting Devices")
    assert  found_rgb
    print("Found Rgb ")                         
    assert found_stereo
    print("Found Stereo ")
except:
    print('Connection failed. Trying to connect again...')
    os.execv(executable, ['python'] + argv)


def get_pipeline(rgbOnly:bool=False, quality:int=96)->dai.Pipeline:
    pipeline = dai.Pipeline()

    # Define sources and outputs
    camRgb = pipeline.create(dai.node.ColorCamera)
     
    ve2 = pipeline.create(dai.node.VideoEncoder)
    
    ve2Out = pipeline.create(dai.node.XLinkOut)

    ve2Out.setStreamName('ve2Out')   

    # Properties
    camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)


    # Create encoders, one for each camera, consuming the frames and encoding them using H.264 / H.265 encoding

    ve2.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.MJPEG)
    ve2.setQuality(quality)
    # Linking
    camRgb.video.link(ve2.input)
    ve2.bitstream.link(ve2Out.input)

    if not rgbOnly:    
        monoLeft = pipeline.create(dai.node.MonoCamera)
        monoRight = pipeline.create(dai.node.MonoCamera)
        ve1 = pipeline.create(dai.node.VideoEncoder)
        ve3 = pipeline.create(dai.node.VideoEncoder)
    
        ve1Out = pipeline.create(dai.node.XLinkOut)
        ve3Out = pipeline.create(dai.node.XLinkOut)

        ve1Out.setStreamName('ve1Out')
        ve3Out.setStreamName('ve3Out')

        monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
        monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)   

        ve1.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.MJPEG)
        ve1.setQuality(quality)
        ve3.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.MJPEG)
        ve3.setQuality(quality)
        # Linking
        monoLeft.out.link(ve1.input)
        
        monoRight.out.link(ve3.input)
        ve1.bitstream.link(ve1Out.input)
        
        ve3.bitstream.link(ve3Out.input)


    return pipeline


stereo_pipeline = get_pipeline()

rgb_pipeline = get_pipeline(rgbOnly=True)

with dai.Device(stereo_pipeline,stereo_info) as stereo, dai.Device(rgb_pipeline,rgb_info) as rgb:
    #rgb.setLogOutputLevel(dai.LogLevel.DEBUG)

    #Rgb queue
    rgbOut = rgb.getOutputQueue(name='ve2Out', maxSize=30, blocking=True)

    # Stereo queues
    stereoOutQ1 = stereo.getOutputQueue(name='ve1Out', maxSize=30, blocking=True)
    stereoOutQ2 = stereo.getOutputQueue(name='ve2Out', maxSize=30, blocking=True)
    stereoOutQ3 = stereo.getOutputQueue(name='ve3Out', maxSize=30, blocking=True)
  
    # creating json for file transfer log
    files_n = {str(dirParent / f'stereo/left{dtp}.mjpeg'):False,
                str(dirParent / f'stereo/rgb{dtp}.mjpeg'):False,
                str(dirParent / f'stereo/right{dtp}.mjpeg'):False,
                str(dirParent / f'rgb/rgb{dtp}.mjpeg'):False
                }
    jsonf = dumps(files_n)
    jsonFile = open("video_transfer.json", "w")
    jsonFile.write(jsonf)
    jsonFile.close()

    # open context  for data record
    with open(dirParent / f'stereo/left{dtp}.mjpeg', 'wb') as stereoLeftH264, open(dirParent / f'stereo/rgb{dtp}.mjpeg', 'wb') as stereoRgbH265, \
        open(dirParent / f'stereo/right{dtp}.mjpeg', 'wb') as stereoRightH264, open(dirParent / f'rgb/rgb{dtp}.mjpeg', 'wb') as rgbH265:
        print("Press Ctrl+C to stop encoding...")
        start = time.time()
        while True:
            try:
                # Empty each queue
                while rgbOut.has():
                    rgbOut.get().getData().tofile(rgbH265)
                while stereoOutQ1.has():
                    stereoOutQ1.get().getData().tofile(stereoLeftH264)

                while stereoOutQ2.has():
                    stereoOutQ2.get().getData().tofile(stereoRgbH265)

                while stereoOutQ3.has():
                    stereoOutQ3.get().getData().tofile(stereoRightH264)

                
            except KeyboardInterrupt:
                # Keyboard interrupt (Ctrl + C) detected
                print("Terminco manual.\n ---¡VIDEOS NO HAN SIDO SUBIDOS!---")
                break

            
            if (time.time()-start)>=3600:
                try:
                    upload_files_from_json(dirParent /"video_transfer.json")
                except:
                    pass #TODO en jetson log que no se pudo subir archivo
                else:
                    rmtree(dirParent / 'stereo', ignore_errors=True)
                    rmtree(dirParent / 'rgb',  ignore_errors=True)
                try:
                    os.execv(executable, ['python'] + argv)
                except:
                    os.execv(executable, ['python3'] + argv)

    