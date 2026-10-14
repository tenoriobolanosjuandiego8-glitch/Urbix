from django.urls import path
from . import views

app_name = 'interactions'

urlpatterns = [
    path('favoritos/', views.favorite_list, name='favorite_list'),
    path('historial/', views.history_list, name='history_list'),
    path('favorito/<str:app_label>/<str:model>/<int:pk>/', views.favorite_toggle, name='favorite_toggle'),
    path('comentar/<str:app_label>/<str:model>/<int:pk>/', views.comment_create, name='comment_create'),
    path('comentario/<int:pk>/editar/', views.comment_edit, name='comment_edit'),
    path('comentario/<int:pk>/eliminar/', views.comment_delete, name='comment_delete'),
    path('comentario/<int:pk>/denunciar/', views.flag_comment, name='flag_comment'),
    path('calificar/<str:app_label>/<str:model>/<int:pk>/', views.rate_object, name='rate_object'),
]
