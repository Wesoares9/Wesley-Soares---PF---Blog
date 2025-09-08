from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField

class Post(models.Model):
    title = models.CharField(max_length=200)            # CharField 1
    subtitle = models.CharField(max_length=200, blank=True)  # CharField 2
    content = RichTextField()                           # texto enriquecido (CKEditor)
    image = models.ImageField(upload_to='posts/%Y/%m/%d/', blank=True, null=True)
    published_at = models.DateTimeField(auto_now_add=True)  # data
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    

    def __str__(self):
        return self.title

   