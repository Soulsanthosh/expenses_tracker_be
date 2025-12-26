from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.db.models import Sum

from .models import LendReturn, TransactionType
from .serializers import LendReturnSerializer


# =========================
# COMMON HELPER
# =========================
def get_user_queryset(request):
    if request.user.is_staff or request.user.is_superuser:
        return LendReturn.objects.all()
    return LendReturn.objects.filter(user=request.user)


# =========================
# CREATE TRANSACTION
# =========================
class LendReturnCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LendReturnSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)  # 🔐 bind user
            return Response(
                {"message": "Transaction added successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================
# GIVEN / RECEIVED SUMMARY
# =========================
class GivenReceivedSummaryAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = get_user_queryset(request)

        persons = qs.values_list("person_name", flat=True).distinct()
        result = []

        for person in persons:
            records = qs.filter(
                person_name=person,
                transaction_type__in=[
                    TransactionType.GIVEN,
                    TransactionType.RECEIVED
                ]
            )

            given = records.filter(
                transaction_type=TransactionType.GIVEN
            ).aggregate(total=Sum("amount"))["total"] or 0

            received = records.filter(
                transaction_type=TransactionType.RECEIVED
            ).aggregate(total=Sum("amount"))["total"] or 0

            balance = float(given) - float(received)

            result.append({
                "person_name": person,
                "given": float(given),
                "received": float(received),
                "balance": balance,
                "status": (
                    "you will get"
                    if balance > 0 else
                    "settled"
                    if balance == 0 else
                    "you need to give"
                )
            })

        return Response(result)


# =========================
# BORROWED / RETURNED SUMMARY
# =========================
class BorrowedReturnedSummaryAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = get_user_queryset(request)

        persons = qs.values_list("person_name", flat=True).distinct()
        result = []

        for person in persons:
            records = qs.filter(
                person_name=person,
                transaction_type__in=[
                    TransactionType.BORROWED,
                    TransactionType.RETURNED
                ]
            )

            borrowed = records.filter(
                transaction_type=TransactionType.BORROWED
            ).aggregate(total=Sum("amount"))["total"] or 0

            returned = records.filter(
                transaction_type=TransactionType.RETURNED
            ).aggregate(total=Sum("amount"))["total"] or 0

            balance = float(returned) - float(borrowed)

            result.append({
                "person_name": person,
                "borrowed": float(borrowed),
                "returned": float(returned),
                "balance": balance,
                "status": (
                    "you need to pay"
                    if balance < 0 else
                    "settled"
                    if balance == 0 else
                    "paid extra"
                )
            })

        return Response(result)


# =========================
# PERSON FULL HISTORY
# =========================
class PersonFullHistoryAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, person_name):
        qs = get_user_queryset(request)

        records = qs.filter(
            person_name=person_name
        ).order_by("date")

        serializer = LendReturnSerializer(records, many=True)

        given = received = borrowed = returned = 0

        for r in records:
            if r.transaction_type == TransactionType.GIVEN:
                given += float(r.amount)
            elif r.transaction_type == TransactionType.RECEIVED:
                received += float(r.amount)
            elif r.transaction_type == TransactionType.BORROWED:
                borrowed += float(r.amount)
            elif r.transaction_type == TransactionType.RETURNED:
                returned += float(r.amount)

        response = {
            "person_name": person_name,
            "lend_summary": {
                "given": given,
                "received": received,
                "balance": given - received
            },
            "borrow_summary": {
                "borrowed": borrowed,
                "returned": returned,
                "balance": returned - borrowed
            },
            "history": serializer.data
        }

        return Response(response)


# =========================
# TOTALS DASHBOARD
# =========================
class LendReturnTotalsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = get_user_queryset(request)

        total_given = qs.filter(
            transaction_type=TransactionType.GIVEN
        ).aggregate(total=Sum("amount"))["total"] or 0

        total_received = qs.filter(
            transaction_type=TransactionType.RECEIVED
        ).aggregate(total=Sum("amount"))["total"] or 0

        total_borrowed = qs.filter(
            transaction_type=TransactionType.BORROWED
        ).aggregate(total=Sum("amount"))["total"] or 0

        total_returned = qs.filter(
            transaction_type=TransactionType.RETURNED
        ).aggregate(total=Sum("amount"))["total"] or 0

        return Response({
            "totals": {
                "given": float(total_given),
                "received": float(total_received),
                "borrowed": float(total_borrowed),
                "returned": float(total_returned)
            }
        })
