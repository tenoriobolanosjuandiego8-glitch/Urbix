"""
config/security_middleware.py
Cabeceras de seguridad adicionales que Django no agrega por defecto.
No requiere ninguna librería nueva (evita más dolores de instalación).

- Content-Security-Policy: limita de dónde puede cargar la página
  scripts/estilos/imágenes, mitigando XSS incluso si algún dato de
  usuario se escapa mal en algún template.
- Referrer-Policy: evita filtrar la URL completa (con tokens en la
  query string, por ejemplo) a sitios externos al hacer clic en enlaces.
- Permissions-Policy: desactiva APIs del navegador que la app no usa
  (cámara, micrófono, etc.), reduciendo superficie de ataque si algún
  script de terceros se ve comprometido.
"""


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Dominios externos que la app sí necesita (CDNs, mapas, IA).
        self.csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://unpkg.com "
            "https://cdn.jsdelivr.net https://api.open-meteo.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com "
            "https://unpkg.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self' https://api.openrouteservice.org https://api.open-meteo.com "
            "https://nominatim.openstreetmap.org https://*.tile.openstreetmap.org; "
            "frame-ancestors 'self';"
        )

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = self.csp
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'camera=(), microphone=(), payment=()'
        response.setdefault('X-Content-Type-Options', 'nosniff')
        return response
