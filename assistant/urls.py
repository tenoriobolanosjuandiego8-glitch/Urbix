from django.urls import path
from . import views

app_name = 'assistant'

urlpatterns = [
    path('chat/', views.chat_api, name='chat_api'),
    path('buscar/', views.search_page, name='search'),
]
