import smtplib
import time
from get_public_ip import PublicIp
import smtplib, ssl
from os import environ

def send_mail(sender:str, psswd:str, receiver:str,subject:str,message:str) -> None:
    port = 465
    ms = f"""Subject:{subject}\n{message}"""

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender, psswd)
        server.sendmail(sender, receiver, ms)


def send_public_ip():
    try:
        send_mail("pythonscript9816@gmail.com",environ.get("GM_PSWD"),"pythonscript9816@gmail.com", "public ip",PublicIp())
        return True
    except:
        return False




   