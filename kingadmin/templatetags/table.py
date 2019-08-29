from django import template
from django.db.models import ManyToManyField
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()


def table_thead(info_dict):
    thead = []
    if info_dict["has_checkbox"]:
        thead.append(mark_safe('<input type="checkbox" lay-filter="checkall" name="" lay-skin="primary">'))

    if info_dict["list_display"]:
        for field in info_dict["list_display"]:
            if hasattr(info_dict["model"], field):
                thead.append(info_dict["model"]._meta.get_field(field).verbose_name)
    else:
        thead.append(info_dict["model"]._meta.model_name)

    if info_dict["options"]:
        thead.append("操作")

    return thead


def table_option_edit(app_label, model_name, pk):
    url = reverse("%s_%s_change" % (app_label, model_name), kwargs={"pk": pk})
    return f"""
          <a title="编辑" onclick="xadmin.open('编辑','{url}',800,600)" href="javascript:;" class="layui-btn">
              <i class="layui-icon">&#xe642;</i>编辑
          </a>
          """


def table_option_delete(app_label, model_name, pk):
    url = reverse("%s_%s_delete" % (app_label, model_name), kwargs={"pk": pk})
    return f""" 
          <a title="删除" onclick="member_del(this,'{url}')" href="javascript:;" class="layui-btn layui-btn-danger">
              <i class="layui-icon">&#xe640;</i>删除
          </a>
          """


def table_tbody_options(info_dict, result):
    """
    构建每一行的 操作列
    :param info_dict: 传递信息
    :param result: 每行数据的实例
    :return:
    """
    options = []
    app_label = info_dict["model"]._meta.app_label
    model_name = info_dict["model"]._meta.model_name

    for option in info_dict["options"]:
        if "edit" == option:
            options.append(table_option_edit(app_label, model_name, result.pk))
        elif "delete" == option:
            options.append(table_option_delete(app_label, model_name, result.pk))
        elif hasattr(info_dict["admin_class"], option):
            attr = getattr(info_dict["admin_class"], option)

            if callable(attr):
                options.append(attr(info_dict["model"], result.pk))
            else:
                raise Exception(f"{option} 应该定义成一个方法")
        else:
            raise Exception(f"请实现 {option} 方法")

    return options


def table_tbody(info_dict):
    table_data_list = []
    for result in info_dict["queryset"]:
        if info_dict["list_display"]:
            row = []

            if info_dict["has_checkbox"]:
                row.append(mark_safe(f'<input type="checkbox" name="pk" value="{result.pk}" lay-skin="primary">'))

            for field in info_dict["list_display"]:
                if hasattr(result, field):
                    is_choice = info_dict["model"]._meta.get_field(field).choices
                    if is_choice:
                        row.append(getattr(result, f"get_{field}_display"))
                    else:
                        _field = info_dict["model"]._meta.get_field(field)
                        # 判断表格展示字段是否是多对多
                        if isinstance(_field, ManyToManyField):
                            '''
                            如果有 自定义 kingadmin类中 有 list_{field} 方法则调用该方法
                            eg: 
                            class BookAdmin(ModelAdmin):
                                list_display = ["title", "publisher"] # publisher 是多对多字段
                                ...

                                def list_publisher(self,instance): # instance 表示该行数据的 model实例
                                    return " ".join(", ".join([str(item) for item in data_m2m] or []))

                            '''
                            if hasattr(info_dict["admin_class"], f"list_{field}"):
                                func = getattr(info_dict["admin_class"], f"list_{field}")
                                row.append(func(result))

                            else:
                                if hasattr(result, field):
                                    data_m2m = getattr(result, field).all()
                                    row.append(", ".join([str(item) for item in data_m2m] or []))
                                else:
                                    row.append("")

                        else:
                            row.append(getattr(result, field))

            if info_dict["options"]:
                options = table_tbody_options(info_dict, result)
                row.append(mark_safe("".join(options)))

            table_data_list.append(row)
        else:
            table_data_list.append([str(result)])

    return table_data_list


@register.inclusion_tag("kingadmin/table/table_data.html")
def table_data(info_dict):
    return {"headers": table_thead(info_dict), "table_data_list": table_tbody(info_dict)}
