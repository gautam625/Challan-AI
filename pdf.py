from fpdf import FPDF
import io

def generate_pdf(car_number, owner, reason, fine, total_pending, grand_total, date, time, image_path):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "TRAFFIC CHALLAN", ln=True, align='C')

    pdf.image(image_path, x=10, y=25, w=80)
    pdf.set_xy(100, 25)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 8, "Owner Details", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.set_x(100); pdf.cell(100, 8, f"Name: {owner[1]}", ln=True)
    pdf.set_x(100); pdf.cell(100, 8, f"Age: {owner[2]}", ln=True)
    pdf.set_x(100); pdf.cell(100, 8, f"Place: {owner[3]}", ln=True)
    pdf.set_x(100); pdf.cell(100, 8, f"Mobile: {owner[4]}", ln=True)

    pdf.ln(5)

    pdf.set_x(100)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 8, "Challan Details", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.set_x(100); pdf.cell(100, 8, f"Vehicle Number : {car_number}", ln=True)
    pdf.set_x(100); pdf.cell(100, 8, f"Date: {date} \t Time: {time}", ln=True)
    pdf.set_x(100); pdf.cell(100, 8, f"Violation: {reason}", ln=True)
    pdf.set_x(100); pdf.cell(100, 8, f"Current Fine: Rs. {fine}", ln=True)
    pdf.set_x(100); pdf.cell(100, 8, f"Previous Pending: Rs. {total_pending}", ln=True)
    pdf.set_x(100); pdf.cell(100, 8, f"Total Amount: Rs. {grand_total}", ln=True)

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return pdf_bytes