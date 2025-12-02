from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework import status
from .serializers import ExpenseSerializer
from .models import expenses
import pandas as pd
from datetime import datetime
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncDay, TruncYear
from .export_utils import export_to_excel, export_to_csv

class ExpensesAPI(APIView):

    # 👉 GET ALL EXPENSES
    def get(self, request):
        expense = expenses.objects.all().order_by('-id')
        serializer = ExpenseSerializer(expense, many=True)
        
        return Response(
            {"message": "Expenses fetched successfully", "results": serializer.data},
            status=status.HTTP_200_OK
        )

    # 👉 CREATE EXPENSE
    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Expense created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {"message": "Validation failed", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 👉 UPDATE EXPENSE PARTIALLY USING ID (PATCH)
    def patch(self, request, id=None):
        if not id:
            return Response(
                {"message": "Expense ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            expense = expenses.objects.get(id=id)
        except expenses.DoesNotExist:
            return Response(
                {"message": "Expense not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ExpenseSerializer(expense, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Expense updated successfully", "data": serializer.data},
                status=status.HTTP_206_PARTIAL_CONTENT
            )

        return Response(
            {"message": "Update failed", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class DailyExpensesAPI(APIView):

    def get(self, request):

        # --------- FILTERS ----------
        date = request.GET.get("date")
        from_date = request.GET.get("from")
        to_date = request.GET.get("to")

        queryset = expenses.objects.all().order_by("date", "time")

        # --- SINGLE DATE FILTER ---
        if date:
            day_expenses = queryset.filter(date=date)
            if not day_expenses.exists():
                return Response({"message": "No expenses found"}, status=200)

            result = {
                "date": date,
                "total": sum(int(i.amount) for i in day_expenses),
                "details": [
                    {
                        "id": exp.id,
                        "type": exp.expenses_type,
                        "amount": exp.amount,
                        "time": exp.time.strftime("%H:%M:%S"),
                        "note": exp.note
                    }
                    for exp in day_expenses
                ]
            }
            return Response(result, status=200)

        # --- DATE RANGE FILTER ---
        if from_date and to_date:
            queryset = queryset.filter(date__range=[from_date, to_date])

        # ----------- GROUPED MULTI-DAY RESPONSE -----------
        result = {}

        for item in queryset:
            date_str = str(item.date)

            if date_str not in result:
                result[date_str] = {
                    "rent": 0,
                    "travel": 0,
                    "shopping": 0,
                    "utilities": 0,
                    "entertainment": 0,
                    "total": 0
                }

            result[date_str][item.expenses_type] += int(item.amount)
            result[date_str]["total"] += int(item.amount)

        return Response(result, status=200)


class ExportExpensesAPI(APIView):

    def get(self, request):

        from_date = request.GET.get("from")
        to_date = request.GET.get("to")

        queryset = expenses.objects.all().order_by("date", "time")

        if from_date and to_date:
            queryset = queryset.filter(date__range=[from_date, to_date])

        if not queryset.exists():
            return Response({"message": "No data available to export"}, status=404)

        # Convert to DataFrame
        data = [
            {
                "Date": str(i.date),
                "Time": i.time.strftime("%H:%M:%S"),
                "Type": i.expenses_type,
                "Amount": i.amount,
                "Note": i.note
            }
            for i in queryset
        ]

        df = pd.DataFrame(data)

        # Export to Excel
        file_name = f"expenses_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        df.to_excel(response, index=False)

        return response
    
    
class MonthlyExpensesAPI(APIView):

    def get(self, request):
        month = request.GET.get("month")       # format YYYY-MM
        start = request.GET.get("from")
        end = request.GET.get("to")

        # ----------------------------
        # 1️⃣  SINGLE MONTH DETAILS API
        # ----------------------------
        if month:
            try:
                month_date = datetime.datetime.strptime(month, "%Y-%m").date()
            except:
                return Response({"error": "Invalid month format. Use YYYY-MM"}, status=400)

            month_exp = expenses.objects.filter(
                date__year=month_date.year,
                date__month=month_date.month
            ).order_by("date")

            # Group by each day
            daily_list = {}
            for exp in month_exp:
                day_key = exp.date.strftime("%Y-%m-%d")
                if day_key not in daily_list:
                    daily_list[day_key] = {
                        "date": day_key,
                        "total": 0,
                        "items": []
                    }

                daily_list[day_key]["items"].append({
                    "id": exp.id,
                    "type": exp.expenses_type,
                    "amount": float(exp.amount),
                    "time": exp.time.strftime("%H:%M:%S"),
                    "note": exp.note,
                })

                daily_list[day_key]["total"] += float(exp.amount)

            total_month = sum(v["total"] for v in daily_list.values())

            return Response({
                "month": month,
                "total_month_expense": total_month,
                "days": list(daily_list.values())
            })

        # ----------------------------
        # 2️⃣  DATE RANGE MONTH FILTER
        # ----------------------------
        if start and end:
            try:
                start_date = datetime.datetime.strptime(start, "%Y-%m-%d")
                end_date = datetime.datetime.strptime(end, "%Y-%m-%d")
            except:
                return Response({"error": "Invalid date format (YYYY-MM-DD)"}, status=400)

            month_data = expenses.objects.filter(
                date__range=[start_date, end_date]
            ).annotate(month=TruncMonth("date")).values("month").annotate(
                total=Sum("amount")
            ).order_by("month")

            return Response({
                "filtered": True,
                "results": [
                    {
                        "month": m["month"].strftime("%Y-%m"),
                        "total": float(m["total"])
                    } for m in month_data
                ]
            })

        # ----------------------------
        # 3️⃣  DEFAULT — SHOW ALL MONTH SUMMARY (WITH CATEGORY TOTALS)
        # ----------------------------
        all_months = expenses.objects.annotate(
            month=TruncMonth("date")
        ).order_by("month")

        summary_dict = {}

        for exp in all_months:
            month_key = exp.date.strftime("%Y-%m")
    
            if month_key not in summary_dict:
                summary_dict[month_key] = {
                    "month": month_key,
                    "total": 0,
                    "categories": {}
                }
    
            # Add to total
            summary_dict[month_key]["total"] += float(exp.amount)
    
            # Add to category
            cat = exp.expenses_type
            summary_dict[month_key]["categories"][cat] = summary_dict[month_key]["categories"].get(cat, 0) + float(exp.amount)

        # Convert dict → list
        response = list(summary_dict.values())

        return Response({
            "message": "Monthly summary fetched",
            "results": response
        })

        
class ExportMonthlyExpensesAPI(APIView):
    def get(self, request):
        start = request.GET.get("from")
        end = request.GET.get("to")

        qs = expenses.objects.all()

        if start and end:
            qs = qs.filter(date__range=[start, end])

        df = pd.DataFrame(list(qs.values()))

        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="monthly_expenses.xlsx"'
        df.to_excel(response, index=False)

        return response
    
    
# ======================================================
# 1️⃣ GET ALL YEARLY EXPENSE SUMMARY
# ======================================================
class YearlyExpensesAPI(APIView):

    def get(self, request):
        """
        Output:
        [
            {
                "year": "2025",
                "total": 52000,
                "category_wise": {
                    "rent": 15000,
                    "travel": 11000,
                    "shopping": 9000,
                    "utilities": 8000,
                    "entertainment": 9000
                }
            }
        ]
        """
        yearly_data = (
            expenses.objects
            .annotate(year=TruncYear("date"))
            .values("year")
            .annotate(total=Sum("amount"))
            .order_by("year")
        )

        final_output = []

        for y in yearly_data:
            year_str = y["year"].year
            category_wise = (
                expenses.objects.filter(date__year=year_str)
                .values("expenses_type")
                .annotate(total=Sum("amount"))
            )

            final_output.append({
                "year": str(year_str),
                "total": y["total"],
                "category_wise": {
                    item["expenses_type"]: item["total"] for item in category_wise
                }
            })

        return Response(final_output, status=status.HTTP_200_OK)


# ======================================================
# 2️⃣ GET SINGLE YEAR → MONTH WISE EXPENSES
# ======================================================
class SingleYearExpensesAPI(APIView):
    def get(self, request, year):
        """
        Output:
        [
            { "month": "2025-01", "total": 2200, category_wise: {...} }
        ]
        """

        monthly_data = (
            expenses.objects.filter(date__year=year)
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total=Sum("amount"))
            .order_by("month")
        )

        output = []

        for m in monthly_data:
            month_str = m["month"].strftime("%Y-%m")

            # get category wise for each month
            category_wise = (
                expenses.objects.filter(date__year=year, date__month=m["month"].month)
                .values("expenses_type")
                .annotate(total=Sum("amount"))
            )

            output.append({
                "month": month_str,
                "total": m["total"],
                "category_wise": {
                    item["expenses_type"]: item["total"] for item in category_wise
                }
            })

        return Response(output, status=status.HTTP_200_OK)


# ======================================================
# 3️⃣ GET SINGLE YEAR → SINGLE MONTH → DAILY DETAILS
# ======================================================
class SingleMonthDailyAPI(APIView):
    def get(self, request, year, month):
        """
        Output:
        [
            {
                "date": "2025-01-03",
                "total": 300,
                "details": [
                    { "time": "14:10", "type": "shopping", "amount": 200, ... }
                ]
            }
        ]
        """

        daily = (
            expenses.objects.filter(date__year=year, date__month=month)
            .values("date")
            .annotate(total=Sum("amount"))
            .order_by("date")
        )

        output = []

        for d in daily:
            details = expenses.objects.filter(date=d["date"]).values(
                "time", "expenses_type", "amount", "note"
            )

            output.append({
                "date": d["date"].strftime("%Y-%m-%d"),
                "total": d["total"],
                "details": list(details)
            })

        return Response(output, status=status.HTTP_200_OK)


# ======================================================
# 4️⃣ EXPORT YEARLY + DATE RANGE EXPORT
# ======================================================
class ExportYearlyExpensesAPI(APIView):

    def get(self, request):
        """
        /export/yearly/?type=excel
        /export/yearly/?year=2025&type=csv
        /export/yearly/?start=2025-01-01&end=2025-01-31&type=excel
        """
        export_type = request.GET.get("type", "excel")
        year = request.GET.get("year")
        start = request.GET.get("start")
        end = request.GET.get("end")

        # ---- export all ----
        if not year and not start:
            records = expenses.objects.all().values()
            return export_to_excel(records, "all_years.xlsx") if export_type == "excel" \
                   else export_to_csv(records, "all_years.csv")

        # ---- export year wise ----
        if year:
            records = expenses.objects.filter(date__year=year).values()
            return export_to_excel(records, f"{year}.xlsx") if export_type == "excel" \
                   else export_to_csv(records, f"{year}.csv")

        # ---- export date range ----
        if start and end:
            records = expenses.objects.filter(date__range=[start, end]).values()
            filename = f"{start}_to_{end}"
            return export_to_excel(records, f"{filename}.xlsx") if export_type == "excel" \
                   else export_to_csv(records, f"{filename}.csv")

        return Response({"error": "Invalid parameters"}, status=400)