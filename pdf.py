from fpdf import FPDF
def generate_pdf(car_number: str, owner: tuple, reason: str,
                 fine: int, pending: int, total: int,
                 date: str, time_str: str, image_path: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(False)

    # ── Header ────────────────────────────────────────────────────────────────
    pdf.set_fill_color(30, 30, 30)
    pdf.rect(0, 0, 210, 18, 'F')
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(210,0, "TRAFFIC CHALLAN", align='C', ln=True)
    pdf.set_text_color(0, 0, 0)

    # ── Vehicle image ─────────────────────────────────────────────────────────
    pdf.image(image_path, x=10, y=30, w=85)

    # ── Owner box ─────────────────────────────────────────────────────────────
    pdf.set_xy(105, 30)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(95, 8, " Owner Details", fill=True, ln=True)
    pdf.set_font("Helvetica", "", 10)
    for label, val in [("Name", owner[1]), ("Age", owner[2]),
                        ("Location", owner[3]), ("Mobile", owner[4])]:
        pdf.set_x(105)
        pdf.cell(35, 7, f"{label}:")
        pdf.cell(60, 7, str(val), ln=True)

    # ── Challan details ───────────────────────────────────────────────────────
    pdf.set_xy(105, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(95, 8, " Challan Details", fill=True, ln=True)
    pdf.set_font("Helvetica", "", 10)
    for label, val in [("Vehicle No.", car_number), ("Date & Time", f"{date}  {time_str}"),
                        ("Violation", reason), ("Current Fine", f"Rs. {fine}"),
                        ("Prev. Pending", f"Rs. {pending}")]:
        pdf.set_x(105)
        pdf.cell(40, 7, f"{label}:")
        pdf.cell(55, 7, str(val), ln=True)

    # Total amount row
    pdf.set_x(105)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(220, 50, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(95, 9, f"  Total Amount:  Rs. {total}", fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)

    # ── Footer ────────────────────────────────────────────────────────────────
    pdf.set_y(275)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, "This is a computer-generated challan. Pay promptly to avoid penalties.", align='C')

    return bytes(pdf.output(dest='S'))
