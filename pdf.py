from fpdf import FPDF

def generate_pdf(car_number, owner, reason, fine, total_pending, grand_total, date, time, image_path):
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "TRAFFIC CHALLAN", ln=True, align='C')
    pdf.ln(5)

    # Vehicle image (left side)
    pdf.image(image_path, x=10, y=25, w=80)

    # Owner details (right side)
    pdf.set_xy(100, 25)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 8, "Owner Details", ln=True)
    pdf.set_font("Arial", "", 12)
    for label, value in [("Name", owner[1]), ("Age", owner[2]), ("Place", owner[3]), ("Mobile", owner[4])]:
        pdf.set_x(100)
        pdf.cell(100, 8, f"{label}: {value}", ln=True)

    pdf.ln(5)

    # Challan details (right side)
    pdf.set_x(100)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 8, "Challan Details", ln=True)
    pdf.set_font("Arial", "", 12)
    for label, value in [
        ("Vehicle Number", car_number),
        ("Date & Time", f"{date}  {time}"),
        ("Violation", reason),
        ("Current Fine", f"Rs. {fine}"),
        ("Previous Pending", f"Rs. {total_pending}"),
        ("Total Amount", f"Rs. {grand_total}"),
    ]:
        pdf.set_x(100)
        pdf.cell(100, 8, f"{label}: {value}", ln=True)

    return bytes(pdf.output(dest='S'))
