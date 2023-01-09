from django.contrib import admin

from foodadv.models import FoodadvRecord, FoodLabelingAdviseQuestion, FoodadvTimeLeft

admin.site.register(FoodadvTimeLeft)
admin.site.register(FoodadvRecord)
admin.site.register(FoodLabelingAdviseQuestion)
