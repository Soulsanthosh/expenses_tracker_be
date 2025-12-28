from django.urls import path
from .views import ExpensesAPI,DailyExpensesAPI,MonthlyExpensesAPI,YearlyExpensesAPI,DailyExpenseChartAPI,MonthlyExpenseChartAPI,YearlyExpenseChartAPI,DashboardSummaryAPI,db_test

urlpatterns = [
    path('add-expenses/', ExpensesAPI.as_view(), name = "add expenses" ),
    path('add-expenses/<int:id>/', ExpensesAPI.as_view(), name = "get specific expenses" ),

    path('daily/', DailyExpensesAPI.as_view(), name = 'daily-grouped-expenses'),
    path('monthly/', MonthlyExpensesAPI.as_view(), name = 'monthly-grouped-expenses'),
    path('yearly/', YearlyExpensesAPI.as_view(), name = 'yearly-grouped-expenses'),

    path('chart/daily/', DailyExpenseChartAPI.as_view(), name = 'daily-chart-expenses'),
    path('chart/monthly/', MonthlyExpenseChartAPI.as_view(), name = 'monthly-chart-expenses'),
    path('chart/yearly/', YearlyExpenseChartAPI.as_view(), name = 'yearly-chart-expenses'),

    path('dashboard/summary/', DashboardSummaryAPI.as_view(), name='dashboard-summary'),

    path("db-test/", db_test),


]
