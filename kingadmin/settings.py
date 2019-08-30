from django.conf import settings
from django.test.signals import setting_changed

DEFAULTS = {
    # Throttling
    'DEFAULT_THROTTLE_RATES': {
        'user': None,
        'anon': None,
    },
    'NUM_PROXIES': None,

    # Pagination
    'PRE_PAGE_NUM': 20,  # 每页显示多少条数据
    'PAGE_COUNT': 5,  # 分页显示几个页面
    'TOTAL_PAGE_NUM': 200,  # 总页码数
    'PAGE_QUERY': 'page',  # 页码url查询参数

    # Filtering
    'SEARCH_PARAM': 'search',  # 关键搜索参数
    'ORDERING_PARAM': 'ordering',

    # Authentication
    'UNAUTHENTICATED_USER': 'django.contrib.auth.models.AnonymousUser',
    'UNAUTHENTICATED_TOKEN': None,

    # Input and output formats
    'DATE_FORMAT': "",
    'DATE_INPUT_FORMATS': "",

    'DATETIME_FORMAT': "",
    'DATETIME_INPUT_FORMATS': "",

    'TIME_FORMAT': "",
    'TIME_INPUT_FORMATS': "",

}


class APISettings:
    """
    A settings object, that allows API settings to be accessed as properties.
    For example:

        from kingadmin.settings import admin_settings
        print(admin_settings.DEFAULT_RENDERER_CLASSES)

    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """

    def __init__(self, defaults=None):
        self.defaults = defaults or DEFAULTS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, 'KING_ADMIN', {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid API setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, '_user_settings'):
            delattr(self, '_user_settings')


admin_settings = APISettings(DEFAULTS)


def reload_api_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == 'KING_ADMIN':
        admin_settings.reload()


setting_changed.connect(reload_api_settings)
