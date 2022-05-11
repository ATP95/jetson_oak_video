def PublicIp():    
    from requests import get

    try:
        ip = get('https://api.ipify.org').text
        return ip
    except Exception as e:
        return False
if __name__=="__main__":
    
    print('My public IP address is: {}'.format(PublicIp()))
