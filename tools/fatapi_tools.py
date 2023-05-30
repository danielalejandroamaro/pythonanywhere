import io

import pandas as pd
from fastapi.responses import StreamingResponse

from main import python_telegram_file_bot


def export_xlsx(matrix, filename: str):
    ioutput = io.BytesIO()

    writer = pd.ExcelWriter(
        ioutput
        , engine='xlsxwriter'
        , engine_kwargs={
            'options': {'strings_to_numbers': False}
        }
    )
    matrix.to_excel(writer, index=False)
    writer.close()
    ioutput.seek(0)

    # fix_name
    change = True
    while change:
        change = False
        for ext in [".xlsx", ".xls"]:
            if filename.endswith(ext):
                filename = filename[:-len(ext)]
                change = True

    headers = {
        'Content-Disposition': f'attachment; filename="{filename}.xlsx"',
    }
    response = StreamingResponse(
        ioutput,
        headers=headers,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

    )
    return response


async def send_telegram_xlsx(matrix, file_name):
    ioutput = io.BytesIO()

    writer = pd.ExcelWriter(
        ioutput
        , engine='xlsxwriter'
        , engine_kwargs={
            'options': {'strings_to_numbers': False}
        }
    )
    matrix.to_excel(writer, index=False)
    writer.close()
    ioutput.seek(0)

    # fix_name
    change = True
    while change:
        change = False
        for ext in [".xlsx", ".xls"]:
            if file_name.endswith(ext):
                file_name = file_name[:-len(ext)]
                change = True

    return await python_telegram_file_bot(
        ioutput,
        f'{file_name}.xlsx'
        # mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
