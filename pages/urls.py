from django.urls import path
from .views import (
    PostListView, PostDetailView, PostCreateView, PostUpdateView, PostDeleteView,
    HomeView, AboutView
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
    path('pages/', PostListView.as_view(), name='post-list'),
    path('pages/create/', PostCreateView.as_view(), name='post-create'),
    path('pages/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('pages/<int:pk>/edit/', PostUpdateView.as_view(), name='post-edit'),
    path('pages/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),
]
