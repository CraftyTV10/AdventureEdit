import os, sys, struct, re, tkinter as tk
from tkinter import filedialog, messagebox, ttk

class RRLevelEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Reflex-Bergkamm Level Editor Alpha v1.2")
        self.root.geometry("1250x750")
        self.root.configure(bg="#2c3e50")
        self.file_path, self.raw_data, self.found_objects, self.selected_idx = None, None, [], None
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.root, text="Kinect Adventures! Reflex-Bergkamm Level Editor Alpha v1.2", font=("Arial", 16, "bold"), fg="#ecf0f1", bg="#34495e", pady=10).pack(fill=tk.X)
        file_frame = tk.Frame(self.root, bg="#2c3e50", pady=10)
        file_frame.pack(fill=tk.X)
        tk.Button(file_frame, text="Datei öffnen", font=("Arial", 11), bg="#3498db", fg="white", command=self.load_file).pack(side=tk.LEFT, padx=10)
        self.lbl_file = tk.Label(file_frame, text="Keine Datei geladen", font=("Arial", 10, "italic"), fg="#bdc3c7", bg="#2c3e50")
        self.lbl_file.pack(side=tk.LEFT, padx=5)
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        list_frame = tk.Frame(main_frame, bg="#2c3e50")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(list_frame, text="Level-Bausteine & Gameplay-Objekte:", font=("Arial", 11, "bold"), fg="#ecf0f1", bg="#2c3e50").pack(anchor=tk.W, pady=5)
        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#34495e", fieldbackground="#34495e", foreground="white")
        style.map("Treeview", background=[("selected", "#2980b9")])
        self.obj_tree = ttk.Treeview(list_frame, columns=("Type", "Info"), show="tree headings", yscrollcommand=scroll.set)
        self.obj_tree.heading("#0", text="Objekt-Name"); self.obj_tree.heading("Type", text="Typ"); self.obj_tree.heading("Info", text="Details")
        self.obj_tree.pack(fill=tk.BOTH, expand=True); self.obj_tree.bind("<<TreeviewSelect>>", self.on_object_select); scroll.config(command=self.obj_tree.yview)
        
        self.canvas_frame = tk.LabelFrame(main_frame, text=" Visueller Schienen-Pfad (X/Y-Draufsicht) ", font=("Arial", 11, "bold"), fg="#ecf0f1", bg="#2c3e50", padx=5, pady=5)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.canvas = tk.Canvas(self.canvas_frame, bg="#111111", highlightthickness=1, highlightbackground="#555")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.ef = tk.LabelFrame(main_frame, text=" Eigenschaften & Steuerung ", font=("Arial", 11, "bold"), fg="#ecf0f1", bg="#34495e", padx=10, pady=10)
        self.ef.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        self.lbl_p = tk.Label(self.ef, text="Wähle links ein Objekt aus.", font=("Arial", 11), fg="#bdc3c7", bg="#34495e")
        self.lbl_p.pack(pady=150)
        
        self.btn_save = tk.Button(self.root, text="Modifiziertes Level (.xxx) speichern", font=("Arial", 12, "bold"), bg="#2ecc71", fg="white", state=tk.DISABLED, command=self.save_file)
        self.btn_save.pack(fill=tk.X, padx=10, pady=10)

        self.menu_bar = tk.Menu(self.root)
        
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Load Level (.xxx)", command=self.load_file)
        file_menu.add_command(label="Save Level (.xxx)", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Level Settings (Timer & Medals)", command=self.open_settings)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        self.root.config(menu=self.menu_bar)








    def load_file(self):
        p = filedialog.askopenfilename(filetypes=[("Unreal Package", "*.xxx"), ("Alle Dateien", "*.*")])
        if not p: return  # HIER WAR DER FIX!
        self.file_path = p; self.lbl_file.config(text=os.path.basename(p))
        with open(p, "rb") as f_in: self.raw_data = bytearray(f_in.read())
        self.scan_level_data()
        self.btn_save.config(state=tk.NORMAL)
        self.draw_visual_path()

    def scan_level_data(self):
        for item in self.obj_tree.get_children(): self.obj_tree.delete(item)
        self.found_objects = []
        kw = [b"obs_", b"whs_", b"gplay", b"track", b"plyr", b"platform", b"score", b"medal", b"timer", b"gold", b"silver", b"bronze", b"barrier", b"hurdle", b"checkpoint", b"cubesoft"]
        for m in re.finditer(b'[a-zA-Z0-9_]{4,64}', self.raw_data):
            st, en = m.start(), m.end(); b = self.raw_data[st:en]
            if any(k in b.lower() for k in kw):
                n = b.decode('ascii', errors='ignore')
                if "ui_" in n.lower() or "img_" in n.lower(): continue
                off = en + 4; is_v = False; c = (0.0, 0.0, 0.0)
                
                for scan_offset in range(en, min(en + 64, len(self.raw_data) - 12)):
                    try:
                        x, y, z = struct.unpack("<fff", self.raw_data[scan_offset:scan_offset+12])
                        if -1000000.0 < x < 100000.0 and -1000000.0 < y < 1000000.0 and -1000000.0 < z < 1000000.0 and (x != 0.0 or y != 0.0 or z != 0.0):
                            is_v, c, off = True, (x, y, z), scan_offset
                            break
                    except: pass
                
                if not is_v and any(x in n.lower() for x in ["track", "barrier", "hurdle", "checkpoint", "cubesoft"]):
                    is_v = True
                
                t = "Schiene" if "track" in n.lower() else ("Barriere" if any(x in n.lower() for x in ["barrier", "hurdle", "checkpoint", "cubesoft"]) else "Deko / Logik")
                inf = f"X: {c[0]:.1f}, Z: {c[2]:.1f}" if is_v else "Wert-Eigenschaft"
                
                self.found_objects.append({"name": n, "type": t, "offset": off, "is_vector": is_v, "coords": c, "start": st})
                node_id = f"row_{len(self.found_objects)-1}"
                self.obj_tree.insert("", tk.END, iid=node_id, text=n, values=(t, inf))

    def draw_visual_path(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width() if self.canvas.winfo_width() > 1 else 300
        h = self.canvas.winfo_height() if self.canvas.winfo_height() > 1 else 400
        self.canvas.create_line(w/2-20, h/2, w/2+20, h/2, fill="#2ecc71", width=1)
        self.canvas.create_line(w/2, h/2-20, w/2, h/2+20, fill="#2ecc71", width=1)
        self.canvas.create_oval(w/2-10, h/2-10, w/2+10, h/2+10, outline="#2ecc71", width=1)
        
        track_pts = []
        for o in self.found_objects:
            if o["is_vector"] and o["coords"] != (0.0, 0.0, 0.0):
                if "track" in o["name"].lower() or "schiene" in o["type"].lower():
                    track_pts.append(((w / 2) + (o["coords"][0] * 0.001), (h / 2) - (o["coords"][1] * 0.001)))
                
        for i in range(len(track_pts) - 1):
            self.canvas.create_line(track_pts[i], track_pts[i+1], fill="#e67e22", width=2)
            
        for o in self.found_objects:
            if o["is_vector"]:
                sx = (w / 2) + (o["coords"][0] * 0.001)
                sy = (h / 2) - (o["coords"][1] * 0.001)
                is_track = "track" in o["name"].lower() or "schiene" in o["type"].lower()
                if self.selected_idx is not None and self.found_objects[self.selected_idx]["name"] == o["name"]: col, sz = "#00ff00", 7
                elif is_track: col, sz = "#3498db", 4
                else: col, sz = "#ff0000", 5
                self.canvas.create_oval(sx-sz, sy-sz, sx+sz, sy+sz, fill=col, outline="white", width=1)

    def on_object_select(self, event):
        items = self.obj_tree.selection()
        if not items: return
        obj_idx = self.obj_tree.index(items)
        self.selected_idx = obj_idx
        obj = self.found_objects[obj_idx]
        self.draw_visual_path()
        for widget in self.ef.winfo_children(): widget.destroy()
        
        g_frame = tk.Frame(self.ef, bg="#34495e")
        g_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(g_frame, text="MASTER STEUERUNG", font=("Arial", 12, "bold"), fg="#2ecc71", bg="#34495e").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        tk.Label(g_frame, text=f"Typ: {obj['type']}", font=("Arial", 10, "italic"), fg="#bdc3c7", bg="#34495e").grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
        tk.Label(g_frame, text=f"Modell ersetzen (Max. {len(obj['name'])} Chars):", fg="white", bg="#34495e").grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10,0))
        self.en = tk.Entry(g_frame, font=("Arial", 11)); self.en.insert(0, obj["name"]); self.en.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=2)
        tk.Button(g_frame, text="Namen im Hex-Code swappen", bg="#e67e22", fg="white", font=("Arial", 9, "bold"), command=lambda: self.apply_name(obj_idx)).grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=(0,10))
        
        tk.Frame(g_frame, height=2, bd=1, relief=tk.SUNKEN, bg="#555").grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        z_text = "Z (Schanzen-Höhe):" if "track" in obj["name"].lower() else "Z (Hürden-Höhe):"
        tk.Label(g_frame, text="3D-POSITION TUNEN:", font=("Arial", 10, "bold"), fg="#3498db", bg="#34495e").grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        tk.Label(g_frame, text="X (Links/Rechts):", fg="white", bg="#34495e").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.ex = tk.Entry(g_frame, font=("Arial", 11)); self.ex.insert(0, f"{obj['coords'][0]:.2f}"); self.ex.grid(row=7, column=1, sticky=tk.EW, padx=5, pady=2)
        tk.Label(g_frame, text="Y (Vorwärts):", fg="white", bg="#34495e").grid(row=8, column=0, sticky=tk.W, pady=2)
        self.ey = tk.Entry(g_frame, font=("Arial", 11)); self.ey.insert(0, f"{obj['coords'][1]:.2f}"); self.ey.grid(row=8, column=1, sticky=tk.EW, padx=5, pady=2)
        tk.Label(g_frame, text=z_text, fg="white", bg="#34495e").grid(row=9, column=0, sticky=tk.W, pady=2)
        self.ez = tk.Entry(g_frame, font=("Arial", 11)); self.ez.insert(0, f"{obj['coords'][2]:.2f}"); self.ez.grid(row=9, column=1, sticky=tk.EW, padx=5, pady=2)
        tk.Button(g_frame, text="Neue Koordinaten injizieren", bg="#3498db", fg="white", font=("Arial", 10, "bold"), command=lambda: self.apply_coords(obj_idx)).grid(row=10, column=0, columnspan=2, sticky=tk.EW, pady=15)
        
    def apply_coords(self, idx):
        obj = self.found_objects[idx]
        try:
            nx, ny, nz = float(self.ex.get()), float(self.ey.get()), float(self.ez.get())
            self.raw_data[obj["offset"]:obj["offset"]+12] = struct.pack("<fff", nx, ny, nz)
            self.found_objects[idx]["coords"] = (nx, ny, nz)
            messagebox.showinfo("Übernommen", "Werte modifiziert!")
            self.scan_level_data()
            self.draw_visual_path()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler: {e}")

    def apply_name(self, idx):
        obj = self.found_objects[idx]
        nn = self.en.get().strip()
        if len(nn) > len(obj["name"]):
            return
        self.raw_data[obj["start"]:obj["start"]+len(obj["name"])] = nn.encode('ascii').ljust(len(obj["name"]), b'\x00')
        messagebox.showinfo("Übernommen", "Name überschrieben!")
        self.scan_level_data()
        self.draw_visual_path()

    def save_file(self):
        p = filedialog.asksaveasfilename(defaultextension=".xxx", filetypes=[("Unreal Package", "*.xxx")])
        if not p:
            return
        self.raw_data[0:4] = b'\x00\x00\x00\x00'
        with open(p, "wb") as f:
            f.write(self.raw_data)
        messagebox.showinfo("Erfolg", "Level gespeichert!")


    def open_settings(self):
        messagebox.showinfo("Level Settings", "Diese Funktion ist noch nicht implementiert.")

if __name__ == "__main__":
    root = tk.Tk()
    icon = tk.PhotoImage(file=r"icon.png")
    root.iconphoto(False, icon)
    app = RRLevelEditor(root)
    root.mainloop()