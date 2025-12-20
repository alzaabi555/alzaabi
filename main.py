import flet as ft
import openpyxl
import csv
import datetime
import json
import os

# --- إعدادات ثابتة ---
POSITIVE_BEHAVIORS = ["مشاركة فعالة", "حل الواجب", "احترام المعلم", "نظافة", "تعاون", "إجابة ذكية"]
NEGATIVE_BEHAVIORS = ["إزعاج", "نسيان الكتاب", "تأخر", "نوم في الحصة", "استخدام الهاتف", "شغب"]

class SchoolApp:
    def __init__(self):
        self.school_data = {}
        self.current_class = ""
        self.current_student_idx = None
        self.selected_date = datetime.date.today().strftime("%Y-%m-%d")
        self.backup_file = "school_backup.json"

    def main(self, page: ft.Page):
        # إعدادات الصفحة
        page.title = "ضبط سلوكيات الطلبة"
        page.rtl = True
        page.theme_mode = ft.ThemeMode.LIGHT
        page.scroll = None
        page.bgcolor = "#f5f5f7"
        page.fonts = {"Arabic": "fonts/NotoNaskhArabic-Regular.ttf"}
        page.theme = ft.Theme(font_family="Arabic")

        # --- إدارة البيانات ---
        def load_data():
            try:
                data = page.client_storage.get("school_db")
                if isinstance(data, dict):
                    self.school_data = data
                else:
                    self.school_data = {}
            except:
                self.school_data = {}

        def save_data():
            page.client_storage.set("school_db", self.school_data)

        load_data()

        # --- عناصر الواجهة ---
        txt_class_name = ft.TextField(
            hint_text="اسم الفصل",
            bgcolor="white",
            border_radius=10,
            expand=True,
            filled=True,
            border_color="indigo"
        )
        
        txt_student_name = ft.TextField(
            hint_text="اسم الطالب",
            bgcolor="white",
            border_radius=10,
            expand=True,
            filled=True,
            border_color="indigo"
        )
        
        # زر التاريخ
        date_button = ft.ElevatedButton(
            text=f"📅 تاريخ اليوم: {self.selected_date}",
            bgcolor="indigo",
            color="white",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            on_click=lambda _: open_date_picker()
        )

        def open_date_picker():
            date_picker = ft.DatePicker(
                first_date=datetime.datetime(2023, 10, 1),
                last_date=datetime.datetime(2030, 10, 1),
                on_change=change_date
            )
            page.overlay.append(date_picker)
            date_picker.pick_date()

        def change_date(e):
            if e.control.value:
                self.selected_date = e.control.value.strftime("%Y-%m-%d")
                date_button.text = f"📅 التاريخ: {self.selected_date}"
                if self.current_class:
                    show_students_view(None)
                page.update()

        # --- استيراد الملفات ---
        file_picker = ft.FilePicker()
        page.overlay.append(file_picker)

        def on_file_picked(e: ft.FilePickerResultEvent):
            if not e.files or not self.current_class:
                return
                
            try:
                file_path = e.files[0].path
                raw_rows = []
                
                # معالجة Excel
                if e.files[0].name.endswith(('xlsx', 'xls')):
                    wb = openpyxl.load_workbook(file_path, data_only=True)
                    sheet = wb.active
                    for row in sheet.iter_rows(values_only=True):
                        raw_rows.append([str(c) if c else "" for c in row])
                
                # معالجة CSV
                elif e.files[0].name.endswith('.csv'):
                    encodings_to_try = ['utf-8-sig', 'cp1256', 'windows-1256', 'iso-8859-6', 'utf-8']
                    
                    for enc in encodings_to_try:
                        try:
                            with open(file_path, 'r', encoding=enc) as f:
                                temp_rows = list(csv.reader(f))
                                text_sample = str(temp_rows)
                                if any("\u0600" <= c <= "\u06FF" for c in text_sample):
                                    raw_rows = temp_rows
                                    break
                        except:
                            continue

                # إضافة الأسماء
                count = 0
                current_students = self.school_data[self.current_class]
                existing_names = {s['name'] for s in current_students}

                for row in raw_rows:
                    for cell in row:
                        val = str(cell).strip()
                        cleaned_val = "".join([c for c in val if c.isalnum() or c.isspace()])
                        
                        if len(cleaned_val) > 2 and not cleaned_val.isdigit():
                            if cleaned_val not in existing_names:
                                current_students.append({
                                    "name": cleaned_val, 
                                    "score": 0, 
                                    "history": [], 
                                    "attendance": {}
                                })
                                existing_names.add(cleaned_val)
                                count += 1
                
                save_data()
                show_students_view(None)
                page.snack_bar = ft.SnackBar(ft.Text(f"✅ تم استيراد {count} اسم بنجاح"), bgcolor="green")
                page.snack_bar.open = True
                page.update()

            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"❌ حدث خطأ: {ex}"), bgcolor="red")
                page.snack_bar.open = True
                page.update()

        file_picker.on_result = on_file_picked

        # --- تصدير البيانات ---
        def export_data(e):
            if not self.current_class:
                return
                
            students = self.school_data[self.current_class]
            output = "الاسم\tالنقاط\tأيام الغياب\n"
            for s in students:
                absent_count = list(s.get('attendance', {}).values()).count('absent')
                output += f"{s['name']}\t{s['score']}\t{absent_count}\n"
            
            page.set_clipboard(output)
            page.snack_bar = ft.SnackBar(ft.Text("📋 تم نسخ البيانات! ألصقها في Excel"), bgcolor="blue")
            page.snack_bar.open = True
            page.update()

        # --- التنقل ---
        def route_change(route):
            page.views.clear()
            
            # الصفحة الرئيسية
            if page.route == "/":
                def add_class(e):
                    if txt_class_name.value and txt_class_name.value not in self.school_data:
                        self.school_data[txt_class_name.value] = []
                        save_data()
                        txt_class_name.value = ""
                        route_change(None)

                def go_to_class(name):
                    self.current_class = name
                    page.go("/class")
                
                def delete_class(name):
                    del self.school_data[name]
                    save_data()
                    route_change(None)
                
                def clear_all(e):
                    self.school_data = {}
                    save_data()
                    route_change(None)

                # قائمة الفصول
                classes_list = ft.ListView(expand=True, spacing=10, padding=15)
                for name in self.school_data:
                    count = len(self.school_data[name])
                    classes_list.controls.append(
                        ft.Card(
                            elevation=2,
                            content=ft.ListTile(
                                leading=ft.Icon(ft.icons.CLASS_, color="indigo"),
                                title=ft.Text(name, weight="bold"),
                                subtitle=ft.Text(f"👥 {count} طالب"),
                                trailing=ft.IconButton(
                                    ft.icons.DELETE,
                                    icon_color="red",
                                    on_click=lambda e, n=name: delete_class(n)
                                ),
                                on_click=lambda e, n=name: go_to_class(n)
                            )
                        )
                    )

                page.views.append(
                    ft.View(
                        "/",
                        [
                            ft.AppBar(
                                title=ft.Text("🏫 ضبط سلوكيات الطلبة"),
                                bgcolor="indigo",
                                color="white",
                                leading=ft.IconButton(
                                    ft.icons.INFO_OUTLINE,
                                    tooltip="معلومات",
                                    on_click=lambda _: show_info_dialog()
                                ),
                                actions=[
                                    ft.IconButton(
                                        ft.icons.DELETE_FOREVER,
                                        tooltip="حذف الكل",
                                        on_click=clear_all
                                    )
                                ]
                            ),
                            ft.Container(
                                padding=20,
                                content=ft.Column([
                                    ft.Text("➕ إضافة فصل جديد", size=20, weight="bold", color="indigo"),
                                    ft.Row([
                                        txt_class_name,
                                        ft.FloatingActionButton(
                                            icon=ft.icons.ADD,
                                            bgcolor="green",
                                            on_click=add_class
                                        )
                                    ])
                                ])
                            ),
                            ft.Divider(),
                            ft.Container(
                                padding=10,
                                content=ft.Column([
                                    ft.Text("📚 الفصول المتاحة", size=18, weight="bold", color="indigo"),
                                    classes_list
                                ])
                            )
                        ],
                        bgcolor="#f2f2f7"
                    )
                )

            # صفحة الفصل
            elif page.route == "/class":
                students = self.school_data.get(self.current_class, [])

                def add_student(e):
                    if txt_student_name.value:
                        students.append({
                            "name": txt_student_name.value,
                            "score": 0,
                            "history": [],
                            "attendance": {}
                        })
                        save_data()
                        txt_student_name.value = ""
                        show_students_view(None)

                def toggle_attendance(student):
                    att = student.get('attendance', {})
                    current_status = att.get(self.selected_date, "present")
                    new_status = "absent" if current_status == "present" else "present"
                    att[self.selected_date] = new_status
                    student['attendance'] = att
                    save_data()
                    show_students_view(None)

                def add_behavior(student, behavior_type, note):
                    if 'history' not in student:
                        student['history'] = []
                    
                    student['history'].append({
                        "date": self.selected_date,
                        "type": behavior_type,
                        "note": note
                    })
                    
                    if behavior_type == 'pos':
                        student['score'] += 1
                    else:
                        student['score'] -= 1
                    
                    save_data()
                    page.close_dialog()
                    show_students_view(None)

                def open_behavior_dialog(student):
                    pos_col = ft.Column([
                        ft.ListTile(
                            title=ft.Text(b),
                            leading=ft.Icon(ft.icons.ADD_CIRCLE, color="green"),
                            on_click=lambda e, n=b: add_behavior(student, 'pos', n)
                        ) for b in POSITIVE_BEHAVIORS
                    ])
                    
                    neg_col = ft.Column([
                        ft.ListTile(
                            title=ft.Text(b),
                            leading=ft.Icon(ft.icons.REMOVE_CIRCLE, color="red"),
                            on_click=lambda e, n=b: add_behavior(student, 'neg', n)
                        ) for b in NEGATIVE_BEHAVIORS
                    ])
                    
                    tabs = ft.Tabs(
                        selected_index=0,
                        tabs=[
                            ft.Tab(text="👍 إيجابي", content=ft.Container(content=pos_col, height=300)),
                            ft.Tab(text="👎 سلبي", content=ft.Container(content=neg_col, height=300))
                        ]
                    )
                    
                    page.dialog = ft.AlertDialog(
                        title=ft.Text(student['name']),
                        content=ft.Container(width=300, content=tabs)
                    )
                    page.dialog.open = True
                    page.update()

                def show_student_details(student):
                    attendance_log = student.get('attendance', {})
                    absent_days = [d for d, status in attendance_log.items() if status == 'absent']
                    history = student.get('history', [])
                    
                    # علامات التبويب
                    behavior_list = ft.ListView(expand=True, spacing=5)
                    if not history:
                        behavior_list.controls.append(ft.Text("لا يوجد سجل سلوكيات", color="grey", text_align="center"))
                    else:
                        for record in reversed(history):
                            icon = ft.icons.THUMB_UP if record['type'] == 'pos' else ft.icons.THUMB_DOWN
                            color = "green" if record['type'] == 'pos' else "red"
                            behavior_list.controls.append(
                                ft.ListTile(
                                    leading=ft.Icon(icon, color=color),
                                    title=ft.Text(record['note'], weight="bold"),
                                    subtitle=ft.Text(record['date'], size=12, color="grey")
                                )
                            )

                    absent_list = ft.ListView(expand=True, spacing=5)
                    if not absent_days:
                        absent_list.controls.append(ft.Text("الطالب منتظم", color="green", text_align="center"))
                    else:
                        for day in sorted(absent_days, reverse=True):
                            absent_list.controls.append(
                                ft.ListTile(
                                    leading=ft.Icon(ft.icons.EVENT_BUSY, color="red"),
                                    title=ft.Text(f"غائب يوم: {day}")
                                )
                            )

                    page.views.append(
                        ft.View(
                            "/student_details",
                            [
                                ft.AppBar(
                                    title=ft.Text(student['name']),
                                    bgcolor="indigo",
                                    color="white",
                                    leading=ft.IconButton(
                                        ft.icons.ARROW_BACK,
                                        on_click=lambda _: page.go("/class")
                                    )
                                ),
                                ft.Container(
                                    padding=20,
                                    content=ft.Row([
                                        ft.Column([
                                            ft.Text("النقاط", color="grey"),
                                            ft.Text(str(student['score']), size=30, weight="bold", color="blue")
                                        ], alignment="center"),
                                        ft.Container(width=20),
                                        ft.Column([
                                            ft.Text("الغياب", color="grey"),
                                            ft.Text(str(len(absent_days)), size=30, weight="bold", color="red")
                                        ], alignment="center"),
                                    ], alignment=ft.MainAxisAlignment.CENTER)
                                ),
                                ft.Tabs(
                                    selected_index=0,
                                    tabs=[
                                        ft.Tab(text="📋 السلوك", content=ft.Container(content=behavior_list, padding=10)),
                                        ft.Tab(text="📅 الغياب", content=ft.Container(content=absent_list, padding=10)),
                                    ],
                                    expand=True
                                )
                            ],
                            bgcolor="white"
                        )
                    )
                    page.update()

                # قائمة الطلاب
                students_lv = ft.ListView(expand=True, spacing=5, padding=10)
                
                for student in students:
                    att_record = student.get('attendance', {})
                    is_absent = att_record.get(self.selected_date) == "absent"
                    bg_color = "#ffebee" if is_absent else "white"
                    att_icon = ft.icons.CANCEL if is_absent else ft.icons.CHECK_CIRCLE
                    att_color = "red" if is_absent else "green"

                    students_lv.controls.append(
                        ft.Card(
                            color=bg_color,
                            elevation=0.5,
                            content=ft.ListTile(
                                leading=ft.IconButton(
                                    icon=att_icon,
                                    icon_color=att_color,
                                    tooltip="تغيير الحضور",
                                    on_click=lambda e, stu=student: toggle_attendance(stu)
                                ),
                                title=ft.Text(student['name'], weight="bold"),
                                subtitle=ft.Text(f"⭐ النقاط: {student['score']}", color="blue"),
                                trailing=ft.Row([
                                    ft.IconButton(
                                        ft.icons.ADD_COMMENT,
                                        icon_color="orange",
                                        tooltip="إضافة سلوك",
                                        on_click=lambda e, stu=student: open_behavior_dialog(stu)
                                    ),
                                    ft.IconButton(
                                        ft.icons.INFO,
                                        icon_color="purple",
                                        tooltip="تفاصيل",
                                        on_click=lambda e, stu=student: show_student_details(stu)
                                    )
                                ], spacing=5)
                            )
                        )
                    )

                page.views.append(
                    ft.View(
                        "/class",
                        [
                            ft.AppBar(
                                title=ft.Text(f"🎒 {self.current_class}"),
                                bgcolor="indigo",
                                color="white",
                                leading=ft.IconButton(
                                    ft.icons.ARROW_BACK,
                                    on_click=lambda _: page.go("/")
                                ),
                                actions=[
                                    ft.IconButton(
                                        ft.icons.COPY,
                                        tooltip="تصدير البيانات",
                                        on_click=export_data
                                    ),
                                    ft.IconButton(
                                        ft.icons.UPLOAD_FILE,
                                        tooltip="استيراد أسماء",
                                        on_click=lambda _: file_picker.pick_files()
                                    )
                                ]
                            ),
                            ft.Container(
                                padding=20,
                                content=ft.Column([
                                    date_button,
                                    ft.Divider(),
                                    ft.Text("➕ إضافة طالب جديد", size=18, weight="bold", color="indigo"),
                                    ft.Row([
                                        txt_student_name,
                                        ft.FloatingActionButton(
                                            icon=ft.icons.PERSON_ADD,
                                            bgcolor="green",
                                            on_click=add_student
                                        )
                                    ])
                                ])
                            ),
                            ft.Divider(),
                            ft.Container(
                                padding=10,
                                content=ft.Column([
                                    ft.Text("👥 قائمة الطلاب", size=18, weight="bold", color="indigo"),
                                    students_lv
                                ])
                            )
                        ],
                        bgcolor="#f2f2f7"
                    )
                )
            
            page.update()

        def show_students_view(_):
            route_change(None)

        def show_info_dialog():
            dlg = ft.AlertDialog(
                title=ft.Text("ℹ️ معلومات التطبيق", weight="bold"),
                content=ft.Column([
                    ft.Container(
                        padding=10,
                        bgcolor=ft.colors.BLUE_50,
                        border_radius=10,
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.PERSON, color="indigo"),
                                title=ft.Text("👨‍🏫 المعلم"),
                                subtitle=ft.Text("محمد درويش الزعابي", color="black", weight="bold")
                            ),
                            ft.Divider(),
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.SCHOOL, color="indigo"),
                                title=ft.Text("🏫 المدرسة"),
                                subtitle=ft.Text("الإبداع للبنين", color="black", weight="bold")
                            ),
                            ft.Divider(),
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.APP_REGISTRATION, color="indigo"),
                                title=ft.Text("📱 التطبيق"),
                                subtitle=ft.Text("ضبط سلوكيات الطلبة v1.0", color="green", weight="bold")
                            )
                        ])
                    )
                ], tight=True),
                actions=[
                    ft.TextButton("إغلاق", on_click=lambda e: page.close_dialog())
                ]
            )
            page.dialog = dlg
            dlg.open = True
            page.update()

        # إعداد التنقل
        page.on_route_change = route_change
        page.go("/")

if __name__ == "__main__":
    app = SchoolApp()
    ft.app(target=app.main, view=ft.WEB_BROWSER)