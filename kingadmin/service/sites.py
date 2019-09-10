from functools import wraps

from django.conf.urls import url
from django.contrib.admin.sites import AlreadyRegistered
from django.db.models import Q
from django.forms.fields import DateTimeField, DateField, TimeField
from django.shortcuts import render
from django.http.response import JsonResponse
from django.urls import reverse
from django.db.models import ForeignKey, ManyToManyField
from django.utils.safestring import mark_safe
from django.forms.models import modelform_factory

from kingadmin.fields import Field
from kingadmin.settings import admin_settings
from kingadmin.utils.paginator import Paginator


class Option(object):
    """
    条件筛选类
    """

    def __init__(self, field, condition=[], is_multiple=False, text_func=None, value_func=None):
        """
        初始化条件筛选
        :param field:筛选字段
        :param condition:筛选字段过滤 列表每个元素表示或的关系，每个元素（字典）表示且的关系
        :param is_multiple:条件筛选时 同一项 是否可以 多选 默认 False
        :param text_func:筛选字段网页显示内容
        :param value_func:筛选字段过滤
        """
        self.field = field
        self.choices = False
        self.text_func = text_func
        self.value_func = value_func
        self.is_multiple = is_multiple

        q = Q()
        q.connector = "OR"
        for filter in condition:
            q.children.append(Q(**filter))
        self.filter = q

    def get_queryset(self, _field, model, params):
        if isinstance(_field, ForeignKey) or isinstance(_field, ManyToManyField):
            row = Row(_field.rel.model.objects.filter(self.filter), self, params, _field.verbose_name, model)
        else:
            if _field.choices:
                self.choices = True
                row = Row(_field.choices, self, params, _field.verbose_name, model)
            else:
                row = Row(model.objects.filter(self.filter), self, params, _field.verbose_name, model)
        return row

    def get_text(self, item):
        """
        对每一个数据进行取值
        :param item: 每一个数据
        :return:
        """
        if self.text_func:
            return self.text_func(item)
        else:
            if self.choices:
                return item[1]
            else:
                if hasattr(item, self.field):
                    return getattr(item, self.field)
                else:
                    return str(item)

    def get_value(self, item, model):
        """
        对每一个数据进行取值，便于进行过滤
        :param item: 当前条件筛选项的其中一个数据
        :param model: 当前url 操作哪个model
        :return:
        """
        if self.text_func:
            return self.value_func(item)
        else:
            if self.choices:
                return str(item[0])
            else:
                if isinstance(item, model):
                    if hasattr(item, self.field):
                        return getattr(item, self.field)
                    else:
                        return str(item)
                else:
                    return str(item.pk)


class Row(object):
    """
    条件筛选每行数据统一格式
    """

    def __init__(self, data_list, option, params, verbose_name, model):
        """
        条件筛选类初始化
        :param data_list: 每行数据 queryset或choices
        :param option: Option类
        :param params: get请求参数
        :param verbose_name: 字段的verbose_name
        :param model: 当前url 操作哪个model
        """
        self.data_list = data_list
        self.option = option
        self.params = params
        self.verbose_name = verbose_name
        self.model = model

    def __iter__(self):
        """
        渲染条件筛选一行数据
        :return:
        """
        is_multiple = "(可多选)" if self.option.is_multiple else ""
        yield mark_safe(f'<label class="layui-form-label">{self.verbose_name}{is_multiple}：</label>')

        params_list = self.params.getlist(self.option.field, [])
        query_dict = self.params.copy()

        if params_list:
            query_dict.pop(self.option.field)
            yield mark_safe(f'<a href="?{query_dict.urlencode()}" class="layui-btn layui-btn-primary">全部</a>')
        else:
            yield mark_safe('<a href="javascript:void()" class="layui-btn">全部</a>')

        query_dict = self.params.copy()
        for data in self.data_list:
            field_value = self.option.get_value(data, self.model)
            params_list = self.params.getlist(self.option.field, [])

            # 是否可以多选项过滤
            if self.option.is_multiple:

                if field_value in params_list:
                    params_list.remove(field_value)

                    if params_list:
                        query_dict.setlist(self.option.field, params_list)
                    else:
                        query_dict.pop(self.option.field)

                    yield mark_safe(
                        f'''<a 
                               href="?{query_dict.urlencode()}" 
                               class="layui-btn"
                           >
                               {self.option.get_text(data)}
                           </a>''')

                else:
                    params_list.append(field_value)
                    query_dict.setlist(self.option.field, params_list)

                    yield mark_safe(
                        f'''<a 
                               href="?{query_dict.urlencode()}" 
                               class="layui-btn layui-btn-primary"
                            >
                               {self.option.get_text(data)}
                            </a>''')
            else:
                query_dict[self.option.field] = field_value
                if query_dict[self.option.field] in params_list:
                    yield mark_safe(
                        f'''<a 
                                href="?{query_dict.urlencode()}" 
                                class="layui-btn"
                            >
                                {self.option.get_text(data)}
                            </a>''')
                else:
                    yield mark_safe(
                        f'''<a 
                                href="?{query_dict.urlencode()}" 
                                class="layui-btn layui-btn-primary"
                            >
                                {self.option.get_text(data)}
                            </a>''')


class ModelAdmin(object):
    list_display = []  # 列表展示字段
    list_order = []  # 结果排序 升序 字段名 降序 -字段名
    checkbox = False  # 是否启动第一列复选框
    action_list = ["bulk_delete", ]  # 批量操作 需要checkbox=True 默认为批量删除

    options = []  # 操作列 可选值 edit delete 也可以自定义方法 默认 []
    """
    options = ["edit", "delete", "switch"]

    def switch(self, model, pk):
        # model 当前模型对象
        # pk 当前行数据的主键
        # return 返回字符串格式
        ...

    """

    add_button = True  # 是否显示添加按钮
    model_form_class = None  # modelForm类
    fields = "__all__"  # forms.ModelForm中Meta中的 fields

    list_search = []  # 搜索字段
    list_filter = []  # 条件筛选字段 可以是字段字符串 或者 是 Option类

    def __init__(self, model, admin_site):
        self.model = model
        self.admin_site = admin_site

    @property
    def list_display_fields(self):
        """
        对list_display（列表展示字段）进行处理
        """
        fields = []
        for field in self.list_display:
            field_obj = getattr(self, field, None)
            if isinstance(field_obj, Field):
                field_obj.bind(field, self)
                fields.append(field_obj)
            else:
                fields.append(field)

        # TODO 如果出现瓶颈, 可以考虑使用 cache, 避免出现重复计算
        return fields

    def get_checkbox(self) -> bool:
        """
        可用于子类判断是否有权限批量删除
        """
        return self.checkbox

    def get_add_button(self) -> bool:
        """
        可用于子类判断是否有权限添加数据
        """
        return self.add_button

    def get_options(self) -> list:
        """
        可用于子类判断是否有权限编辑或删除
        """
        return self.options

    def get_list_display(self) -> list:
        """
        用于子类继承，根据不同用户展示不同数据，可以跨表查询
        """
        return self.list_display_fields

    def get_list_order(self) -> list:
        """
        用于子类继承，根据不同用户进行排序，可以跨表排序
        """
        return self.list_order

    def get_model_form_class(self) -> object:
        """
        用于子类继承，自定义modelForm
        :return:
        """
        if self.model_form_class:
            return self.model_form_class

        return modelform_factory(self.model, fields=self.fields)

    def get_action_list(self) -> list:
        """
        用于子类继承，获取批量操作操作
        """
        action_list = []
        for func in self.action_list:
            if hasattr(self, func):
                fun = getattr(self, func)
                action_list.append({"value": fun.__name__, "label": fun.label})

        return action_list

    def get_list_search(self):
        """
        用于子类继承，获取关键字搜索字段，可以跨表过滤
        """
        return self.list_search

    def get_list_filter(self):
        """
        用于子类继承，获取过滤字段，可以跨表过滤
        """
        list_filter = []
        for option in self.list_filter:
            if isinstance(option, str):
                list_filter.append(Option(option))
            elif isinstance(option, Option):
                list_filter.append(option)

        return list_filter

    def bulk_delete(self, request):
        pk_list = request.POST.getlist("pk")
        self.model.objects.filter(pk__in=pk_list).delete()

    bulk_delete.label = "批量删除"

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            url("^$", self.wrapper(self.changelist_view), name="%s_%s_changelist" % info),
            url("^add/$", self.wrapper(self.add_view), name="%s_%s_add" % info),
            url("^delete/(?P<pk>\d+)$", self.wrapper(self.delete_view), name="%s_%s_delete" % info),
            url("^change/(?P<pk>\d+)$", self.wrapper(self.change_view), name="%s_%s_change" % info)
        ]

        extra_url = self.extra_url()
        if extra_url:
            urlpatterns.extend(extra_url)

        return urlpatterns

    def extra_url(self) -> list:
        pass

    @property
    def urls(self):
        return self.get_urls(), None, None

    def get_list_filter_conditions(self, request):
        """
        获取过滤条件筛选的 条件
        :return:
        """
        comb_condition = {}
        for option in self.get_list_filter():
            condition = request.GET.getlist(option.field)
            if condition:
                comb_condition[f"{option.field}__in"] = condition

        return comb_condition

    def get_search_queryset(self, request, queryset):
        """
        查询关键字的 queryset
        """
        keyword = request.GET.get(admin_settings.SEARCH_PARAM, "")
        if keyword:
            query = Q()
            query.connector = "OR"
            for filter in self.get_list_search():
                query.children.append((filter + "__contains", keyword))
            queryset = queryset.filter(query)

        return queryset

    def get_list_filter_rows(self, request):
        """
        获取条件筛选的 数据
        """
        list_filter_rows = []
        for option in self.get_list_filter():
            _field = self.model._meta.get_field(option.field)
            row = option.get_queryset(_field, self.model, request.GET)
            list_filter_rows.append(row)
        return list_filter_rows

    def changelist_view(self, request):
        """
        列表展示页面
        """
        info = self.model._meta.app_label, self.model._meta.model_name

        if request.method == "POST":
            # 进行批量处理
            bulk = request.POST.get("bulk")

            if bulk:
                if hasattr(self, bulk):
                    res = getattr(self, bulk)(request)
                    if res:
                        return res

        queryset = self.model.objects.all()

        # 搜索关键字
        queryset = self.get_search_queryset(request, queryset)
        # 排序
        queryset = queryset.order_by(*self.get_list_order())

        # 条件筛选
        comb_condition = self.get_list_filter_conditions(request)
        queryset = queryset.filter(**comb_condition).distinct()

        # 分页
        paginator = Paginator(queryset, request.GET)
        page_html, queryset = paginator.get_html()

        # 获取url搜索参数
        search_param = admin_settings.SEARCH_PARAM

        data = {
            "table_data": {
                "queryset": queryset,
                "list_display": self.get_list_display(),
                "has_checkbox": self.get_checkbox(),
                "options": self.get_options(),
                "model": self.model,
                "admin_class": self,
            },
            "has_checkbox": self.get_checkbox(),
            "has_add_button": self.get_add_button(),
            "add_url": reverse("kingadmin:%s_%s_add" % info),
            "action_list": self.get_action_list(),
            "list_filter": self.get_list_search(),
            "keyword": request.GET.get(search_param, ""),
            "page_html": page_html,
            "list_filter_rows": self.get_list_filter_rows(request),
            "search_param": search_param,
        }

        return render(request, "kingadmin/changelist.html", data)

    def add_view(self, request):
        """
        添加数据页面
        """
        if request.method == "GET":
            AddModelForm = self.get_model_form_class()
            forms = AddModelForm()

            datetime_fields = []
            for form in forms:
                if isinstance(form.field, DateTimeField):
                    datetime_fields.append({"elem": form.id_for_label, "type": "datetime"})
                elif isinstance(form.field, DateField):
                    datetime_fields.append({"elem": form.id_for_label, "type": "date"})
                elif isinstance(form.field, TimeField):
                    datetime_fields.append({"elem": form.id_for_label, "type": "time"})

            info = self.model._meta.app_label, self.model._meta.model_name
            add_url = reverse("kingadmin:%s_%s_add" % info)
            return render(request, "kingadmin/form.html", {
                "fields": forms,
                "add_change_url": add_url,
                "datetime_fields": datetime_fields
            })

        elif request.method == "POST":
            AddModelForm = self.get_model_form_class()
            forms = AddModelForm(request.POST)
            if forms.is_valid():
                forms.save()
                return JsonResponse({"code": 200, "msg": "添加成功"})

            return JsonResponse({"code": 201, "msg": "添加失败", "errors": forms.errors})
        else:
            return JsonResponse({"code": 403, "msg": "请求方法不被允许"})

    def delete_view(self, request, pk):
        """
        删除单条数据
        """
        obj = self.model.objects.filter(pk=pk)
        result = obj.delete()
        if result:
            return JsonResponse({"code": 200, "msg": "删除成功"})
        else:
            return JsonResponse({"code": 401, "msg": "删除失败"})

    def change_view(self, request, pk):
        """
        修改数据页面
        """
        if request.method == "GET":
            obj = self.model.objects.filter(pk=pk).first()
            if obj:
                ChangeModelForm = self.get_model_form_class()
                forms = ChangeModelForm(instance=obj)

                datetime_fields = []
                for form in forms:
                    if isinstance(form.field, DateTimeField):
                        datetime_fields.append({"elem": form.id_for_label, "type": "datetime"})
                    elif isinstance(form.field, DateField):
                        datetime_fields.append({"elem": form.id_for_label, "type": "date"})
                    elif isinstance(form.field, TimeField):
                        datetime_fields.append({"elem": form.id_for_label, "type": "time"})

                info = self.model._meta.app_label, self.model._meta.model_name
                change_url = reverse("kingadmin:%s_%s_change" % info, kwargs={"pk": pk})
                return render(request, "kingadmin/form.html", {
                    "fields": forms,
                    "add_change_url": change_url,
                    "datetime_fields": datetime_fields
                })

            else:
                return JsonResponse({"code": 401, "msg": "数据错误"})

        elif request.method == "POST":
            obj = self.model.objects.filter(pk=pk).first()
            if obj:
                ChangeModelForm = self.get_model_form_class()
                forms = ChangeModelForm(data=request.POST, instance=obj)
                if forms.is_valid():
                    forms.save()
                    return JsonResponse({"code": 200, "msg": "修改成功"})
                return JsonResponse({"code": 201, "msg": "修改失败", "errors": forms.errors})
            else:
                return JsonResponse({"code": 401, "msg": "数据错误"})
        else:
            return JsonResponse({"code": 403, "msg": "请求方法不被允许"})

    def wrapper(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            return func(*args, **kwargs)

        return inner


class AdminSite(object):
    namespace = "kingadmin"

    def __init__(self):
        self._registry = {}

    def register(self, model, admin_class=None):
        if admin_class is None:
            admin_class = ModelAdmin

        if model in self._registry:
            raise AlreadyRegistered('The model %s is already registered' % model.__name__)

        self._registry[model] = admin_class(model, self)

    def get_urls(self):
        urlpatterns = []

        for model, admin_site in self._registry.items():
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            urlpatterns.append(
                url("^%s/%s/" % (app_label, model_name), admin_site.urls)
            )

        urlpatterns += [url("^$", self.home, name="home")]
        urlpatterns += [url("^welcome/$", self.welcome, name="welcome")]
        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), "kingadmin", self.namespace

    def home(self, request):
        return render(request, "kingadmin/home.html")

    def welcome(self, request):
        return render(request, "kingadmin/welcome.html")


site = AdminSite()
