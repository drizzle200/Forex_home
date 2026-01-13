from django.contrib import admin
from . import models
# Register your models here.
class trade_view(admin.ModelAdmin):
   list_display=['trade_id', 'buy_or_sell']
   list_filter = ['timestamp','pair','entry_place']


#class Course_curriculums_view(admin.ModelAdmin):
 #   list_display= ['name']

##class Course_lessons_view(admin.ModelAdmin):
#    list_display = ['lesson_name','courses','curriculums']
admin.site.register(models.Trades, trade_view)
#admin.site.register(models.Course_curriculums, Course_curriculums_view)
#admin.site.register(models.Course_lessons,Course_lessons_view)
#admin.site.register(models.Flight)
#admin.site.register(models.Passenger