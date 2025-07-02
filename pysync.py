import os
import tkinter as tk
from tkinter import filedialog, messagebox
from threading import Thread
import subprocess

class BackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Backup Utility - Multiple Pairs")

        self.pairs = []  # List of (source, destination) tuples

        # Widgets
        self.pairs_listbox = tk.Listbox(root, width=100)
        self.pairs_listbox.pack(pady=10)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        add_pair_btn = tk.Button(btn_frame, text="Add Pair", command=self.add_pair)
        add_pair_btn.grid(row=0, column=0, padx=5)

        remove_pair_btn = tk.Button(btn_frame, text="Remove Selected Pair", command=self.remove_selected_pair)
        remove_pair_btn.grid(row=0, column=1, padx=5)

        start_btn = tk.Button(root, text="Start Backup", command=self.start_backup)
        start_btn.pack(pady=10)

    def add_pair(self):
        src = filedialog.askdirectory(title="Select Source Folder")
        if not src:
            return
        dst = filedialog.askdirectory(title="Select Destination Folder")
        if not dst:
            return
        self.pairs.append((src, dst))
        self.pairs_listbox.insert(tk.END, f"{src}  ->  {dst}")

    def remove_selected_pair(self):
        sel = self.pairs_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.pairs.pop(idx)
        self.pairs_listbox.delete(idx)

    def start_backup(self):
        if not self.pairs:
            messagebox.showerror("Error", "Please add at least one source-destination pair.")
            return
        Thread(target=self.run_backup).start()

    def run_backup(self):
        for src, dst in self.pairs:
            src_clean = src.rstrip("/\\")
            src_name = os.path.basename(src_clean)
            # Mirror into a subfolder of dst, preserving name
            target = os.path.join(dst, src_name)
            cmd = ["robocopy", src, target, "/MIR", "/Z", "/W:1", "/R:2", "/XA:SH", "/XJ"]
            subprocess.run(cmd, shell=True)
            
            # Remove hidden and system attributes from destination directory
            attrib_cmd = ["attrib", "-h", "-s", target]
            subprocess.run(attrib_cmd, shell=True)
        messagebox.showinfo("Backup Completed", "All backups finished.")

if __name__ == "__main__":
    root = tk.Tk()
    app = BackupApp(root)
    root.mainloop()
