from django.db import models
from django.utils import timezone


# Create your models here.
class Book(models.Model):
    title = models.CharField(max_length=20, verbose_name="书名")
    publisher = models.ForeignKey("Publisher", verbose_name="出版社")

    def __str__(self):
        return self.title


class Authors(models.Model):
    name = models.CharField(max_length=20)
    book = models.ManyToManyField("Book")

    def __str__(self):
        return self.name


class Publisher(models.Model):
    name = models.CharField(max_length=50, verbose_name="出版社名称")
    city_choices = (
        (1, "北京"),
        (2, "上海"),
        (3, "深圳"),
    )
    city = models.IntegerField(verbose_name="城市", choices=city_choices, default=1)
    address = models.CharField(max_length=50, verbose_name="地址", default="")
    editorial_staff = models.ManyToManyField(verbose_name="编辑", to="EditorialStaff")
    owner = models.ManyToManyField(verbose_name="拥有人", to="Owner")
    create_date = models.DateTimeField(verbose_name="创建时间", default=timezone.now())

    def __str__(self):
        return self.name


class Owner(models.Model):
    name = models.CharField(max_length=20, verbose_name="姓名")

    def __str__(self):
        return self.name


class EditorialStaff(models.Model):
    name = models.CharField(max_length=20, verbose_name="姓名")

    def __str__(self):
        return self.name
