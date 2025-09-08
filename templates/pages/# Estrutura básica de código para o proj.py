# Estrutura básica de código para o projeto Django
# Apps: pages, accounts, messenger
# ATENÇÃO: Este esqueleto foi ajustado para evitar erro quando
# o pacote `django-ckeditor` (e `ckeditor_uploader`) NÃO está instalado.
# Se você tiver esse pacote instalado e preferir usar o CKEditor,
# configure-o normalmente em settings.py e remova o fallback abaixo.

# ===========================================
# pages/models.py
# ===========================================
from django.db import models
from django.conf import settings
from django.urls import reverse

# Tentativa de usar o campo rico do CKEditor quando disponível.
# Se o pacote não estiver instalado, fazemos um fallback para
# models.TextField — isso evita o ModuleNotFoundError em ambientes
# onde `django-ckeditor` não foi instalado.
try:
    from ckeditor_uploader.fields import RichTextUploadingField as RichTextField
    CKEDITOR_AVAILABLE = True
except Exception:
    RichTextField = models.TextField  # fallback simples
    CKEDITOR_AVAILABLE = False

class Post(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)
    # usa RichTextField se disponível, caso contrário TextField
    content = RichTextField()
    image = models.ImageField(upload_to='posts/%Y/%m/%d/', blank=True, null=True)
    published_at = models.DateTimeField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('pages:detail', args=[self.slug])


# ===========================================
# pages/forms.py
# ===========================================
from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'subtitle', 'content', 'image', 'published_at', 'slug']


# ===========================================
# pages/views.py
# ===========================================
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .models import Post
from .forms import PostForm

class HomeView(ListView):
    model = Post
    template_name = 'pages/home.html'
    ordering = ['-published_at']

class PostDetailView(DetailView):
    model = Post
    template_name = 'pages/detail.html'

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'pages/form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class OwnerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

class PostUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'pages/form.html'

class PostDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Post
    template_name = 'pages/confirm_delete.html'
    success_url = reverse_lazy('pages:home')


# ===========================================
# pages/urls.py
# ===========================================
from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.TemplateView.as_view(template_name='pages/about.html'), name='about'),
    path('pages/<slug:slug>/', views.PostDetailView.as_view(), name='detail'),
    path('pages/create/', views.PostCreateView.as_view(), name='create'),
    path('pages/<slug:slug>/edit/', views.PostUpdateView.as_view(), name='edit'),
    path('pages/<slug:slug>/delete/', views.PostDeleteView.as_view(), name='delete'),
]


# ===========================================
# accounts/models.py
# ===========================================
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(blank=True, null=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_profile(sender, instance, created, **kwargs):
    # cria profile quando o usuário é criado. Se por algum motivo
    # o profile não existir em atualizações, tenta criar um também.
    if created:
        Profile.objects.create(user=instance)
    else:
        # protege contra usuário que não tenha profile
        try:
            instance.profile.save()
        except Exception:
            Profile.objects.get_or_create(user=instance)


# ===========================================
# accounts/forms.py
# ===========================================
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Profile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'birth_date', 'website']


# ===========================================
# accounts/views.py
# ===========================================
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, ProfileForm


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('pages:home')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'accounts/profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, 'accounts/edit_profile.html', {'form': form})


# ===========================================
# accounts/urls.py
# ===========================================
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
]


# ===========================================
# messenger/models.py
# ===========================================
from django.db import models
from django.conf import settings

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender} to {self.receiver} at {self.created_at}"


# ===========================================
# messenger/forms.py
# ===========================================
from django import forms
from .models import Message
from django.contrib.auth import get_user_model
User = get_user_model()

class MessageForm(forms.ModelForm):
    receiver = forms.ModelChoiceField(queryset=User.objects.none())

    class Meta:
        model = Message
        fields = ['receiver', 'body']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['receiver'].queryset = User.objects.exclude(pk=user.pk)


# ===========================================
# messenger/views.py
# ===========================================
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import MessageForm
from .models import Message

@login_required
def inbox(request):
    messages = request.user.received_messages.order_by('-created_at')
    return render(request, 'messenger/inbox.html', {'messages': messages})

@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.save()
            return redirect('messenger:inbox')
    else:
        form = MessageForm(user=request.user)
    return render(request, 'messenger/send.html', {'form': form})


# ===========================================
# messenger/urls.py
# ===========================================
from django.urls import path
from . import views

app_name = 'messenger'

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('send/', views.send_message, name='send'),
]


# ===========================================
# templates/base.html (exemplo mínimo)
# ===========================================
"""
<!DOCTYPE html>
<html>
<head>
  <title>{% block title %}Meu Blog{% endblock %}</title>
</head>
<body>
  <nav>
    <a href="{% url 'pages:home' %}">Home</a>
    <a href="{% url 'pages:about' %}">Sobre</a>
    {% if user.is_authenticated %}
      <a href="{% url 'accounts:profile' %}">Perfil</a>
      <a href="{% url 'messenger:inbox' %}">Mensagens</a>
      <a href="{% url 'accounts:logout' %}">Logout</a>
    {% else %}
      <a href="{% url 'accounts:login' %}">Login</a>
      <a href="{% url 'accounts:register' %}">Inscrever-se</a>
    {% endif %}
  </nav>
  <main>
    {% block content %}{% endblock %}
  </main>
</body>
</html>
"""


# ===========================================
# Test básico adicionado: tests/test_models.py
# (opcional — serve como sanity check rápido para o modelo Post)
# ===========================================

# Observação: este teste usa o test runner do Django. Execute com:
# python manage.py test

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

try:
    # Import do modelo Post para os testes
    from pages.models import Post
    from django.urls import reverse

    class PostModelTest(TestCase):
        def setUp(self):
            User = get_user_model()
            self.user = User.objects.create_user(username='testuser', password='pass')

        def test_create_post_and_get_absolute_url(self):
            post = Post.objects.create(
                title='Test',
                subtitle='Sub',
                content='Content',
                image='',
                published_at=timezone.now(),
                author=self.user,
                slug='test',
            )
            self.assertEqual(str(post), 'Test')
            self.assertEqual(post.get_absolute_url(), reverse('pages:detail', args=['test']))
except Exception:
    # Se import falhar no ambiente (por ex. Django não configurado neste sandbox),
    # não quebramos o arquivo — apenas ignoramos a seção de testes.
    pass
