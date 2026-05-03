import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import zipfile
import shutil
import subprocess
import threading
import json
import io
from PIL import Image

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"

LANG = {
    "ru": {
        "title": "Easy Game Installer (EGI) v1.1",
        "tab_install": "Installer",
        "tab_make": "Maegi (Maker)",
        "no_icon": "Нет иконки",
        "select_egi_label": "Выберите .egi файл",
        "btn_select_egi": "ВЫБРАТЬ ПАКЕТ (.EGI)",
        "btn_install": "УСТАНОВИТЬ",
        "make_title": "Создание пакета egi",
        "ph_title": "Название пакета",
        "ph_desc": "Описание и версия",
        "obb_check": "OBB кэш не требуется",
        "btn_folder": "1. ВЫБРАТЬ ПАПКУ ИСТОЧНИКА",
        "btn_build": "2. СОБРАТЬ EGI",
        "adb_not_found_title": "ADB не найден",
        "adb_not_found_msg": "ADB не обнаружен в системе. Пожалуйста, укажите путь к adb.exe вручную.",
        "adb_select_title": "Выберите adb.exe",
        "err_no_adb": "ОШИБКА: Путь к ADB не задан!",
        "log_adb": "Использую ADB: {}",
        "err_no_device": "Устройство не найдено! Проверь USB/Отладку.",
        "log_install": "Установка: {}...",
        "log_obb": "Копирование кэша: {}...",
        "log_done": "УСТАНОВКА ЗАВЕРШЕНА!",
        "log_temp": "Временные файлы удалены.",
        "done_title": "egi",
        "done_msg": "Все файлы успешно установлены!",
        "build_ok_title": "egi",
        "build_ok_msg": "Пакет успешно создан!",
        "build_err_title": "Ошибка сборки",
        "err_generic": "Ошибка: {}",
        "lang_btn": "EN",
    },
    "en": {
        "title": "Easy Game Installer (EGI) v1.1",
        "tab_install": "Installer",
        "tab_make": "Maegi (Maker)",
        "no_icon": "No icon",
        "select_egi_label": "Select .egi file",
        "btn_select_egi": "SELECT PACKAGE (.EGI)",
        "btn_install": "INSTALL",
        "make_title": "Create egi Package",
        "ph_title": "Package name",
        "ph_desc": "Description and version",
        "obb_check": "OBB cache not required",
        "btn_folder": "1. SELECT SOURCE FOLDER",
        "btn_build": "2. BUILD EGI",
        "adb_not_found_title": "ADB not found",
        "adb_not_found_msg": "ADB was not found on this system. Please select the path to adb.exe manually.",
        "adb_select_title": "Select adb.exe",
        "err_no_adb": "ERROR: ADB path is not set!",
        "log_adb": "Using ADB: {}",
        "err_no_device": "Device not found! Check USB / USB Debugging.",
        "log_install": "Installing: {}...",
        "log_obb": "Copying cache: {}...",
        "log_done": "INSTALLATION COMPLETE!",
        "log_temp": "Temporary files removed.",
        "done_title": "egi",
        "done_msg": "All files installed successfully!",
        "build_ok_title": "egi",
        "build_ok_msg": "Package created successfully!",
        "build_err_title": "Build error",
        "err_generic": "Error: {}",
        "lang_btn": "RU",
    },
}

current_lang = "ru"


def t(key, *args):
    s = LANG[current_lang].get(key, key)
    return s.format(*args) if args else s


def get_adb_path():
    try:
        subprocess.run(["adb", "version"], capture_output=True, check=True)
        return "adb"
    except:
        pass

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            saved_path = config.get("adb_path")
            if saved_path and os.path.exists(saved_path):
                return f'"{saved_path}"'

    messagebox.showinfo(t("adb_not_found_title"), t("adb_not_found_msg"))
    path = filedialog.askopenfilename(title=t("adb_select_title"), filetypes=[("Executables", "*.exe")])

    if path:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"adb_path": path}, f)
        return f'"{path}"'

    return None


class EgiApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(t("title"))
        self.geometry("650x750")

        self.lang_btn = ctk.CTkButton(self, text=t("lang_btn"), width=50, height=28, command=self.toggle_lang)
        self.lang_btn.pack(anchor="ne", padx=12, pady=(8, 0))

        self.tabview = ctk.CTkTabview(self, width=630, height=690)
        self.tabview.pack(padx=10, pady=(4, 10))

        self.tab_install = self.tabview.add(t("tab_install"))
        self.tab_make = self.tabview.add(t("tab_make"))

        self.setup_install_tab()
        self.setup_make_tab()

    def toggle_lang(self):
        global current_lang
        current_lang = "en" if current_lang == "ru" else "ru"
        self.refresh_ui()

    def refresh_ui(self):
        self.title(t("title"))
        self.lang_btn.configure(text=t("lang_btn"))

        self.icon_label.configure(text=t("no_icon"))
        self.label_inst.configure(text=t("select_egi_label"))
        self.btn_select_egi.configure(text=t("btn_select_egi"))
        self.btn_start_install.configure(text=t("btn_install"))

        self.label_make.configure(text=t("make_title"))
        self.entry_title.configure(placeholder_text=t("ph_title"))
        self.entry_desc.configure(placeholder_text=t("ph_desc"))
        self.obb_not_required.configure(text=t("obb_check"))
        self.btn_select_folder.configure(text=t("btn_folder"))
        self.btn_build.configure(text=t("btn_build"))

    def setup_install_tab(self):
        self.icon_label = ctk.CTkLabel(self.tab_install, text=t("no_icon"), width=120, height=120, fg_color="gray20", corner_radius=15)
        self.icon_label.pack(pady=15)

        self.label_inst = ctk.CTkLabel(self.tab_install, text=t("select_egi_label"), font=("Arial", 18, "bold"))
        self.label_inst.pack(pady=5)

        self.desc_label = ctk.CTkLabel(self.tab_install, text="", font=("Arial", 13), text_color="gray", wraplength=500)
        self.desc_label.pack(pady=5)

        self.btn_select_egi = ctk.CTkButton(self.tab_install, text=t("btn_select_egi"), height=40, command=self.select_egi)
        self.btn_select_egi.pack(pady=15)

        self.progress = ctk.CTkProgressBar(self.tab_install, width=500)
        self.progress.pack(pady=10)
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self.tab_install, width=550, height=180, font=("Consolas", 12))
        self.log_box.pack(pady=10)

        self.btn_start_install = ctk.CTkButton(self.tab_install, text=t("btn_install"), fg_color="#2ecc71", hover_color="#27ae60", height=45, command=self.start_install_thread)
        self.btn_start_install.pack(pady=10)

    def setup_make_tab(self):
        self.label_make = ctk.CTkLabel(self.tab_make, text=t("make_title"), font=("Arial", 18, "bold"))
        self.label_make.pack(pady=15)

        self.entry_title = ctk.CTkEntry(self.tab_make, placeholder_text=t("ph_title"), width=450)
        self.entry_title.pack(pady=8)

        self.entry_desc = ctk.CTkEntry(self.tab_make, placeholder_text=t("ph_desc"), width=450)
        self.entry_desc.pack(pady=8)

        self.obb_not_required = ctk.CTkCheckBox(self.tab_make, text=t("obb_check"))
        self.obb_not_required.pack(pady=12)

        self.btn_select_folder = ctk.CTkButton(self.tab_make, text=t("btn_folder"), width=250, command=self.select_source_folder)
        self.btn_select_folder.pack(pady=10)

        self.btn_build = ctk.CTkButton(self.tab_make, text=t("btn_build"), fg_color="#9b59b6", hover_color="#8e44ad", width=300, height=45, command=self.build_egi)
        self.btn_build.pack(pady=25)

    def log(self, text):
        self.log_box.insert(tk.END, f"> {text}\n")
        self.log_box.see(tk.END)

    def extract_icon_from_apk(self, apk_path, output_path):
        try:
            with zipfile.ZipFile(apk_path, 'r') as z:
                icon_targets = [
                    'res/drawable-xxhdpi-v4/ic_launcher.png',
                    'res/mipmap-xxhdpi-v4/ic_launcher.png',
                    'res/drawable-hdpi/icon.png',
                    'res/mipmap-hdpi/ic_launcher.png',
                    'res/drawable/icon.png'
                ]
                for target in icon_targets:
                    if target in z.namelist():
                        with open(output_path, "wb") as f:
                            f.write(z.read(target))
                        return True
        except:
            pass
        return False

    def select_egi(self):
        path = filedialog.askopenfilename(filetypes=[("EGI Files", "*.egi")])
        if path:
            self.selected_egi = path
            self.load_preview(path)

    def load_preview(self, path):
        try:
            with zipfile.ZipFile(path, 'r') as z:
                if "icon.png" in z.namelist():
                    img_data = z.read("icon.png")
                    img = Image.open(io.BytesIO(img_data))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 120))
                    self.icon_label.configure(image=ctk_img, text="")

                if "info.json" in z.namelist():
                    info = json.loads(z.read("info.json").decode('utf-8'))
                    self.label_inst.configure(text=info.get("title", "Game"))
                    self.desc_label.configure(text=info.get("description", ""))
        except:
            pass

    def select_source_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.source_dir = path

    def start_install_thread(self):
        if hasattr(self, 'selected_egi'):
            self.btn_start_install.configure(state="disabled")
            threading.Thread(target=self.install_process, daemon=True).start()

    def install_process(self):
        adb_path = get_adb_path()
        if not adb_path:
            self.log(t("err_no_adb"))
            self.btn_start_install.configure(state="normal")
            return

        temp_dir = "temp_maegi"
        try:
            self.log(t("log_adb", adb_path))
            adb_check = subprocess.run(f"{adb_path} devices", shell=True, capture_output=True, text=True)
            lines = adb_check.stdout.strip().split('\n')
            if not any("device" in line and "List" not in line for line in lines):
                self.log(t("err_no_device"))
                return

            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            with zipfile.ZipFile(self.selected_egi, 'r') as z:
                z.extractall(temp_dir)
            self.progress.set(0.3)

            apk_folder = os.path.join(temp_dir, "apk")
            if os.path.exists(apk_folder):
                apks = [f for f in os.listdir(apk_folder) if f.endswith('.apk')]
                for apk in apks:
                    self.log(t("log_install", apk))
                    subprocess.run(f'{adb_path} install "{os.path.join(apk_folder, apk)}"', shell=True)

            obb_folder = os.path.join(temp_dir, "obb")
            if os.path.exists(obb_folder) and os.listdir(obb_folder):
                for f in os.listdir(obb_folder):
                    self.log(t("log_obb", f))
                    subprocess.run(f'{adb_path} push "{os.path.join(obb_folder, f)}" /sdcard/Android/obb/', shell=True)

            self.progress.set(1.0)
            self.log(t("log_done"))
            messagebox.showinfo(t("done_title"), t("done_msg"))
        except Exception as e:
            self.log(t("err_generic", e))
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                self.log(t("log_temp"))
            self.btn_start_install.configure(state="normal")

    def build_egi(self):
        if not hasattr(self, 'source_dir'):
            return

        title = self.entry_title.get()
        desc = self.entry_desc.get()
        save_path = filedialog.asksaveasfilename(defaultextension=".egi", filetypes=[("EGI Files", "*.egi")])

        if save_path:
            try:
                apk_dir = os.path.join(self.source_dir, "apk")
                icon_file = os.path.join(self.source_dir, "icon.png")
                if not os.path.exists(icon_file) and os.path.exists(apk_dir):
                    apks = [f for f in os.listdir(apk_dir) if f.endswith('.apk')]
                    if apks:
                        self.extract_icon_from_apk(os.path.join(apk_dir, apks[0]), icon_file)

                meta = {"title": title, "description": desc}
                with open(os.path.join(self.source_dir, "info.json"), "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=4)

                temp_zip = save_path.replace(".egi", "")
                shutil.make_archive(temp_zip, 'zip', self.source_dir)
                if os.path.exists(save_path):
                    os.remove(save_path)
                os.rename(temp_zip + ".zip", save_path)
                messagebox.showinfo(t("build_ok_title"), t("build_ok_msg"))
            except Exception as e:
                messagebox.showerror(t("build_err_title"), str(e))


if __name__ == "__main__":
    app = EgiApp()
    app.mainloop()
