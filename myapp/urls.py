from django.urls import path
from .views import form_view, invoice_list_view, generate_pdf,expense_report_view, expense_report_list_view,dashboard_view,generate_expense_report_pdf,package_report_view,package_report_list_view,generate_package_report_pdf

urlpatterns = [
    path('form/', form_view, name='form_view'),
    path('invoices/', invoice_list_view, name='invoice_list_view'),
    path('pdf/<str:invoice_id>/', generate_pdf, name='generate_pdf'),
    path('Expensesform/', expense_report_view, name='expense_report_view'),
    path('Expenseslist/', expense_report_list_view, name='expense_report_list_view'),
    path('', dashboard_view, name='dashboard'),
    path('expense/report/pdf/<int:report_id>/', generate_expense_report_pdf, name='generate_expense_report_pdf'),
    path('package-report/new/', package_report_view, name='package_report_view'),
    path('package-reports/', package_report_list_view, name='package_report_list_view'),
    path('package/report/pdf/<int:report_id>/', generate_package_report_pdf, name='generate_package_report_pdf'),
  
 
    
]
