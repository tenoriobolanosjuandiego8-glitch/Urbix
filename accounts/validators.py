"""
accounts/validators.py
Validadores reutilizables de seguridad para archivos subidos por
usuarios (fotos de perfil, portadas de negocio, galerías). Sin esto,
cualquier usuario podría subir un archivo disfrazado de imagen
(ej. un .php o .exe con extensión .jpg) o un archivo gigante que
sature el servidor.
"""
import os

from django.core.exceptions import ValidationError

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_IMAGE_SIZE_MB = 5


def validate_image_file(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f'Formato no permitido ({ext}). Usa JPG, PNG, WEBP o GIF.'
        )

    if file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f'La imagen no puede pesar más de {MAX_IMAGE_SIZE_MB} MB.')

    # Verifica que el contenido real del archivo sea una imagen válida,
    # no solo que tenga extensión de imagen (evita archivos disfrazados).
    try:
        from PIL import Image
        file.seek(0)
        img = Image.open(file)
        img.verify()
        file.seek(0)
    except Exception:
        raise ValidationError('El archivo no es una imagen válida o está dañado.')
