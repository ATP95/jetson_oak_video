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







