# admin.py
from django.contrib import admin
from .models import MyFormData, Item
from .models import ExpenseReport, ExpenseDetail
from .models import PackageReport, PackageDetail 

@admin.register(MyFormData)
class MyFormDataAdmin(admin.ModelAdmin):
    list_display = ('company', 'your_name', 'invoice', 'datetime_field1', 'datetime_field2')  

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('myformdata', 'item_desc', 'qty', 'rate', 'sgst', 'cgst', 'cess') 

@admin.register(ExpenseReport)
class ExpenseReportAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'your_name', 'invoice_id', 'date_from', 'date_to')
    search_fields = ('company_name', 'your_name', 'invoice_id')

@admin.register(ExpenseDetail)
class ExpenseDetailAdmin(admin.ModelAdmin):
    list_display = ('expense_report', 'expense_description', 'merchant', 'amount')
    search_fields = ('expense_description', 'merchant')



@admin.register(PackageReport)
class PackageReportAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'your_name', 'client_name', 'invoice_id', 'order_date', 'package_date')
    search_fields = ('company_name', 'your_name', 'client_name', 'invoice_id')

@admin.register(PackageDetail)
class PackageDetailAdmin(admin.ModelAdmin):
    list_display = ('package_report', 'item_description', 'order_quantity', 'shipped_quantity')
    search_fields = ('item_description',)