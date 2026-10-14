"""assistant/views.py"""
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .ai import ask_chatbot, smart_search
from .models import ChatMessage


@login_required
@require_POST
def chat_api(request):
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    message = (data.get('message') or '').strip()
    if not message:
        return JsonResponse({'error': 'Mensaje vacío'}, status=400)

    # Construimos el historial reciente para que el chatbot tenga contexto
    recent = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:10]
    history = [{'role': m.role, 'content': m.content} for m in reversed(recent)]

    ChatMessage.objects.create(user=request.user, role=ChatMessage.Role.USER, content=message)
    reply = ask_chatbot(message, history=history)
    ChatMessage.objects.create(user=request.user, role=ChatMessage.Role.ASSISTANT, content=reply)

    return JsonResponse({'reply': reply})


def search_page(request):
    query = request.GET.get('q', '').strip()
    explanation, category, results = ('', None, [])
    if query:
        explanation, category, results = smart_search(query)
    return render(request, 'assistant/buscador.html', {
        'query': query, 'explanation': explanation, 'category': category, 'results': results,
    })
