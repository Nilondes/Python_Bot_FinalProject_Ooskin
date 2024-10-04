from django.contrib import admin
from .models import User, Ad, SearchCriteria


admin.site.register(Ad)
admin.site.register(User)
admin.site.register(SearchCriteria)
