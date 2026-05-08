# Media Hub (Versión 1.1)

Aplicación de escritorio modular hecha en Python (PyQt6) para agrupar múltiples herramientas de conversión y edición impulsadas por Inteligencia Artificial, sin depender de páginas con anuncios.

Incluye una interfaz gráfica moderna con tarjetas, sistema de drag & drop, validación por tipo de archivo y barra de progreso durante conversiones masivas.

## Herramientas Incluidas

El Hub principal cuenta con las siguientes micro-aplicaciones integradas:

### 1. Multimedia Converter
- **Audio:** Conversión entre múltiples formatos (`mp3`, `wav`, `flac`, `ogg`, `m4a`).
- **Video:** Conversión de video sin marca de agua (`mp4`, `mkv`, `avi`, `mov`, `webm`).
- **Imágenes:** Conversión de formato para imágenes estándar.
- **Reescalador:** Redimensiona imágenes usando píxeles exactos o porcentajes, manteniendo la relación de aspecto y evitando agrandamientos forzados.

### 2. Document Converter
- **Office a PDF:** Convierte archivos de Word (`docx`) a PDF manteniendo el formato original (requiere MS Word instalado).
- **PDF a Word:** Extrae texto y formato de documentos PDF y los guarda en `.docx`.
- Soporte para procesamiento por lotes.

### 3. Background Eraser (IA)
- Utiliza la librería `rembg` para **eliminar fondos automáticamente**.
- Recorta sujetos y objetos principales sin intervención humana.
- Resultado siempre en formato `.png` para conservar la transparencia.

### 4. Quality Enhancer (IA - Real-ESRGAN)
- Herramienta de super resolución que utiliza el potente motor **Real-ESRGAN (Vulkan/NCNN)**.
- Mejora la calidad de la imagen por 4x recuperando píxeles perdidos y eliminando artefactos (efecto Remini).
- *El modelo de 25MB se descarga de forma automática en el primer uso.*

## Requisitos

- Python 3.11+ (recomendado)
- Dependencias de `requirements.txt`
- **FFmpeg** (obligatorio para audio/video)
- Microsoft Office (opcional, recomendado para conversiones precisas de Docx a PDF)

## Instalación

1) Clona o descarga el proyecto.

2) Crea y activa entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3) Instala dependencias:

```powershell
pip install -r requirements.txt
```

4) Instala FFmpeg (Windows recomendado):

```powershell
winget install "FFmpeg (Essentials Build)"
```

Si no queda en `PATH`, define la variable:

```powershell
setx FFMPEG_PATH "C:\ruta\a\ffmpeg.exe"
```

## Ejecución

```powershell
python main.py
```

## Troubleshooting rápido

- **“ffmpeg no está disponible”**  
  Asegúrate de haber instalado FFmpeg o configura la variable de entorno `FFMPEG_PATH`.

- **Demora excesiva en Background Eraser o Quality Enhancer**  
  La primera vez que uses estas herramientas, el sistema descargará los modelos de IA automáticamente (aproximadamente 25MB y 170MB). Después de la primera vez será mucho más rápido.
