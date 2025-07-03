#!/usr/bin/env python3
# pysync_web.py — original GUI + Flask + directory‐browse endpoint

import os
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

from flask import Flask, jsonify, request, send_file

# --- Original BackupApp class, unchanged except making .run_backup public
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
        threading.Thread(target=self.run_backup).start()

    def run_backup(self):
        for src, dst in self.pairs:
            src_clean = src.rstrip("/\\")
            src_name = os.path.basename(src_clean)
            target = os.path.join(dst, src_name)
            cmd = ["robocopy", src, target, "/MIR", "/Z", "/W:1", "/R:2", "/XA:SH", "/XJ"]
            subprocess.run(cmd, shell=True)
            subprocess.run(["attrib", "-h", "-s", target], shell=True)
        messagebox.showinfo("Backup Completed", "All backups finished.")

# --- Flask web interface
app = Flask(__name__, static_folder='.', static_url_path='')

@app.route('/')
def serve_index():
    return send_file('index.html')

@app.route('/api/pairs', methods=['GET', 'POST'])
def api_pairs():
    if request.method == 'GET':
        return jsonify([{'src': s, 'dst': d} for s, d in backup_app.pairs])
    data = request.get_json() or {}
    src, dst = data.get('src'), data.get('dst')
    if not src or not dst:
        return jsonify({'error': 'src and dst required'}), 400
    backup_app.pairs.append((src, dst))
    return jsonify({'status': 'ok'})

@app.route('/api/pairs/<int:idx>', methods=['DELETE'])
def api_remove_pair(idx):
    if 0 <= idx < len(backup_app.pairs):
        backup_app.pairs.pop(idx)
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'invalid index'}), 404

@app.route('/api/backup', methods=['POST'])
def api_start_backup():
    if not backup_app.pairs:
        return jsonify({'error': 'no pairs to back up'}), 400
    threading.Thread(target=backup_app.run_backup).start()
    return jsonify({'status': 'backup started'})

# --- New: directory‐browse endpoint
@app.route('/api/browse', methods=['GET'])
def api_browse():
    # pop up a native folder chooser, return the path chosen
    chooser = tk.Tk()
    chooser.withdraw()
    path = filedialog.askdirectory(title="Select Folder")
    chooser.destroy()
    if not path:
        return jsonify({'path': None})
    return jsonify({'path': path})

def run_flask():
    app.run(host='127.0.0.1', port=5000, threaded=True)

if __name__ == '__main__':
    root = tk.Tk()
    backup_app = BackupApp(root)
    threading.Thread(target=run_flask, daemon=True).start()
    print("Web interface at http://127.0.0.1:5000")
    root.mainloop()
