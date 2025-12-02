import pandas as pd
from django.http import HttpResponse

def export_to_excel(records, filename="export.xlsx"):
    df = pd.DataFrame(records)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    df.to_excel(response, index=False)
    return response


def export_to_csv(records, filename="export.csv"):
    df = pd.DataFrame(records)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    df.to_csv(response, index=False)
    return response
