import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import sqlite3
import pandas as pd
from fpdf import FPDF

class AttendanceApp(toga.App):
    def startup(self):
        # 1. إعداد قاعدة البيانات المحلية
        self.conn = sqlite3.connect('school_data.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS students 
                             (id INTEGER PRIMARY KEY, name TEXT, attendance TEXT, behavior TEXT)''')
        self.conn.commit()

        # 2. تصميم الواجهة (الأزرار العلوية)
        self.main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        btn_box = toga.Box(style=Pack(direction=ROW, padding=5))
        btn_import = toga.Button('استيراد من إكسل 📥', on_press=self.import_students, style=Pack(flex=1))
        btn_report = toga.Button('طباعة تقرير PDF 📄', on_press=self.export_pdf, style=Pack(flex=1))
        btn_box.add(btn_import, btn_report)

        # 3. جدول عرض الطلاب
        self.table = toga.Table(
            headings=['الاسم', 'الحضور', 'السلوك'],
            style=Pack(flex=1, padding=5)
        )
        self.load_data() # تحميل البيانات عند البدء

        self.main_box.add(btn_box)
        self.main_box.add(self.table)
        
        self.main_window = toga.MainWindow(title="نظام إدارة الطلاب")
        self.main_window.content = self.main_box
        self.main_window.show()

    # --- الوظائف المنطقية ---
    def load_data(self):
        self.cursor.execute("SELECT name, attendance, behavior FROM students")
        self.table.data = self.cursor.fetchall()

    def import_students(self, widget):
        try:
            # فتح منقي الملفات (Files App) في الآيفون
            file_path = self.main_window.open_file_dialog("اختر ملف إكسل", file_types=['xlsx', 'csv'])
            if file_path:
                df = pd.read_excel(file_path) if file_path.suffix == '.xlsx' else pd.read_csv(file_path)
                for name in df['الاسم']:
                    self.cursor.execute("INSERT INTO students (name, attendance, behavior) VALUES (?, 'غائب', 'لا يوجد')", (name,))
                self.conn.commit()
                self.load_data()
                self.main_window.info_dialog("نجاح", "تم استيراد قائمة الطلاب بنجاح")
        except Exception as e:
            self.main_window.error_dialog("خطأ", f"حدث خطأ أثناء الاستيراد: {str(e)}")

    def export_pdf(self, widget):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12) # ملاحظة: يتطلب إضافة خط يدعم العربية للتقارير الفعلية
        pdf.cell(200, 10, txt="تقرير الطلاب اليومي", ln=True, align='C')
        
        for row in self.table.data:
            line = f"Name: {row.name} | Status: {row.attendance} | Behavior: {row.behavior}"
            pdf.cell(200, 10, txt=line, ln=True)
        
        pdf.output("report.pdf")
        self.main_window.info_dialog("تم", "تم حفظ التقرير بصيغة PDF")
