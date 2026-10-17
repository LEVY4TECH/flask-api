from fpdf import FPDF

pdf = FPDF()

def create_pdf(payment_data, transaction_code):
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(200, 10, txt=payment_data, align="C")
    pdf.output(f"receipts/{transaction_code}.pdf")
    
# create_pdf("Transaction Code : USD4G7FGD, Amount : 1, Date : 15/10/2026", "USD4G7FGD")
    
