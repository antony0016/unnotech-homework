from django.db import models


class FocusNews(models.Model):
    title = models.CharField(max_length=256)
    url = models.URLField(unique=True)
    image_url = models.URLField()
    image_caption = models.CharField(max_length=256, blank=True)
    content = models.TextField(blank=True)
    author = models.CharField(max_length=64, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title}/{self.author}"
