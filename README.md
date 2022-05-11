## Configuracion de la Jetson
La Jetson nano esta configurada con los siguientes parametros:

|Variable | Description|
|---|:---:|
|ip estatica | 192.168.1.203|
|hostname | jetson-linux|
|username | jetsoak |
|password | oak2022 |

utilizando estos parametros esta habilitada tanto la conexion *ssh* como la conexion *vnc*.

---
## Captura de Imagen

El [programa principal](main.py) captura la imagen de las camaras OAK PoE las cuales fueron asignadas a las **ip estaticas** *192.168.1.2* y *192.168.1.3* .

 Una de las camaras captura ambas imagenes mono y tambien rgb y las guarda en la carpeta **stereo** ( carpeta creada automaticamente en el mismo directorio de ejecución del programa), mientras que, la otra camara solo captura la imagen rgb y la guarda en la carpeta de nombre **rgb**. Los archivos estan guardados a **30 fps** en calidad *MJPEG*.

 Al mismo tiempo se  crea una id unica para los archivos utilizando la fecha y hora en la que empezo a correr el programa
 ```python
 "%d%m_%H%M%S"
 ```
con esto se tambien se crea un diccionario que tiene como llaves el nombre de archivo y como valores **false** indicando esto que el archivo aun no a sido enviado a almacenamiento. Este diccionario se guarda localmente como archivo JSON para poder acceder a este desde fuera de la instancia actual del programa.

El programa funciona durante 1 hora por defecto ([se puede cambiar en linea 152](main.py#L152)) y luego deja de capturar imagenes para subir a la nube lo que ya ha guardado.

---
## Subida a la nube
Para subir los videos en este caso a [google storage](https://cloud.google.com/storage) se utiliza el scrip [file_transfer](file_transfer.py), que lee el archivo "video_transfer.json" que se creo anteriormente y para cada directorio de video que tengan como valor falso crea una sesion de [carga reanudable](upload_to_google.py) (que puede manejar intermitencia en el internet) para mandar los videos.

Cada vez que logra mandar un video exitosamente modifica el estado de este en el archivo JSON a **true**. Esto ya que cada vez que el programa inicie verificara la existencia de videos y si es que estos han sido exitosamente subidos. Por lo tanto, si llegara a haber una falla antes de que se termine de enviar uno de los videos, la proxima vez que se inicie la captura de datos, primero se enviaran los videos que faltan antes de conectar las camaras.

---
Debido a las posibles limitaciones en acho de banda y capacidad de computo de la jetson 
por el momento no se utilizo ninguna forma de computacion en paralelo para subir los archivos, pero deberia funcionar relativamente rapido con conexiones estables por cable ethernet.

---

## Correr Programa como servicio en Jetson

Para que el programa funcione cada vez que la Jetson enciende y que cada vez que se complete el ciclo de captura de imagen y subida se vueva a iniciar nuevamente, se deja el programa funcionando como servicio para que así sea el sistema operativo el que se encarge de reiniciarlo.

El archivo [camera-oak.service](camera-oak.service) correspondera al servicio **camera-oak** en los ajustes del sistema. Para indicarle al servicio que programa usar, en la linea ExecStart se colocan la direccion al interprete de python, espacio, direccion del script (en este caso [main.py](main.py)).

```service
ExecStart = <direccion del interprete de python> <direccion del script.py a correr>
```

Para habilitar el servicio se deben ejecutar los siguientes comandos en el mismo directorio que el archivo *.service*:
```bash 
$ sudo cp camera-oak.service /etc/systemd/system/
$ sudo systemctl daemon-reload
$ sudo systemctl enable camera-oak.service
```
Para iniciar el servicio (comenzara a ejecutarse el script y la captura de imagen) se debe usar
```bash
$ sudo systemctl start camera-oak.service
```

Para parar el servicio(dejara de capturar imagen o de subir a la nube y no volvera a reiniciar automaticamente)
```bash
$ sudo systemctl stop camera-oak.service
```
Para reiniciar o para comprobar el estatus del servicio, usar respectivamente
```bash
$ sudo systemctl restart camera-oak.service
$ sudo systemctl status camera-oak.service
```