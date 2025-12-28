from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import expenses
from .serializers import ExpensesSerializer

from datetime import date, timedelta
from collections import defaultdict

from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncYear

from django.http import JsonResponse
from django.db import connection

def db_test(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
        return JsonResponse({"db": "ok", "result": row})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"db": "error", "error": str(e)}, status=500)


# =========================
# COMMON HELPER
# =========================
def get_user_queryset(request):
    if request.user.is_staff or request.user.is_superuser:
        return expenses.objects.all()
    return expenses.objects.filter(user=request.user)


# =========================
# CRUD EXPENSES
# =========================
class ExpensesAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id=None):
        queryset = get_user_queryset(request)

        if id:
            queryset = queryset.filter(id=id)

        serializer = ExpensesSerializer(queryset, many=True)
        return Response(
            {"results": serializer.data, "count": queryset.count()},
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = ExpensesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)  # 🔐 bind user
            return Response(
                {"message": "Expenses Added Successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        queryset = get_user_queryset(request)
        expense = queryset.get(id=id)

        serializer = ExpensesSerializer(
            expense, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Updated Successfully"})
        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        queryset = get_user_queryset(request)
        expense = queryset.get(id=id)
        expense.delete()
        return Response({"message": "Deleted Successfully"})


# =========================
# DAILY EXPENSES
# =========================
class DailyExpensesAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        datas = get_user_queryset(request).order_by("date")

        daily_data = {}

        for expense in datas:
            date_key = expense.date.strftime("%Y-%m-%d")
            expense_type = expense.expenses_type

            daily_data.setdefault(date_key, {})
            daily_data[date_key].setdefault(expense_type, {
                "expenses_type": expense_type,
                "total_amount": 0,
                "amounts": [],
                "notes": []
            })

            daily_data[date_key][expense_type]["total_amount"] += float(expense.amount)
            daily_data[date_key][expense_type]["amounts"].append(float(expense.amount))
            daily_data[date_key][expense_type]["notes"].append(expense.note)

        response = [
            {"date": d, "expenses": list(v.values())}
            for d, v in daily_data.items()
        ]

        return Response(response)


# =========================
# MONTHLY EXPENSES
# =========================
class MonthlyExpensesAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        datas = get_user_queryset(request).order_by("date")
        monthly_data = {}

        for expense in datas:
            month_key = expense.date.strftime("%Y-%m")
            expense_type = expense.expenses_type

            monthly_data.setdefault(month_key, {})
            monthly_data[month_key].setdefault(expense_type, {
                "expenses_type": expense_type,
                "total_amount": 0,
                # "amounts": [],
                # "notes": []
            })

            monthly_data[month_key][expense_type]["total_amount"] += float(expense.amount)
            # monthly_data[month_key][expense_type]["amounts"].append(float(expense.amount))
            # monthly_data[month_key][expense_type]["notes"].append(expense.note)

        response = [
            {"month": m, "expenses": list(v.values())}
            for m, v in monthly_data.items()
        ]

        return Response(response)


# =========================
# YEARLY EXPENSES
# =========================
class YearlyExpensesAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        datas = get_user_queryset(request).order_by("date")
        yearly_data = {}

        for expense in datas:
            year_key = expense.date.strftime("%Y")
            expense_type = expense.expenses_type

            yearly_data.setdefault(year_key, {})
            yearly_data[year_key].setdefault(expense_type, {
                "expenses_type": expense_type,
                "total_amount": 0,
                # "amounts": [],
                # "notes": []
            })

            yearly_data[year_key][expense_type]["total_amount"] += float(expense.amount)
            # yearly_data[year_key][expense_type]["amounts"].append(float(expense.amount))
            # yearly_data[year_key][expense_type]["notes"].append(expense.note)

        response = [
            {"year": y, "expenses": list(v.values())}
            for y, v in yearly_data.items()
        ]

        return Response(response)


# =========================
# CHART APIs (DAILY / MONTHLY / YEARLY)
# =========================
class DailyExpenseChartAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = get_user_queryset(request)

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])

        queryset = queryset.values("date", "expenses_type") \
            .annotate(total_amount=Sum("amount")) \
            .order_by("date")

        chart_totals = defaultdict(float)
        for item in queryset:
            chart_totals[item["expenses_type"]] += float(item["total_amount"])

        return Response({
            "chart": {
                "labels": list(chart_totals.keys()),
                "values": list(chart_totals.values())
            }
        })


class MonthlyExpenseChartAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = get_user_queryset(request)

        queryset = queryset.annotate(
            month=TruncMonth("date")
        ).values("month", "expenses_type") \
         .annotate(total_amount=Sum("amount")) \
         .order_by("month")

        chart_totals = defaultdict(float)
        for item in queryset:
            chart_totals[item["expenses_type"]] += float(item["total_amount"])

        return Response({
            "chart": {
                "labels": list(chart_totals.keys()),
                "values": list(chart_totals.values())
            }
        })


class YearlyExpenseChartAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = get_user_queryset(request)

        queryset = queryset.annotate(
            year=TruncYear("date")
        ).values("year", "expenses_type") \
         .annotate(total_amount=Sum("amount")) \
         .order_by("year")

        chart_totals = defaultdict(float)
        for item in queryset:
            chart_totals[item["expenses_type"]] += float(item["total_amount"])

        return Response({
            "chart": {
                "labels": list(chart_totals.keys()),
                "values": list(chart_totals.values())
            }
        })


# =========================
# DASHBOARD SUMMARY
# =========================
class DashboardSummaryAPI(APIView):
    permission_classes = [IsAuthenticated]

    def percentage_change(self, current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 2)

    def get(self, request):
        queryset = get_user_queryset(request)

        today = date.today()
        yesterday = today - timedelta(days=1)

        # =========================
        # TOTALS
        # =========================
        total_expense = queryset.aggregate(
            total=Sum("amount")
        )["total"] or 0

        today_expense = queryset.filter(
            date=today
        ).aggregate(total=Sum("amount"))["total"] or 0

        yesterday_expense = queryset.filter(
            date=yesterday
        ).aggregate(total=Sum("amount"))["total"] or 0

        # =========================
        # MONTH COMPARISON
        # =========================
        this_month_expense = queryset.filter(
            date__year=today.year,
            date__month=today.month
        ).aggregate(total=Sum("amount"))["total"] or 0

        last_month_date = today.replace(day=1) - timedelta(days=1)

        last_month_expense = queryset.filter(
            date__year=last_month_date.year,
            date__month=last_month_date.month
        ).aggregate(total=Sum("amount"))["total"] or 0

        # =========================
        # YEAR COMPARISON
        # =========================
        this_year_expense = queryset.filter(
            date__year=today.year
        ).aggregate(total=Sum("amount"))["total"] or 0

        last_year_expense = queryset.filter(
            date__year=today.year - 1
        ).aggregate(total=Sum("amount"))["total"] or 0

        # =========================
        # RESPONSE
        # =========================
        response = {
            "summary": {
                "total_expense": float(total_expense),
                "today_expense": float(today_expense),
                "this_month_expense": float(this_month_expense),
                "this_year_expense": float(this_year_expense),
            },
            "comparison": {
                "today_vs_yesterday": {
                    "today": float(today_expense),
                    "yesterday": float(yesterday_expense),
                    "percentage": self.percentage_change(
                        today_expense, yesterday_expense
                    ),
                    "status": (
                        "increase" if today_expense > yesterday_expense
                        else "decrease" if today_expense < yesterday_expense
                        else "same"
                    )
                },
                "this_month_vs_last_month": {
                    "this_month": float(this_month_expense),
                    "last_month": float(last_month_expense),
                    "percentage": self.percentage_change(
                        this_month_expense, last_month_expense
                    ),
                    "status": (
                        "increase" if this_month_expense > last_month_expense
                        else "decrease" if this_month_expense < last_month_expense
                        else "same"
                    )
                },
                "this_year_vs_last_year": {
                    "this_year": float(this_year_expense),
                    "last_year": float(last_year_expense),
                    "percentage": self.percentage_change(
                        this_year_expense, last_year_expense
                    ),
                    "status": (
                        "increase" if this_year_expense > last_year_expense
                        else "decrease" if this_year_expense < last_year_expense
                        else "same"
                    )
                }
            }
        }

        return Response(response)