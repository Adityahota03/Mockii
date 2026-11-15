import csv
import re
from io import BytesIO, StringIO

from openpyxl import Workbook
from openpyxl.styles import Font

from .report_service import (
    get_student_report,
    get_exam_report,
    get_mock_test_report,
    get_attempt_report,
    get_performance_report,
    get_question_report,
    get_content_report,
)


def sanitize_sheet_title(title, existing_titles=None):
    """
    Sanitizes sheet titles for Excel:
    - Removes invalid characters: \\ / ? * : [ ]
    - Limits to 31 characters max
    - Ensures uniqueness among sheets in the workbook
    """
    clean = re.sub(r"[\\/*?:\[\]]", "_", str(title)).strip()
    if not clean:
        clean = "Sheet"
    clean = clean[:31]

    if existing_titles is not None:
        base = clean[:27]
        counter = 1
        while clean.lower() in [t.lower() for t in existing_titles]:
            clean = f"{base}_{counter}"[:31]
            counter += 1

    return clean


def get_export_report_data(days=30):
    """
    Unified dataset for export matching current report services.
    """
    return {
        "Students": get_student_report(days=days),
        "Exams": get_exam_report(days=days),
        "Mock Tests": get_mock_test_report(days=days),
        "Attempts": get_attempt_report(days=days),
        "Performance": get_performance_report(days=days),
        "Questions": get_question_report(days=days),
        "Content": get_content_report(),
    }


def write_dict_sheet(workbook, raw_title, data, existing_titles):
    sheet_title = sanitize_sheet_title(raw_title, existing_titles)
    existing_titles.append(sheet_title)

    worksheet = workbook.create_sheet(title=sheet_title)

    worksheet["A1"] = "Metric"
    worksheet["B1"] = "Value"

    worksheet["A1"].font = Font(bold=True)
    worksheet["B1"].font = Font(bold=True)

    row = 2
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            continue

        worksheet.cell(row=row, column=1, value=str(key))
        worksheet.cell(row=row, column=2, value=value)
        row += 1

    worksheet.column_dimensions["A"].width = 35
    worksheet.column_dimensions["B"].width = 25

    return worksheet


def write_list_sheet(workbook, raw_title, data, existing_titles):
    sheet_title = sanitize_sheet_title(raw_title, existing_titles)
    existing_titles.append(sheet_title)

    worksheet = workbook.create_sheet(title=sheet_title)

    if not data:
        worksheet["A1"] = "No data available."
        return worksheet

    first_item = data[0]

    if not isinstance(first_item, dict):
        worksheet["A1"] = "Value"
        worksheet["A1"].font = Font(bold=True)
        for index, value in enumerate(data, start=2):
            worksheet.cell(row=index, column=1, value=str(value))
        return worksheet

    headers = list(first_item.keys())

    for column, header in enumerate(headers, start=1):
        cell = worksheet.cell(row=1, column=column, value=str(header))
        cell.font = Font(bold=True)

    for row_index, item in enumerate(data, start=2):
        for column_index, header in enumerate(headers, start=1):
            value = item.get(header)
            if isinstance(value, (dict, list)):
                value = str(value)
            worksheet.cell(row=row_index, column=column_index, value=value)

    # Set reasonable column widths
    for col_idx in range(1, len(headers) + 1):
        col_letter = worksheet.cell(row=1, column=col_idx).column_letter
        worksheet.column_dimensions[col_letter].width = 22

    return worksheet


def build_excel_report(days=30):
    report_data = get_export_report_data(days=days)

    workbook = Workbook()
    default_sheet = workbook.active
    workbook.remove(default_sheet)

    existing_titles = []

    # Overview Metadata Sheet
    overview_title = sanitize_sheet_title("Overview", existing_titles)
    existing_titles.append(overview_title)
    overview_sheet = workbook.create_sheet(title=overview_title)

    overview_sheet["A1"] = "Mockii Platform Admin Report"
    overview_sheet["A1"].font = Font(bold=True, size=14)
    overview_sheet["A2"] = "Analytics Period"
    overview_sheet["B2"] = f"{days} Days"
    overview_sheet["A2"].font = Font(bold=True)

    overview_sheet["A4"] = "Report Category"
    overview_sheet["B4"] = "Key Summary Metric"
    overview_sheet["C4"] = "Value"
    overview_sheet["A4"].font = Font(bold=True)
    overview_sheet["B4"].font = Font(bold=True)
    overview_sheet["C4"].font = Font(bold=True)

    ov_row = 5
    for report_name, report in report_data.items():
        if isinstance(report, dict):
            summary = report.get("summary")
            if isinstance(summary, dict):
                for metric, val in summary.items():
                    if not isinstance(val, (dict, list)):
                        overview_sheet.cell(row=ov_row, column=1, value=report_name)
                        overview_sheet.cell(row=ov_row, column=2, value=str(metric))
                        overview_sheet.cell(row=ov_row, column=3, value=val)
                        ov_row += 1

    overview_sheet.column_dimensions["A"].width = 25
    overview_sheet.column_dimensions["B"].width = 30
    overview_sheet.column_dimensions["C"].width = 20

    # Build report sheets
    for report_name, report in report_data.items():
        if not isinstance(report, dict):
            continue

        # Scalar data on root level
        scalar_data = {
            k: v for k, v in report.items()
            if not isinstance(v, (dict, list))
        }
        if scalar_data:
            write_dict_sheet(workbook, report_name, scalar_data, existing_titles)

        # Iterate nested elements
        for key, value in report.items():
            if isinstance(value, list):
                write_list_sheet(workbook, f"{report_name} {key}", value, existing_titles)
            elif isinstance(value, dict):
                nested_scalars = {
                    nk: nv for nk, nv in value.items()
                    if not isinstance(nv, (dict, list))
                }
                if nested_scalars:
                    write_dict_sheet(
                        workbook,
                        f"{report_name} {key}",
                        nested_scalars,
                        existing_titles,
                    )

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def build_csv_report(days=30):
    report_data = get_export_report_data(days=days)

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Mockii Admin Report"])
    writer.writerow(["Analytics Period", f"{days} Days"])
    writer.writerow([])
    writer.writerow(["Report", "Section", "Metric", "Value"])

    for report_name, report in report_data.items():
        if not isinstance(report, dict):
            continue

        # Top-level scalar metrics
        for metric, value in report.items():
            if not isinstance(value, (dict, list)):
                writer.writerow([report_name, "General", metric, value])

        # Nested dictionary sections (e.g. summary, completion)
        for section_name, section_content in report.items():
            if isinstance(section_content, dict):
                for metric, value in section_content.items():
                    if not isinstance(value, (dict, list)):
                        writer.writerow([report_name, section_name, metric, value])

    return output.getvalue()
