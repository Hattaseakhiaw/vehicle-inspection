from flask import Flask, render_template, request
from flask_mail import Mail, Message
import pandas as pd
import os
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.drawing.image import Image  # เพิ่มการนำเข้า Image
import pillow_heif
from PIL import Image as PILImage
from werkzeug.utils import secure_filename  # นำเข้า secure_filename ที่นี่

app = Flask(__name__)

# การตั้งค่าการเชื่อมต่อกับเซิร์ฟเวอร์อีเมล
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hatta.seakh@gmail.com'
app.config['MAIL_PASSWORD'] = 'izpj wupb gxbu uysl'
app.config['MAIL_DEFAULT_SENDER'] = 'hatta.seak@gmail.com'

mail = Mail(app)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'heic', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ฟังก์ชันแปลง HEIC เป็น JPG
def convert_heic_to_jpg(heic_path):
    heif_file = pillow_heif.open(heic_path)
    image = PILImage.frombytes(heif_file.mode, heif_file.size, heif_file.data)
    jpg_path = heic_path.replace(".heic", ".jpg")
    image.save(jpg_path, format="JPEG")
    return jpg_path

# รายการตรวจสอบยานพาหนะ
important_items = {
    "ระดับน้ำหล่อเย็น , น้ำมันเครื่อง  การรั่วขณะติดเครื่องยนต์",
    "ระดับน้ำมันเบรก , คลัช , เพาเวอร์  การรั่วขณะติดเครื่องยนต์",
    "ตรวจสอบมาตรวัดบนแนวหน้าปัทม์และสัญญาณไฟเตือน (โดยเฉพาะไฟเตือนระดับน้ำมันเบรค)",
    "ตรวจสอบสภาพวาล์ว , ท่อ , ข้อต่อต่างๆ",
    "สภาพปั้มลงสินค้าและรอยการรั่วหยด",
    "เกจแสดงความร้อนเครื่องยนต์ (ดิจิตอล)"
}

inspection_items = [
    {"id": i + 1, "name": name, "important": name in important_items} for i, name in enumerate([  
        "ระดับน้ำหล่อเย็น , น้ำมันเครื่อง  การรั่วขณะติดเครื่องยนต์",
        "ระดับน้ำมันเบรก , คลัช , เพาเวอร์  การรั่วขณะติดเครื่องยนต์",
        "ระดับน้ำมันเชื้อเพลิง  การรั่วขณะติดเครื่องยนต์",
        "ทดสอบการทำงานของเครื่องยนต์และเสียงผิดปกติ",
        "ทดสอบการทำงานของระบบ  เบรก ,  ครัช  ,  เกียร์ , พวงมาลัย",
        "ตรวจสอบมาตรวัดบนแนวหน้าปัทม์และสัญญาณไฟเตือน (โดยเฉพาะไฟเตือนระดับน้ำมันเบรค)",
        "ทดสอบการทำงานใบปัดน้ำฝนและน้ำฉีดกระจก",
        "เข็มขัดนิรภัยใช้งานได้",
        "กระจกมองข้าง  ซ้าย-ขวา",
        "ระบบไฟแสงสว่างหน้า / ไฟเลี้ยว  / ไฟเบรก / ไฟหรี่ / ไฟหลังคา / แตร",
        "สภาพแบตเตอรี่และน้ำกลั่น / ฝาครอบ",
        "สภาพยางหน้า / หลัง / อะไหล่ / แรงดันลมยาง / กระทะล้อ / น็อตล้อ",
        "ถ่ายน้ำจากถังลม / วาล์วเดรนลม",
        "สภาพทั่วไปรอบรถ ( รอยเฉี่ยวชน )",
        "หมวกนิรภัย , กระบังหน้า",
        "แว่นตานิรภัย , ก๊อกเกิ้ล",
        "ถุงมือป้องกันสารเคมี",
        "ชุด PVC ป้องกันสารเคมี",
        "รองเท้านิรภัย , รองเท้าบู๊ทยาง",
        "หน้ากากกรองสารเคมี",
        "ขวดน้ำล้างตา",
        "เข็มขัดกันตกจากที่สูง",
        "ป้ายสัญลักษณ์แสดงข้อมูลสินค้า(แผ่น UN.ใหญ่) ทั้งหมด 3 ด้าน",
        "เอกสารความปลอดภัยเกี่ยวกับสารเคมี (SDS) และแผนฉุกเฉิน",
        "ถังดับเพลิง ( เกจอยู่ในพื้นที่สีเขียว )",
        "ไม้หมอนหนุนล้อ",
        "กรวยจราจร 2 อัน",
        "ถังเดรนประจำรถ ( ถังสแตนเลสสำหรับรถโซลเวนท์ )",
        "ลิ่ม, ค้อน",
        "พลั่ว",
        "เสื้อกั๊กสะท้อนแสง",
        "วัสดุสำหรับซับสาร",
        "ปูนขาว",
        "แผ่นพลาสติก",
        "เทปกั้นบริเวณ",
        "ไฟฉาย",
        "ประแจรวมหลายเบอร์ 1 ชุด",
        "ตรวจสภาพแท้งค์หารอยรั่มซึม",
        "ตรวจสอบสภาพวาล์ว , ท่อ , ข้อต่อต่างๆ",
        "หน้าแปลน 2 นิ้ว",
        "หน้าแปลน 3 นิ้ว",
        "ล๊อกเร็วตัวผู้ 2 นิ้ว ( Part E )",
        "ล๊อกเร็วตัวเมีย 2 นิ้ว ( Part C )",
        "สภาพสายส่งสินค้า",
        "สภาพสายสำรองส่งสินค้า ( ถ้ามี )",
        "สภาพปั้มลงสินค้าและรอยการรั่วหยด",
        "สภาพสวิทช์ปุ่มกดฉุกเฉินรอบรถ 3 จุด และทดสอบการทำงาน",
        "ทดสอบการทำงานของวาล์วฉุกเฉิน ( Internal Valve )",
        "ปลั๊ก 5 ขา 16 แอมป์",
        "ปลั๊ก 5 ขา 32 แอมป์",
        "เกจแสดงความร้อนเครื่องยนต์ (ดิจิตอล)",
        "ข้อต่อเกลียวนอกละเอียดเกลียวในหยาบ 3 นิ้ว",
        "ข้อต่อเกลียวนอกหยาบเกลียวในละเอียด 3 นิ้ว",
        "ข้อต่อตัวผู้ 3 นิ้ว เกลียวใน(Part  A)",
        "ข้อต่อตัวเมีย 3 นิ้ว เกลียวอก(Part B)",
        "หัวกรอกสำหรับกรอกสารเคมี"
    ])
]

# ฟังก์ชันส่งอีเมล
def send_email_with_attachment(excel_filename):
    msg = Message(
        'Inspection Report',  
        recipients=['hatta.seak@gmail.com']  
    )
    with app.open_resource(excel_filename) as fp:
        msg.attach(excel_filename, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', fp.read())

    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

# หน้าแรกของแอปพลิเคชัน
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        license_plate = request.form['license_plate']
        date = request.form['date']
        driver = request.form['driver']
        inspection_data = []

        # เก็บข้อมูลการตรวจสอบ
        for item in inspection_items:
            status = request.form.get(f"status_{item['id']}")
            image = request.files.get(f"image_{item['id']}")

            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)  # ใช้ secure_filename ที่นำเข้ามา
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(filepath)
                if filename.lower().endswith(".heic"):
                    convert_heic_to_jpg(filepath)

            inspection_data.append({
                'id': item['id'],
                'name': item['name'],
                'status': status,
                'image': filepath if image else None
            })

        # สร้างไฟล์ Excel
        excel_filename = generate_excel_report(inspection_data, license_plate, date, driver)

        # ส่งอีเมล
        send_email_with_attachment(excel_filename)

        return render_template('index.html', items=inspection_items, message="ส่งรายงานแล้ว")
    return render_template('index.html', items=inspection_items)

# สร้างไฟล์ Excel
def generate_excel_report(data, license_plate, date, driver):
    # สร้าง DataFrame สำหรับข้อมูลการตรวจสอบ
    df = pd.DataFrame(data)

    # สร้างไฟล์ Excel
    excel_filename = f"static/{license_plate}_inspection_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
    
    # เปิดไฟล์ Excel และเพิ่มข้อมูลการตรวจสอบ
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        workbook = writer.book
        sheet = workbook.create_sheet('Inspection Report')
        
        # เพิ่มข้อมูลทะเบียนรถ, วันที่ และพนักงานขับรถในแถวแรก
        sheet['A1'] = 'License Plate'
        sheet['B1'] = license_plate
        sheet['A2'] = 'Date'
        sheet['B2'] = date
        sheet['A3'] = 'Driver'
        sheet['B3'] = driver

        # เขียนข้อมูลการตรวจสอบในเซลล์ถัดไป
        for index, row in df.iterrows():
            sheet.append([row['name'], row['status']])

            # ถ้ามีไฟล์ภาพในคอลัมน์ 'image' ของข้อมูลการตรวจสอบ
            if row['image']:
                try:
                    img = Image(row['image'])  # เพิ่มรูปภาพ
                    img.width = 100  # ปรับขนาดภาพตามต้องการ
                    img.height = 100
                    # เพิ่มรูปภาพในเซลล์ที่เหมาะสม
                    sheet.add_image(img, f'C{index + 4}')  # แทรกรูปในคอลัมน์ C
                except Exception as e:
                    print(f"Error inserting image: {e}")

    return excel_filename

if __name__ == '__main__':
    app.run(debug=True)
