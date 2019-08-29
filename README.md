## 后台管理系统 
kingadmin基于X-admin(前端),django-1.11(后端)开发。kingadmin用于快速搭建后台管理系统。

### v0.1.1功能
-
1. 修复分页页码缺少错误
2. 增加展示页面操作列可以自定义
3. 增加全局配置类
    - 在项目文件settings.py文件中增加配置信息
    ```python
        KING_ADMIN = {
            'PRE_PAGE_NUM': 2,  # 每页显示多少条数据
            'PAGE_COUNT': 5,  # 分页显示几个页面
            'PAGE_QUERY': 'p',  # 页码url查询参数
   
            'SEARCH_PARAM': 'keyword', # 关键搜索参数
        }
   ```
   - 目前仅支持`分页`、`关键字搜索`相关功能配置，后续添加其他工鞥

### v0.1.0功能 
-
1. 数据展示页面
    1. 单条操作数据
    2. 批量操作数据
2. 数据增加页面
3. 数据删除功能
4. 数据修改页面

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
       list_display = ["title", "publisher", "price", "authors"] # 列表页面展示的字段 目前不支持跨表查自定义 默认 []
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
       
       
       def list_authors(self, instance):  # instance 表示该行数据的 model实例
           return "-".join([str(item) for item in instance.editorial_staff.all()] or [])
   	
       def bulk_init(self, request): # 自定义批量操作
           pk_list = request.POST.getlist("pk")
           self.model.objects.filter(pk__in=pk_list).update(name="xxx")
           
       bulk_init.label = "批量初始化"
       
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
            <a onclick="xadmin.add_tab('图书列表','{% url 'app01_book_changelist' %}')">
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
                    <a onclick="xadmin.add_tab('出版社列表','{% url "app01_publisher_changelist" %}')">
                        <i class="iconfont">&#xe6a7;</i>
                        <cite>出版社列表</cite></a>
                </li>
            </ul>
        </li>
    </ul>
</li>
<!-- 自定义路由结束-->
```

