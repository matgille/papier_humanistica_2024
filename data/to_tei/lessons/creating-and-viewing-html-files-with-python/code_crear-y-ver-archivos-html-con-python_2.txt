# escribe-html-2-windows.py

import webbrowser

f = open('holamundo.html','w')

mensaje = """<html>
<head></head>
<body><p>Hola Mundo!</p></body>
</html>"""

f.write(mensaje)
f.close()

webbrowser.open_new_tab('holamundo.html')
