from django.contrib import admin
from .models import User, Ad, SearchCriteria, AdComments


admin.site.register(Ad)
admin.site.register(User)
admin.site.register(SearchCriteria)
admin.site.register(AdComments)
