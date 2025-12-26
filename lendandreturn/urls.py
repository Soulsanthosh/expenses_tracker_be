from django.urls import path
from .views import (
    LendReturnCreateAPI,
    GivenReceivedSummaryAPI,
    BorrowedReturnedSummaryAPI,
    PersonFullHistoryAPI,
    LendReturnTotalsAPI
)

urlpatterns = [
    path("lend-return/add/", LendReturnCreateAPI.as_view()),

    path("lend-return/summary/given-received/",
         GivenReceivedSummaryAPI.as_view()),

    path("lend-return/summary/borrowed-returned/",
         BorrowedReturnedSummaryAPI.as_view()),

    path("lend-return/person/<str:person_name>/",
         PersonFullHistoryAPI.as_view()),

     path(
        "lend-return/totals/",
        LendReturnTotalsAPI.as_view(),
        name="lend-return-totals"
    ),
]
