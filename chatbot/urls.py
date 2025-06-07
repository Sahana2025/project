from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('choose/', views.choose_category, name='choose_category'),
    path('chat/plant/', views.plant_chat, name='plant_chat'),
    path('chat/animal/', views.animal_chat, name='animal_chat'),
    path('chat/human/', views.human_chat, name='human_chat'),
]
