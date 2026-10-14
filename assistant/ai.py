"""
assistant/ai.py
Capa de integración con la API de Claude (Anthropic). Aquí vive toda
la lógica de "IA" de URBIX: el chatbot y el buscador inteligente.

Si no hay ANTHROPIC_API_KEY configurada, las funciones devuelven un
mensaje explicando cómo activarlo, en vez de romper la página.
"""
import json
import os

from django.conf import settings

from routes.models import Route
from restaurants.models import Restaurant
from hotels.models import Hotel
from tourism.models import TouristPlace
from events.models import Event

MODEL = 'claude-sonnet-5'


def _get_client():
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    return anthropic.Anthropic(api_key=api_key)


def _build_context():
    """
    Arma un resumen en texto plano de lo que hay en la base de datos,
    para que Claude pueda responder con información real de URBIX en
    lugar de inventar datos.
    """
    lines = ['# Datos actuales de URBIX (Popayán)\n']

    lines.append('## Rutas de transporte')
    for r in Route.objects.filter(is_active=True):
        lines.append(f'- {r.name}: {r.origin} → {r.destination}, dura ~{r.duration_minutes} min')

    lines.append('\n## Restaurantes')
    for r in Restaurant.objects.filter(is_active=True)[:30]:
        lines.append(f'- {r.name} ({r.tag}, {r.price_range}) — {r.address}')

    lines.append('\n## Hoteles')
    for h in Hotel.objects.filter(is_active=True)[:30]:
        lines.append(f'- {h.name} — desde ${h.approx_price:,.0f}/noche — {h.address}')

    lines.append('\n## Lugares turísticos')
    for p in TouristPlace.objects.filter(is_active=True)[:30]:
        lines.append(f'- {p.name} ({p.tag})')

    lines.append('\n## Eventos próximos')
    for e in Event.objects.filter(is_active=True)[:20]:
        lines.append(f'- {e.name} — {e.place} — {e.start_at:%d/%m/%Y %H:%M}')

    return '\n'.join(lines)


CHATBOT_SYSTEM_PROMPT = """Eres el asistente virtual de URBIX, una app de movilidad
inteligente para Popayán, Colombia. Ayudas a los usuarios con rutas de bus,
horarios, restaurantes, hoteles, lugares turísticos y eventos de la ciudad.

Reglas:
- Responde SIEMPRE en español, de forma breve, cálida y concreta (máximo 4-5 líneas).
- Usa solamente la información de contexto que se te da abajo; si no tienes el
  dato, dilo con honestidad y sugiere revisar la sección correspondiente de la app.
- No inventes precios, horarios ni direcciones que no estén en el contexto.
- Si preguntan algo fuera de temas de URBIX (clima, tareas, etc.), responde
  amablemente que solo puedes ayudar con temas de movilidad y turismo en Popayán.

Contexto actual:
{context}
"""


def ask_chatbot(message, history=None):
    """
    history: lista de dicts [{'role': 'user'|'assistant', 'content': '...'}, ...]
    Retorna un string con la respuesta.
    """
    client = _get_client()
    if client is None:
        return ('El chatbot todavía no está activado. Pídele a tu administrador que '
                'configure ANTHROPIC_API_KEY en el archivo .env (ver README).')

    messages = (history or []) + [{'role': 'user', 'content': message}]

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=500,
            system=CHATBOT_SYSTEM_PROMPT.format(context=_build_context()),
            messages=messages,
        )
        return response.content[0].text
    except Exception as exc:  # nunca romper la página por un fallo de la API
        return f'Hubo un problema hablando con el asistente ({exc}). Intenta de nuevo en un momento.'


SEARCH_SYSTEM_PROMPT = """Eres el motor de búsqueda inteligente de URBIX (Popayán).
El usuario escribe una frase en lenguaje natural describiendo lo que busca.
Debes devolver SOLO un JSON (sin texto adicional, sin markdown) con esta forma:

{{
  "category": "restaurantes" | "hoteles" | "turismo" | "eventos" | "rutas",
  "keywords": ["palabra1", "palabra2"],
  "price_hint": "bajo" | "medio" | "alto" | null,
  "explanation": "una frase corta en español explicando qué vas a mostrar"
}}

Elige la categoría que mejor corresponda a la intención del usuario.
"keywords" son palabras clave para buscar por nombre o descripción (en español,
sin tildes si es más simple). Si el usuario menciona presupuesto (barato,
económico, lujo, etc.) usa price_hint; si no, usa null.

Contexto de categorías disponibles en URBIX:
{context}
"""


def smart_search(query):
    """
    Convierte una búsqueda en lenguaje natural en resultados reales de la BD.
    Retorna (explanation:str, category:str, results:list[model instances]).
    """
    client = _get_client()
    if client is None:
        return ('La búsqueda inteligente todavía no está activada (falta configurar '
                'ANTHROPIC_API_KEY).', None, [])

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=SEARCH_SYSTEM_PROMPT.format(context=_build_context()),
            messages=[{'role': 'user', 'content': query}],
        )
        raw = response.content[0].text.strip()
        raw = raw.removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        parsed = json.loads(raw)
    except Exception as exc:
        return (f'No se pudo interpretar la búsqueda ({exc}).', None, [])

    category = parsed.get('category')
    keywords = parsed.get('keywords') or []
    explanation = parsed.get('explanation', '')

    results = []
    q_filter = None
    from django.db.models import Q
    for kw in keywords:
        clause = Q(name__icontains=kw) | Q(description__icontains=kw) if kw else None
        if clause:
            q_filter = clause if q_filter is None else (q_filter | clause)

    if category == 'restaurantes':
        qs = Restaurant.objects.filter(is_active=True)
        results = list(qs.filter(q_filter) if q_filter else qs[:9])
    elif category == 'hoteles':
        qs = Hotel.objects.filter(is_active=True)
        results = list(qs.filter(q_filter) if q_filter else qs[:9])
    elif category == 'turismo':
        qs = TouristPlace.objects.filter(is_active=True)
        results = list(qs.filter(q_filter) if q_filter else qs[:9])
    elif category == 'eventos':
        qs = Event.objects.filter(is_active=True)
        results = list(qs.filter(q_filter) if q_filter else qs[:9])
    elif category == 'rutas':
        qs = Route.objects.filter(is_active=True)
        results = list(qs.filter(q_filter) if q_filter else qs[:9])

    return explanation, category, results
