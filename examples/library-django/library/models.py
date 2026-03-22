from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True, default="")
    born = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=300)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    published = models.DateField(null=True, blank=True)
    isbn = models.CharField(max_length=13, blank=True, default="")
    genre = models.CharField(max_length=100, blank=True, default="")
    summary = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
