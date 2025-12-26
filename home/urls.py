from django.urls import path
from .views import ExpensesAPI,DailyExpensesAPI,ExportExpensesAPI,MonthlyExpensesAPI, ExportMonthlyExpensesAPI,YearlyExpensesAPI,SingleYearExpensesAPI,SingleMonthDailyAPI,ExportYearlyExpensesAPI

urlpatterns = [
    path('expenses/', ExpensesAPI.as_view()),         # GET, POST
    path('expenses/<int:id>/', ExpensesAPI.as_view()), # PATCH
    path('daily-expenses/', DailyExpensesAPI.as_view(), name='daily-expenses'),# Get All / Single Day / Date Range
    path('daily-expenses/export/', ExportExpensesAPI.as_view(), name='export-expenses'), # Export All / Export Date Range
    path('monthly-expenses/', MonthlyExpensesAPI.as_view(), name='monthly-expenses'),
    path('monthly-expenses/export/', ExportMonthlyExpensesAPI.as_view(), name='monthly-export'),
    path("yearly/", YearlyExpensesAPI.as_view()),  
    path("yearly/<int:year>/", SingleYearExpensesAPI.as_view()),  
    path("yearly/<int:year>/<int:month>/", SingleMonthDailyAPI.as_view()),  
    # Export All / Year / Range
    path("export/yearly/", ExportYearlyExpensesAPI.as_view()),
]
