#-----------------------------------------------
# Convertidor de Imagenes
#-----------------------------------------------

from PIL import Image, ImageFile
import os
import shutil

# Pillow sometimes fails on truncated images; enable loading anyway
ImageFile.LOAD_TRUNCATED_IMAGES = True


def _prepare_dest(ruta_destino: str) -> str:
    """Asegura que la carpeta de destino exista dentro del repositorio.

    - Si `ruta_destino` es relativa, se interpreta respecto a la raíz del repo.
    - Crea el directorio padre si no existe.
    - Devuelve la ruta absoluta final a usar para guardar.
    """
    if ruta_destino is None:
        raise ValueError("ruta_destino no puede ser None")

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    if not os.path.isabs(ruta_destino):
        ruta_abs = os.path.join(repo_root, ruta_destino)
    else:
        ruta_abs = ruta_destino

    parent = os.path.dirname(ruta_abs)
    if parent == '':
        parent = os.path.join(repo_root, 'destino')
        ruta_abs = os.path.join(parent, os.path.basename(ruta_abs))

    os.makedirs(parent, exist_ok=True)
    return ruta_abs


def _find_ffmpeg() -> str | None:
    """Intentar localizar el ejecutable ffmpeg."""
    env_path = os.environ.get('FFMPEG_PATH')
    if env_path:
        env_path = os.path.abspath(env_path)
        if os.path.isfile(env_path):
            return env_path
        if os.path.isdir(env_path):
            for candidate in ('ffmpeg.exe', 'ffmpeg'):
                maybe = os.path.join(env_path, candidate)
                if os.path.isfile(maybe):
                    return maybe

    for name in ('ffmpeg', 'ffmpeg.exe'):
        p = shutil.which(name)
        if p:
            return p

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    candidates = [
        os.path.join(repo_root, 'ffmpeg', 'ffmpeg'),
        os.path.join(repo_root, 'ffmpeg', 'ffmpeg.exe'),
        os.path.join(repo_root, 'ffmpeg', 'bin', 'ffmpeg'),
        os.path.join(repo_root, 'ffmpeg', 'bin', 'ffmpeg.exe'),
        os.path.join(repo_root, 'bin', 'ffmpeg'),
        os.path.join(repo_root, 'bin', 'ffmpeg.exe'),
        os.path.join(repo_root, 'ffmpeg.exe'),
        os.path.join(repo_root, 'ffmpeg'),
    ]

    user_profile = os.environ.get('USERPROFILE', '')
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    program_files = os.environ.get('ProgramFiles', r'C:\Program Files')
    program_files_x86 = os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')
    windows_candidates = [
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'C:\ffmpeg\ffmpeg.exe',
        os.path.join(program_files, 'ffmpeg', 'bin', 'ffmpeg.exe'),
        os.path.join(program_files_x86, 'ffmpeg', 'bin', 'ffmpeg.exe'),
        os.path.join(program_files, 'ImageMagick-7.1.1-Q16-HDRI', 'ffmpeg.exe'),
        os.path.join(local_app_data, 'Microsoft', 'WinGet', 'Links', 'ffmpeg.exe'),
        os.path.join(user_profile, 'scoop', 'shims', 'ffmpeg.exe'),
        os.path.join(user_profile, 'scoop', 'apps', 'ffmpeg', 'current', 'bin', 'ffmpeg.exe'),
        os.path.join(os.environ.get('ProgramData', r'C:\ProgramData'), 'chocolatey', 'bin', 'ffmpeg.exe'),
    ]
    candidates.extend(windows_candidates)

    for c in candidates:
        if os.path.isfile(c):
            return c

    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if p and os.path.isfile(p):
            return p
    except Exception:
        pass

    return None


class ImageFormats:
    formatos_imagen = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'gif', 'ico']

    @staticmethod
    def _open_image(ruta_origen):
        return Image.open(ruta_origen)

    @staticmethod
    def _save_image(img: Image.Image, ruta_destino: str, formato: str, quality: int = 85):
        ruta_destino = _prepare_dest(ruta_destino)
        formato_lower = formato.lower()

        if formato_lower in ('jpg', 'jpeg'):
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                fondo = Image.new('RGB', img.size, (255, 255, 255))
                fondo.paste(img.convert('RGBA'), mask=img.convert('RGBA').split()[-1])
                fondo.save(ruta_destino, 'JPEG', quality=quality)
            else:
                img.convert('RGB').save(ruta_destino, 'JPEG', quality=quality)
        elif formato_lower == 'png':
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img.save(ruta_destino, 'PNG', optimize=True)
            else:
                img.convert('RGB').save(ruta_destino, 'PNG', optimize=True)
        elif formato_lower == 'webp':
            img.save(ruta_destino, 'WEBP', quality=quality, method=6)
        elif formato_lower == 'ico':
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            # Ensure it fits max standard ico size, but PIL handles standard resizing or saves as is.
            img.save(ruta_destino, format='ICO')
        else:
            try:
                img.save(ruta_destino, formato.upper())
            except Exception:
                img.save(ruta_destino)

        return f"✅ Convertido: {os.path.basename(ruta_destino)}"

    @staticmethod
    def convertir(ruta_origen, ruta_destino, formato_destino=None):
        try:
            if formato_destino is None:
                formato_destino = os.path.splitext(ruta_destino)[1].lstrip('.').lower()
            img = ImageFormats._open_image(ruta_origen)
            return ImageFormats._save_image(img, ruta_destino, formato_destino)
        except Exception as e:
            return f"⚠️ Error con {os.path.basename(ruta_origen)}: {e}"

    @staticmethod
    def convertir_jpg_a_png(ruta_origen, ruta_destino):
        try:
            img = ImageFormats._open_image(ruta_origen)
            return ImageFormats._save_image(img, ruta_destino, 'png')
        except Exception as e:
            return f"⚠️ Error con {os.path.basename(ruta_origen)}: {e}"

    @staticmethod
    def convertir_jpg_a_webp(ruta_origen, ruta_destino):
        try:
            img = ImageFormats._open_image(ruta_origen)
            return ImageFormats._save_image(img, ruta_destino, 'webp')
        except Exception as e:
            return f"⚠️ Error con {os.path.basename(ruta_origen)}: {e}"

    @staticmethod
    def convertir_png_a_jpg(ruta_origen, ruta_destino):
        try:
            img = ImageFormats._open_image(ruta_origen)
            return ImageFormats._save_image(img, ruta_destino, 'jpg')
        except Exception as e:
            return f"⚠️ Error con {os.path.basename(ruta_origen)}: {e}"

    @staticmethod
    def convertir_png_a_webp(ruta_origen, ruta_destino):
        try:
            img = ImageFormats._open_image(ruta_origen)
            return ImageFormats._save_image(img, ruta_destino, 'webp')
        except Exception as e:
            return f"⚠️ Error con {os.path.basename(ruta_origen)}: {e}"

    @staticmethod
    def convertir_webp_a_jpg(ruta_origen, ruta_destino):
        try:
            img = ImageFormats._open_image(ruta_origen)
            return ImageFormats._save_image(img, ruta_destino, 'jpg')
        except Exception as e:
            return f"⚠️ Error con {os.path.basename(ruta_origen)}: {e}"

    @staticmethod
    def convertir_webp_a_png(ruta_origen, ruta_destino):
        try:
            img = ImageFormats._open_image(ruta_origen)
            return ImageFormats._save_image(img, ruta_destino, 'png')
        except Exception as e:
            return f"⚠️ Error con {os.path.basename(ruta_origen)}: {e}"


class ImageRescalerLogic:
    @staticmethod
    def reescalar_imagen(ruta_origen, ruta_destino, modo="pixeles", ancho_target=None, alto_target=None, porcentaje=None, mantener_aspecto=True, no_agrandar=False):
        try:
            img = Image.open(ruta_origen)
            w, h = img.size

            if modo == "porcentaje":
                if porcentaje is None:
                    return "⚠️ Error: Porcentaje no especificado."
                factor = porcentaje / 100.0
                new_w = int(w * factor)
                new_h = int(h * factor)
            else: # pixeles
                if ancho_target is None or alto_target is None:
                    return "⚠️ Error: Ancho y alto deben especificarse en modo píxeles."
                new_w = int(ancho_target)
                new_h = int(alto_target)

                if mantener_aspecto:
                    # Si mantener aspecto está activo, recalculamos en base a la escala más restrictiva
                    # O podemos simplemente reescalar manteniendo el aspecto del ancho. 
                    # Generalmente se respeta el que se modificó, pero dejaremos que la UI mande 
                    # el ancho/alto con el aspecto ya mantenido o recalculamos acá si hace falta.
                    # Asumimos que la UI ya pasa los valores correctamente ajustados.
                    pass

            if no_agrandar:
                if new_w > w or new_h > h:
                    new_w = min(new_w, w)
                    new_h = min(new_h, h)

            if (new_w, new_h) == (w, h):
                # No resize needed, just save copy
                img_resized = img
            else:
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
            return ImageFormats._save_image(img_resized, ruta_destino, os.path.splitext(ruta_destino)[1].lstrip('.').lower())
        except Exception as e:
            return f"⚠️ Error reescalando {os.path.basename(ruta_origen)}: {e}"


class BackgroundRemoverLogic:
    @staticmethod
    def quitar_fondo(ruta_origen, ruta_destino):
        try:
            import rembg
            with open(ruta_origen, "rb") as input_file:
                input_data = input_file.read()
                
            # Utilizamos un modelo avanzado y aplicamos post-procesado para evitar manchas
            session = rembg.new_session("isnet-general-use")
            output_data = rembg.remove(input_data, session=session, post_process_mask=True)
            
            # Ensure the destination path is absolute and exists
            ruta_destino = _prepare_dest(ruta_destino)
            
            with open(ruta_destino, "wb") as output_file:
                output_file.write(output_data)
                
            return f"✅ Fondo eliminado: {os.path.basename(ruta_destino)}"
        except ImportError:
            return "⚠️ Error: La librería rembg no está instalada."
        except Exception as e:
            return f"⚠️ Error quitando fondo a {os.path.basename(ruta_origen)}: {e}"


class ImageEnhancerLogic:
    @staticmethod
    def _download_model_if_needed():
        import requests
        import zipfile
        appdata_dir = os.environ.get('APPDATA') or os.path.expanduser('~')
        models_dir = os.path.join(appdata_dir, "MediaHub", "models", "realesrgan")
        os.makedirs(models_dir, exist_ok=True)
        exe_path = os.path.join(models_dir, "realesrgan-ncnn-vulkan.exe")
        
        if not os.path.exists(exe_path):
            zip_path = os.path.join(models_dir, "realesrgan.zip")
            url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(models_dir)
                    
                os.remove(zip_path)
            else:
                raise Exception("No se pudo descargar el modelo de Super Resolución (Real-ESRGAN).")
        return exe_path

    @staticmethod
    def mejorar_calidad(ruta_origen, ruta_destino):
        import subprocess
        import tempfile
        import shutil
        import uuid
        try:
            exe_path = ImageEnhancerLogic._download_model_if_needed()
            
            # Ensure the destination path is absolute and exists
            ruta_destino = _prepare_dest(ruta_destino)
            
            # Use temp files to avoid Unicode issues with the executable
            temp_dir = tempfile.gettempdir()
            unique_id = str(uuid.uuid4())
            ext_origen = os.path.splitext(ruta_origen)[1].lower()
            if not ext_origen:
                ext_origen = ".png"
            
            input_tmp = os.path.join(temp_dir, f"input_{unique_id}{ext_origen}")
            output_tmp = os.path.join(temp_dir, f"output_{unique_id}.png")
            
            shutil.copy2(ruta_origen, input_tmp)
            
            # Run Real-ESRGAN
            cmd = [
                exe_path,
                "-i", input_tmp,
                "-o", output_tmp,
                "-s", "4"
            ]
            
            # Hide console window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.run(cmd, check=True, startupinfo=startupinfo)
            
            if os.path.exists(output_tmp):
                shutil.copy2(output_tmp, ruta_destino)
            else:
                raise Exception("El programa no generó la imagen de salida.")
                
            # Cleanup
            try:
                os.remove(input_tmp)
                os.remove(output_tmp)
            except:
                pass
            
            return f"✅ Calidad mejorada con IA (Real-ESRGAN): {os.path.basename(ruta_destino)}"
        except Exception as e:
            return f"⚠️ Error mejorando la calidad de {os.path.basename(ruta_origen)}: {e}"


class AudioFormats:
    formatos_audio = ['mp3', 'wav', 'flac', 'ogg', 'm4a', 'mpeg', 'aac', 'wma', 'alac', 'aiff']

    @staticmethod
    def _run_ffmpeg(ruta_origen, ruta_destino, extra_args=None):
        import subprocess
        if extra_args is None:
            extra_args = []
        ruta_destino = _prepare_dest(ruta_destino)
        ffmpeg_path = _find_ffmpeg()
        if not ffmpeg_path:
            return False, '❌ ffmpeg no está disponible. Añádelo a PATH o define la variable de entorno FFMPEG_PATH apuntando al ejecutable.'
        cmd = [ffmpeg_path, '-y', '-i', ruta_origen] + extra_args + [ruta_destino]
        try:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, cwd=repo_root)
            return True, f"✅ Convertido: {os.path.basename(ruta_origen)} -> {os.path.basename(ruta_destino)}"
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode(errors='replace') if isinstance(e.stderr, (bytes, bytearray)) else str(e.stderr)
            return False, f"⚠️ Error en ffmpeg: {stderr}"

    @staticmethod
    def _default_audio_args(formato_destino: str):
        fmt = (formato_destino or '').lower()
        if fmt == 'mp3':
            return ['-vn', '-c:a', 'libmp3lame', '-b:a', '192k']
        if fmt == 'wav':
            return ['-vn', '-c:a', 'pcm_s16le', '-ar', '44100', '-ac', '2']
        if fmt == 'flac':
            return ['-vn', '-c:a', 'flac']
        if fmt == 'ogg':
            return ['-vn', '-c:a', 'libvorbis', '-q:a', '5']
        if fmt in ('m4a', 'aac'):
            return ['-vn', '-c:a', 'aac', '-b:a', '192k']
        return ['-vn', '-c:a', 'aac', '-b:a', '192k']

    @staticmethod
    def convertir(ruta_origen, ruta_destino, formato_destino=None):
        try:
            if formato_destino is None:
                formato_destino = os.path.splitext(ruta_destino)[1].lstrip('.').lower()
            extra_args = AudioFormats._default_audio_args(formato_destino)
            ok, msg = AudioFormats._run_ffmpeg(ruta_origen, ruta_destino, extra_args=extra_args)
            return msg
        except Exception as e:
            return f"⚠️ Error con {os.path.basename(ruta_origen)}: {e}"


class VideoFormats:
    formatos_video = ['mp4', 'mkv', 'avi', 'mov', 'webm', 'flv', 'wmv', 'm4v', '3gp', 'mpeg']

    @staticmethod
    def _run_ffmpeg(ruta_origen, ruta_destino, extra_args=None):
        import subprocess
        if extra_args is None:
            extra_args = []
        ruta_destino = _prepare_dest(ruta_destino)
        ffmpeg_path = _find_ffmpeg()
        if not ffmpeg_path:
            return False, '❌ ffmpeg no está disponible. Añádelo a PATH o define la variable de entorno FFMPEG_PATH apuntando al ejecutable.'
        cmd = [ffmpeg_path, '-y', '-i', ruta_origen] + extra_args + [ruta_destino]
        try:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, cwd=repo_root)
            return True, f"✅ Convertido: {os.path.basename(ruta_origen)} -> {os.path.basename(ruta_destino)}"
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode(errors='replace') if isinstance(e.stderr, (bytes, bytearray)) else str(e.stderr)
            return False, f"⚠️ Error en ffmpeg: {stderr}"

    @staticmethod
    def _default_video_args(formato_destino: str):
        fmt = (formato_destino or '').lower()
        if fmt in ('mp4', 'mov', 'm4v'):
            return ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart']
        if fmt == 'mkv':
            return ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k']
        if fmt == 'webm':
            return ['-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '32', '-c:a', 'libopus', '-b:a', '128k']
        if fmt == 'avi':
            return ['-c:v', 'mpeg4', '-q:v', '5', '-c:a', 'libmp3lame', '-b:a', '192k']
        if fmt == 'wmv':
            return ['-c:v', 'wmv2', '-c:a', 'wmav2']
        if fmt == 'flv':
            return ['-c:v', 'flv', '-c:a', 'libmp3lame', '-b:a', '128k']
        if fmt == '3gp':
            return ['-c:v', 'h263', '-c:a', 'aac', '-b:a', '96k']
        return ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k']

    @staticmethod
    def convertir(ruta_origen, ruta_destino, formato_destino=None):
        try:
            if formato_destino is None:
                formato_destino = os.path.splitext(ruta_destino)[1].lstrip('.').lower()
            extra_args = VideoFormats._default_video_args(formato_destino)
            ok, msg = VideoFormats._run_ffmpeg(ruta_origen, ruta_destino, extra_args=extra_args)
            return msg
        except Exception as e:
            return f"⚠️ Error con {os.path.basename(ruta_origen)}: {e}"
