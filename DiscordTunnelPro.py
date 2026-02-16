import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import os
import sys
import ctypes
import threading
import time
import winreg
from PIL import Image, ImageDraw
import pystray

class DiscordTunnelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TR-Gate Pro v2.7")
        self.root.geometry("550x900")
        self.root.resizable(False, False)
        
        # Load Icon
        try:
            icon_path = self.get_resource_path("icon.ico")
            self.root.iconbitmap(icon_path)
        except: pass

        # Colors - Define this FIRST because tray uses it
        self.colors = {
            "bg": "#2c2f33",
            "card": "#23272a",
            "primary": "#5865F2",
            "success": "#43b581",
            "danger": "#f04747",
            "text": "#ffffff",
            "text_dim": "#b9bbbe",
            "input": "#40444b"
        }
        self.root.configure(bg=self.colors["bg"])
        
        # System Tray Prep
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.tray_icon = None
        self.setup_tray()
        
        # Flags for silent execution (No CMD windows)
        self.CREATE_NO_WINDOW = 0x08000000
        
        # Paths
        # Paths
        if hasattr(sys, '_MEIPASS'):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
            
        # Store blacklist in AppData for a cleaner user experience
        appdata_path = os.path.join(os.getenv('APPDATA'), "TRGatePro")
        if not os.path.exists(appdata_path):
            os.makedirs(appdata_path)
            
        self.blacklist_path = os.path.join(appdata_path, "custom_blacklist.txt")
        
        # Migration: Move existing blacklist from app directory if it exists
        old_local_path = os.path.join(os.path.dirname(sys.executable) if hasattr(sys, '_MEIPASS') else self.base_path, "custom_blacklist.txt")
        if os.path.exists(old_local_path) and not os.path.exists(self.blacklist_path):
            try:
                import shutil
                shutil.move(old_local_path, self.blacklist_path)
            except: pass
        
        # Ensure initial blacklist exists if not found
        if not os.path.exists(self.blacklist_path):
            initial_domains = [
                "discord.com", "discord.gg", "discordapp.com", "discordapp.net", 
                "gateway.discord.gg", "cdn.discordapp.com", "media.discordapp.net",
                "images.discordapp.net", "discordstatus.com", "discord.media",
                "dis.gd", "discord.co", "discord.design", "discord.dev", 
                "discord.gift", "discord.new", "discord.store", "discord.tools",
                "remote-auth-gateway.discord.gg", "latency.discord.media"
            ]
            with open(self.blacklist_path, "w", encoding="utf-8") as f:
                f.write("\n".join(initial_domains))

        self.setup_styles()
        self.create_widgets()
        
        self.check_initial_status()
        
        # Background monitor thread
        self.stop_monitor = False
        self.monitor_thread = threading.Thread(target=self.status_monitor, daemon=True)
        self.monitor_thread.start()
        
        # Initial Autostart check
        self.update_autostart_checkbox()

        # Handle start minimized
        if "--minimized" in sys.argv:
            self.root.withdraw()

    def get_resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Card.TFrame", background=self.colors["card"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 10))

    def create_widgets(self):
        # Header Card
        header_card = ttk.Frame(self.root, style="Card.TFrame", padding=20)
        header_card.pack(fill="x", padx=0, pady=0)
        
        # Logo in UI
        try:
            logo_path = self.get_resource_path("logo.png")
            self.logo_img = tk.PhotoImage(file=logo_path).subsample(4, 4) # Adjust size
            tk.Label(header_card, image=self.logo_img, bg=self.colors["card"]).pack(pady=(0, 10))
        except: pass

        tk.Label(header_card, text="TR-GATE PRO", fg=self.colors["primary"], bg=self.colors["card"], font=("Segoe UI Black", 24)).pack()
        self.status_label = tk.Label(header_card, text="STATUS: INACTIVE", fg=self.colors["danger"], bg=self.colors["card"], font=("Segoe UI Bold", 12))
        self.status_label.pack(pady=5)
        
        # Controls Section
        control_frame = ttk.Frame(self.root, style="TFrame", padding=15)
        control_frame.pack(fill="x")
        
        self.btn_start = tk.Button(control_frame, text="START SYSTEM", command=self.start_tunnel, bg=self.colors["success"], fg="white", font=("Segoe UI Bold", 11), relief="flat", height=2)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=5)
        
        self.btn_stop = tk.Button(control_frame, text="STOP SYSTEM", command=self.stop_tunnel, bg=self.colors["danger"], fg="white", font=("Segoe UI Bold", 11), relief="flat", height=2)
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=5)
        
        # Domain Manager Section
        tk.Label(self.root, text="DOMAIN MANAGER (BLACKLIST)", fg=self.colors["text_dim"], bg=self.colors["bg"], font=("Segoe UI Bold", 10)).pack(pady=(10, 0))
        
        self.domain_list = tk.Listbox(self.root, bg=self.colors["input"], fg="white", borderwidth=0, highlightthickness=0, font=("Segoe UI", 10), selectbackground=self.colors["primary"])
        self.domain_list.pack(fill="both", expand=True, padx=20, pady=10)
        
        domain_controls = ttk.Frame(self.root, style="TFrame", padding=10)
        domain_controls.pack(fill="x")
        
        tk.Button(domain_controls, text="+ ADD SITE", command=self.add_domain, bg=self.colors["primary"], fg="white", font=("Segoe UI Bold", 9), relief="flat").pack(side="left", padx=10, fill="x", expand=True)
        tk.Button(domain_controls, text="- REMOVE SELECTED", command=self.remove_domain, bg="#4f545c", fg="white", font=("Segoe UI Bold", 9), relief="flat").pack(side="right", padx=10, fill="x", expand=True)
        
        self.load_domains()

        # Settings Section
        settings_frame = ttk.Frame(self.root, style="TFrame", padding=15)
        settings_frame.pack(fill="x")
        
        self.autostart_var = tk.BooleanVar()
        self.check_autostart = tk.Checkbutton(
            settings_frame, 
            text="Start with Windows (System Boot)", 
            variable=self.autostart_var,
            command=self.toggle_autostart,
            bg=self.colors["bg"],
            fg=self.colors["text"],
            selectcolor=self.colors["card"],
            activebackground=self.colors["bg"],
            activeforeground=self.colors["primary"],
            font=("Segoe UI", 10)
        )
        self.check_autostart.pack(side="left", padx=10)

        # Footer
        tk.Label(self.root, text="Silent Mode Enabled | No Popups", fg="#4f545c", bg=self.colors["bg"], font=("Segoe UI", 8)).pack(side="bottom", pady=10)

    def load_domains(self):
        self.domain_list.delete(0, tk.END)
        if os.path.exists(self.blacklist_path):
            with open(self.blacklist_path, "r") as f:
                for line in f:
                    domain = line.strip()
                    if domain:
                        self.domain_list.insert(tk.END, domain)

    def add_domain(self):
        domain = simpledialog.askstring("Add Site", "Enter domain name (e.g., example.com):")
        if domain:
            with open(self.blacklist_path, "a") as f:
                f.write(f"\n{domain}")
            self.load_domains()
            messagebox.showinfo("Success", f"{domain} added to list. Restart tunnel if it's already running.")

    def remove_domain(self):
        selection = self.domain_list.curselection()
        if selection:
            domain = self.domain_list.get(selection)
            with open(self.blacklist_path, "r") as f:
                lines = f.readlines()
            with open(self.blacklist_path, "w") as f:
                for line in lines:
                    if line.strip() != domain:
                        f.write(line)
            self.load_domains()
            messagebox.showinfo("Success", f"{domain} removed.")

    def is_admin(self):
        try: return ctypes.windll.shell32.IsUserAnAdmin()
        except: return False

    def get_arch(self):
        if os.environ.get('PROCESSOR_ARCHITECTURE') == 'AMD64' or os.environ.get('PROCESSOR_ARCHITEW6432'):
            return "x86_64"
        return "x86"

    def silent_run(self, cmd_list):
        return subprocess.run(cmd_list, capture_output=True, text=True, creationflags=self.CREATE_NO_WINDOW)

    def start_tunnel(self):
        if not self.is_admin(): return
        self.btn_start.config(state="disabled", text="STARTING...")
        threading.Thread(target=self._run_start, daemon=True).start()

    def _run_start(self):
        try:
            arch = self.get_arch()
            exe_path = os.path.join(self.base_path, arch, "goodbyedpi.exe")
            
            # Stop first silently
            self.silent_run(["sc", "stop", "TRGatePro"])
            self.silent_run(["sc", "delete", "TRGatePro"])
            
            # Cleanup and DNS Flush
            self.silent_run(["sc", "stop", "TRGatePro"])
            self.silent_run(["sc", "delete", "TRGatePro"])
            self.silent_run(["ipconfig", "/flushdns"])
            time.sleep(1) # Wait for deletion to take effect
            
            # Correctly escape quotes for sc create binPath
            # The entire binPath value must be in quotes, and internal quotes must be escaped with \"
            escaped_exe = exe_path.replace('"', '\\"')
            escaped_blacklist = self.blacklist_path.replace('"', '\\"')
            
            # Use -5 --set-ttl 5 for Turkey, ensuring --blacklist is correctly used
            service_cmd = f'\\"{escaped_exe}\\" -5 --set-ttl 5 --blacklist \\"{escaped_blacklist}\\" --dns-addr 77.88.8.8 --dns-port 1253 --dnsv6-addr 2a02:6b8::feed:0ff --dnsv6-port 1253'
            
            # Create command with space after binPath=
            create_cmd = f'sc create TRGatePro binPath= "{service_cmd}" start= auto'
            
            # Execute and notify
            subprocess.run(create_cmd, shell=True, creationflags=self.CREATE_NO_WINDOW)
            subprocess.run("sc description TRGatePro \"TR-Gate Pro Tunnel Bypass System\"", shell=True, creationflags=self.CREATE_NO_WINDOW)
            subprocess.run("sc start TRGatePro", shell=True, creationflags=self.CREATE_NO_WINDOW)
            
            time.sleep(2) # Give it a bit more time to start
            self.root.after(0, lambda: self.btn_start.config(state="normal", text="START SYSTEM"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("System Error", str(e)))

    def stop_tunnel(self):
        if not self.is_admin(): return
        self.btn_stop.config(state="disabled", text="STOPPING...")
        threading.Thread(target=self._run_stop, daemon=True).start()

    def _run_stop(self):
        try:
            # Stop and delete the main service
            self.silent_run(["sc", "stop", "TRGatePro"])
            self.silent_run(["sc", "delete", "TRGatePro"])
            # Clean up WinDivert drivers just in case they are stuck
            self.silent_run(["sc", "stop", "WinDivert"])
            self.silent_run(["sc", "delete", "WinDivert"])
            self.silent_run(["sc", "stop", "WinDivert14"])
            self.silent_run(["sc", "delete", "WinDivert14"])
            # Kill any lingering process
            self.silent_run(["taskkill", "/F", "/IM", "goodbyedpi.exe", "/T"])
            
            time.sleep(1)
            self.root.after(0, lambda: self.btn_stop.config(state="normal", text="STOP SYSTEM"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("System Error", str(e)))

    def status_monitor(self):
        while not self.stop_monitor:
            try:
                result = self.silent_run(["sc", "query", "TRGatePro"])
                if "RUNNING" in result.stdout:
                    self.root.after(0, lambda: self.status_label.config(text="STATUS: ACTIVE", fg=self.colors["success"]))
                else:
                    self.root.after(0, lambda: self.status_label.config(text="STATUS: INACTIVE", fg=self.colors["danger"]))
            except:
                self.root.after(0, lambda: self.status_label.config(text="STATUS: INACTIVE", fg=self.colors["danger"]))
            time.sleep(2)

    def check_initial_status(self): pass

    # --- New Features: Tray & Autostart ---

    def hide_window(self):
        self.root.withdraw()
        # Ensure tray icon is running
        if self.tray_icon is None:
            self.setup_tray()

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def setup_tray(self):
        if self.tray_icon: return
        try:
            # Create a simple icon image
            width = 64
            height = 64
            color1 = self.colors["primary"]
            image = Image.new('RGB', (width, height), self.colors["bg"])
            dc = ImageDraw.Draw(image)
            dc.ellipse([8, 8, 56, 56], fill=color1)
            dc.ellipse([20, 20, 44, 44], fill=self.colors["success"]) # Small secondary indicator
            
            menu = pystray.Menu(
                pystray.MenuItem("Open TR-Gate Pro", self.show_window),
                pystray.MenuItem("Exit Completely", self.quit_app)
            )
            
            self.tray_icon = pystray.Icon("TRGatePro", image, "TR-Gate Pro", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except: pass

    def quit_app(self, icon=None, item=None):
        self.stop_monitor = True
        
        # Ensure services are stopped BEFORE closing
        try:
            # Stop and delete the main service
            self.silent_run(["sc", "stop", "TRGatePro"])
            self.silent_run(["sc", "delete", "TRGatePro"])
            # Clean up WinDivert drivers
            self.silent_run(["sc", "stop", "WinDivert"])
            self.silent_run(["sc", "delete", "WinDivert"])
            self.silent_run(["sc", "stop", "WinDivert14"])
            self.silent_run(["sc", "delete", "WinDivert14"])
            # Force kill the driver/exe process just in case
            self.silent_run(["taskkill", "/F", "/IM", "goodbyedpi.exe", "/T"])
        except:
            pass

        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        # Give a small moment for cleanup
        time.sleep(0.5)
        os._exit(0) # Force exit to ensure no threads hang

    def update_autostart_checkbox(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "TRGatePro")
            winreg.CloseKey(key)
            self.autostart_var.set(True)
        except WindowsError:
            self.autostart_var.set(False)

    def toggle_autostart(self):
        app_path = f'"{sys.executable}" --minimized'
        if not hasattr(sys, '_MEIPASS'):
            # If running as script, we need to point to python and the script
            app_path = f'"{sys.executable}" "{os.path.abspath(__file__)}" --minimized'
            
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            if self.autostart_var.get():
                winreg.SetValueEx(key, "TRGatePro", 0, winreg.REG_SZ, app_path)
                messagebox.showinfo("Autostart", "Application will now start with Windows.")
            else:
                try:
                    winreg.DeleteValue(key, "TRGatePro")
                    messagebox.showinfo("Autostart", "Autostart disabled.")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            messagebox.showerror("Error", f"Could not update registry: {e}")
            self.update_autostart_checkbox() # Revert checkbox

if __name__ == "__main__":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    
    root = tk.Tk()
    app = DiscordTunnelApp(root)
    root.mainloop()
