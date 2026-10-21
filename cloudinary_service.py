import cloudinary
import cloudinary.uploader

cloud_name = 'nxm4cewr'
api_key = '485395155977232'
secret_key = 'StJm1vgl-JV_5zaLZsl2kOgMghU'

# Connecting to cloudinary
cloudinary.config(
    cloud_name=cloud_name,
    api_key=api_key,
    api_secret=secret_key
)
print("cloudinary configuration succesful")

def upload_pdf(pdf_file):
    try:
        file_path = f"receipts/{pdf_file}.pdf"
        # upload pdf
        upload = cloudinary.uploader.upload(file_path, resource_type = "raw")
        receipts_url = upload["secure_url"]
        
        print("successful cloudinary upload")
        print(receipts_url)
        return "success"
    except Exception as e:
        print(f"upload failed: {e}")
        return "failed cloudinary upload"    