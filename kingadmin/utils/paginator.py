from django.utils.safestring import mark_safe

from kingadmin.settings import admin_settings


class Paginator:
    def __init__(self, query_sets, query_params={}):
        """
        分页初始化方法
        :param query_sets: queryset查询的所有数据
        :param query_params: request.GET 参数
        """
        current_page = query_params.get(admin_settings.PAGE_QUERY, 1)
        try:
            if type(current_page) == str:
                if current_page.isdecimal():
                    current_page = int(current_page)
                else:
                    current_page = 1

        except Exception as e:
            print("分页错误", e)
            current_page = 1

        self.query_sets = query_sets[:admin_settings.TOTAL_PAGE_NUM * admin_settings.PRE_PAGE_NUM]
        self.query_params = query_params
        self.total_num = self.query_sets.count()

        max_page_num, mod = divmod(self.total_num, admin_settings.PRE_PAGE_NUM)
        if mod != 0:
            max_page_num += 1

        if current_page > max_page_num:
            current_page = max_page_num

        self.current_page = current_page

        # 所有数据量不足 展示页码数
        if max_page_num < admin_settings.PAGE_COUNT:
            start_page_num = 1
            end_page_num = max_page_num
        else:
            half_page = admin_settings.PAGE_COUNT // 2

            start_page_num = self.current_page - half_page
            end_page_num = self.current_page + half_page

            if start_page_num < 1:
                start_page_num = 1

            if end_page_num > max_page_num:
                end_page_num = max_page_num
                start_page_num = max_page_num - admin_settings.PAGE_COUNT + 1

            if end_page_num - start_page_num < admin_settings.PAGE_COUNT:
                end_page_num = start_page_num + admin_settings.PAGE_COUNT - 1

        self.start_page_num = start_page_num
        self.end_page_num = end_page_num
        self.max_page_num = max_page_num

    def get_html(self):

        # 判断上一页是否存在
        if self.current_page - 1 > 0:
            previous_page = {"status": True, "num": self.current_page - 1}
        else:
            previous_page = {"status": False, "num": 1}

        # 判断下一页是否存在
        if self.current_page < self.max_page_num:
            next_page = {"status": True, "num": self.current_page + 1}
        else:
            next_page = {"status": False, "num": self.current_page}

        # 判断是否有get请求
        if self.query_params:
            query = self.query_params.copy()
            if query.get(admin_settings.PAGE_QUERY):
                query.pop(admin_settings.PAGE_QUERY)

            urlencode = query.urlencode()
            if urlencode:
                query_url = "&" + urlencode
            else:
                query_url = urlencode

        else:
            query_url = ""

        # 组装页码数
        inner_html = ''
        for i in range(self.start_page_num, self.end_page_num + 1):
            if i == self.current_page:
                inner_html += f"""
                <span class="layui-laypage-curr">
                    <em class="layui-laypage-em"></em>
                    <em>{i}</em>
                </span>
                """
            else:
                inner_html += f'<a href="?{admin_settings.PAGE_QUERY}={i}{query_url}" class="num">{i}</a>'

        # 组装上一页
        if previous_page["status"]:
            previous_html = '''
                  <a href="?%s=%s%s" class="prev" >
                    上一页
                  </a>
            ''' % (admin_settings.PAGE_QUERY, previous_page["num"], query_url)
        else:
            previous_html = '''
                             <a href="javascript:void();" class="layui-disabled">
                               上一页
                             </a>
                           '''
        # 组装下一页
        if next_page["status"]:
            next_html = '''
                      <a href="?%s=%s%s" class="next">
                        下一页
                      </a>
                    ''' % (admin_settings.PAGE_QUERY, next_page["num"], query_url)
        else:
            next_html = '''
                          <a href="javascript:void();" class="layui-disabled">
                            下一页
                          </a>
                        '''

        page_html = mark_safe('''
        <div class="layui-box layui-laypage layui-laypage-default">
          <div>
            %s
            %s
            %s
          </div>
        </div>      
        ''' % (previous_html, inner_html, next_html))

        start = (self.current_page - 1) * admin_settings.PRE_PAGE_NUM
        page_obj = self.query_sets[start:start + admin_settings.PRE_PAGE_NUM]

        return page_html, page_obj
