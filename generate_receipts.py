from fpdf import FPDF
from cloudinary_service import upload_pdf

pdf = FPDF()

def create_pdf(payment_data, transaction_code):
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(200, 10, txt=payment_data, align="C")
    pdf.output(f"receipts/{transaction_code}.pdf")
    
    print("this is create pdf.......")
    # uploading pdf to cloudinary

    upload_pdf(transaction_code)
    
