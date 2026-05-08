import PyInstaller.__main__
import os

# Determinar el directorio base
base_dir = os.path.dirname(os.path.abspath(__file__))

# Rutas a incluir
assets_dir = os.path.join(base_dir, 'assets')
main_script = os.path.join(base_dir, 'main.py')

PyInstaller.__main__.run([
    main_script,
    '--name=MediaHub',
    '--onedir',             # Modo carpeta (más rápido de abrir que onefile)
    '--windowed',           # Sin consola negra de fondo
    '--icon=assets/hub/media.png', # Ícono del ejecutable
    f'--add-data={assets_dir};assets', # Incluir carpeta assets
    '--clean',              # Limpiar caché
    '--noconfirm',          # Sobrescribir sin preguntar
])

print("\n--- ¡Compilación completada! ---")
print("El ejecutable está en la carpeta 'dist/MediaHub'.")
