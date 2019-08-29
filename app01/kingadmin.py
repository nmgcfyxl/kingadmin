from django import forms

from app01 import models
from kingadmin.service.sites import ModelAdmin, site, Option


class BookModelForm(forms.ModelForm):
    class Meta:
        model = models.Book
        fields = "__all__"

    def clean_title(self):
        title = self.cleaned_data.get("title")
        if len(title) < 2:
            raise forms.ValidationError("长度小于2位")
        return title


class BookAdmin(ModelAdmin):
    list_display = ["title", "publisher"]
    list_order = ["id", ]
    checkbox = True
    options = ["edit", "delete", ]
    model_form_class = BookModelForm
    list_search = ["title", "publisher__name"]


class PublisherAdmin(ModelAdmin):
    list_display = ["id", "name", "city", "address", "editorial_staff"]
    options = ["delete", "edit"]
    checkbox = True
    list_filter = [
        Option("name", condition=[{"name__contains": "我"}, {"id__lt": 4}]),
        "city",
        Option("address", ),
        Option("editorial_staff", is_multiple=True),
    ]

    def list_editorial_staff(self, instance):  # instance 表示该行数据的 model实例
        return "-".join([str(item) for item in instance.editorial_staff.all()] or [])


site.register(models.Book, BookAdmin)
site.register(models.Publisher, PublisherAdmin)
site.register(models.EditorialStaff)
