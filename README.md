## 后台管理系统 
kingadmin基于X-admin(前端),django-1.11(后端)开发。kingadmin用于快速搭建后台管理系统。


### 开发环境
> win10 django-1.11.20 python 3.7.3

### 使用说明

1. 项目``settings.py`中INSTALLED_APPS中添加kingadmin
```python

INSTALLED_APPS = [
    ...
    'kingadmin.apps.KingadminConfig',
    ...
]
```
2. 项目``urls.py`中添加路由
```python
from kingadmin.service.sites import site

urlpatterns = [
    url(r'^admin/', site.urls),
]
```

3. 在需要展示的app包下，增加``kingadmin.py`文件


4. `kingadmin.py`文件中可配置如下信息

   1. 注册admin

   ```python
   from kingadmin.service.sites import ModelAdmin, site
   
   site.register(models.Book)
   ```

   2. 自定义配置

   ```python
   from django import forms
   
   from app01 import models
   from kingadmin import fields
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
       list_display = ["title", "publisher", "price", "authors", "test"] # 列表页面展示的字段 目前不支持跨表查自定义 默认 []
       list_order = ["id", ] # 排序的字段 field 升序 -filed 降序 默认 []
       checkbox = True # 是否显示复选框  批量操作时，需要此项为True 默认 False
       action_list = ["bulk_delete", "bulk_init"] # 批量操作函数 默认 ["bulk_delete", ] 批量删除
       options = ["edit", "delete", ] # 操作列 可选值 edit delete 也可以自定义方法 默认 [] 
       """
       options = ["edit", "delete", "switch"]
 
       def switch(self, model, pk):
           # model 当前模型对象
           # pk 当前行数据的主键
           # return 返回字符串格式
           ...
       
       """
       add_button = True  # 是否显示添加按钮 默认 True
       model_form_class = BookModelForm # 自定义form表单进行页面渲染 默认 None
       fields = "__all__"  # forms.ModelForm中Meta中的 fields 默认form表单中fields
       
       list_search = ["title", "publisher__name"] # 可搜索字段 默认 []
       list_filter = [  # 条件筛选字段 可以是字段字符串 或者 是 Option类
           Option("name", condition=[{"name__contains": "我"}, {"id__lt": 4}]),
           "city",
           Option("address", ),
           Option("editorial_staff", is_multiple=True),
       ] 
       '''
       可以自定义 get_add_button 等，重写父类的方法，用于不同权限的展示
       
       
       Option类初始化函数
       
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
       '''
       
       
       def list_authors(self, instance):  # instance 表示该行数据的 model实例 可以用于展示多个值的显示格式
           return "-".join([str(item) for item in instance.editorial_staff.all()] or [])
           # return instance.editorial_staff.count() # 显示个数
   	
       def bulk_init(self, request): # 自定义批量操作
           pk_list = request.POST.getlist("pk")
           self.model.objects.filter(pk__in=pk_list).update(name="xxx")
           
       bulk_init.label = "批量初始化"
       
       test = fields.StringField(source="editorial_staff.first.name", verbose_name="测试")
       '''
       fields目标提供一下方法
       1. StringField 显示获取的数据字符串
       source用于指定获取的字段值，verbose_name用于显示表头标题
       2. HtmlField 渲染一段html代码
       template指定渲染html页面的文件
       3. ImgHtmlField 渲染一张图片
       img_domain图片的站点, width图片宽, height图片高
       4. MethodField 自定义内容
       类中需要实现 get_{field} 方法
       eg:
       def get_xxx(self, instance): # instance是该行的实例对象
           return "xxx"
       '''
       
   site.register(models.Book, BookAdmin)
   ```

   5. 在kingadmin/templates/kingadmin/home.html 中添加需要展示的路由

```html
<!-- 自定义路由开始 -->
<li>
    <a href="javascript:;">
        <i class="iconfont left-nav-li" lay-tips="图书管理">&#xe6b8;</i>
        <cite>图书管理</cite>
        <i class="iconfont nav_right">&#xe697;</i></a>
    <ul class="sub-menu">
        <li>
            <a onclick="xadmin.add_tab('图书列表','{% url 'kingadmin:app01_book_changelist' %}')">
                <i class="iconfont">&#xe6a7;</i>
                <cite>图书列表</cite></a>
        </li>
        <li>
            <a href="javascript:;">
                <i class="iconfont">&#xe70b;</i>
                <cite>出版社管理</cite>
                <i class="iconfont nav_right">&#xe697;</i></a>
            <ul class="sub-menu">
                <li>
                    <a onclick="xadmin.add_tab('出版社列表','{% url "kingadmin:app01_publisher_changelist" %}')">
                        <i class="iconfont">&#xe6a7;</i>
                        <cite>出版社列表</cite></a>
                </li>
            </ul>
        </li>
    </ul>
</li>
<!-- 自定义路由结束-->
```

