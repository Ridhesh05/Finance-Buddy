from django.contrib import admin
from .models import Expense, DailyIncome,Goal,Blog,Notification,Profile
from import_export.admin import ImportExportModelAdmin


class ExpenseAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name', 'type', 'date', 'amount', 'user', 'id')
    list_filter = ('type', 'user')
    search_fields = ('name', 'description')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(user=request.user)
        return queryset

    ordering = ('user', 'date')

admin.site.register(Expense, ExpenseAdmin)

class DailyIncomeAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'income_type', 'income')
    list_filter = ('user', 'date', 'income_type')
    search_fields = ('user__username', 'date', 'income_type')
    ordering = ('user', 'date')

admin.site.register(DailyIncome, DailyIncomeAdmin)

class GoalAdmin(admin.ModelAdmin):
    list_display=('user','name','desired_date')
    list_filter = ('user',)
admin.site.register(Goal,GoalAdmin)



admin.site.register(Blog)

admin.site.register(Notification)

admin.site.register(Profile)



