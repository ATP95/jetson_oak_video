from asyncio.windows_utils import pipe
import depthai as dai
import time
from upload_to_google import GCSObjectStreamUpload
from keyboard import is_pressed,read_key

pipeline = dai.Pipeline()

camRgb = pipeline.create(dai.node.ColorCamera)
camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)

ve = pipeline.create(dai.node.VideoEncoder)
    
veOut = pipeline.create(dai.node.XLinkOut)

veOut.setStreamName('veOut')  

camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)

ve.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.MJPEG)
ve.setQuality(96)
camRgb.video.link(ve.input)
ve.bitstream.link(veOut.input)

with dai.Device(pipeline=pipeline,usb2Mode=True) as cam, GCSObjectStreamUpload(bucket_name="oak_video",blob_name="video_stream_6.MJPEG",chunk_size=1024*1024) as GSU:
    rgbOut = cam.getOutputQueue(name='veOut', maxSize=30, blocking=True)
    st = time.perf_counter()
    print("Uploading to:",GSU._request.resumable_url,sep='\n')
    print("PRESS Q TO STOP STREAMING...")
    while True:
        bytes = bytearray()
        try:
            while rgbOut.has():
                bytes.extend(rgbOut.get().getData().tobytes())
        except KeyboardInterrupt:
                # Keyboard interrupt (Ctrl + C) detected
                print("Terminco manual.\n ---¡VIDEOS NO HAN SIDO SUBIDOS!---")
                GSU.write(bytes)
                break
        GSU.write(bytes)
        if read_key()=="q":
            break

        
        if time.perf_counter()-st >= 120:
            GSU.write(bytes)
            break

# with dai.Device(pipeline=pipeline,usb2Mode=True) as cam, open("ending.MJPEG",'wb') as f:
#     rgbOut = cam.getOutputQueue(name='veOut', maxSize=30, blocking=True)
#     for _ in range(2):
#         while rgbOut.has():
#             rgbOut.get().getData().tofile(f)

    