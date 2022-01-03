from django.core.cache import cache


class ClearCacheMixin:
    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        super().tearDown()
        cache.clear()
