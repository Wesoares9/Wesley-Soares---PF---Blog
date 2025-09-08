from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('send/', views.send_message, name='send-message'),
    path('<int:pk>/', views.message_detail, name='message-detail'),
]
