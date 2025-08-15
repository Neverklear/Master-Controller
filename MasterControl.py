#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MasterControl - Grant Full Control (GUI) for Windows
- Elevates to admin automatically
- Recursively grants Full Control to current user + Everyone (or Everyone SID)
- Works IN PLACE (modifies ACLs only; no files written anywhere)
"""

import os
import sys
import threading
import subprocess
import ctypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

APP_TITLE = "MasterControl — Grant Full Control"
APP_WIDTH = 780
APP_HEIGHT = 560

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def relaunch_as_admin():
    # Relaunch current script with elevation
    params = " ".join([f'"{arg}"' for arg in sys.argv])
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    except Exception as e:
        messagebox.showerror("Elevation failed", f"Could not request administrator privileges.\n\n{e}")
    sys.exit(0)

def whoami():
    try:
        out = subprocess.check_output(["whoami"], text=True, stderr=subprocess.STDOUT).strip()
        return out  # DOMAIN\Username
    except Exception:
        dom = os.environ.get("USERDOMAIN", "")
        usr = os.environ.get("USERNAME", "")
        if dom and usr:
            return f"{dom}\\{usr}"
        return os.environ.get("USERNAME", "UnknownUser")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(680, 480)

        self.selected_path = tk.StringVar(value="")
        self.take_ownership = tk.BooleanVar(value=False)
        self.enable_inheritance = tk.BooleanVar(value=True)
        self.include_root_folder = tk.BooleanVar(value=False)  # default = contents only
        self.use_everyone_sid = tk.BooleanVar(value=False)     # use S-1-1-0 instead of localized "Everyone"

        self._build_ui()

    def _build_ui(self):
        pad = 10

        # Folder picker
        pick_frame = ttk.LabelFrame(self, text="Target folder")
        pick_frame.pack(fill="x", padx=pad, pady=(pad, 6))
        entry = ttk.Entry(pick_frame, textvariable=self.selected_path)
        entry.pack(side="left", fill="x", expand=True, padx=(pad, 6), pady=pad)
        ttk.Button(pick_frame, text="Browse…", command=self.browse).pack(side="right", padx=pad, pady=pad)

        # Options
        opt_frame = ttk.LabelFrame(self, text="Options")
        opt_frame.pack(fill="x", padx=pad, pady=(0, 6))

        row1 = ttk.Frame(opt_frame); row1.pack(fill="x", padx=pad, pady=(8,2))
        ttk.Checkbutton(row1, text="Take ownership first (takeown)", variable=self.take_ownership).pack(side="left", padx=(0,18))
        ttk.Checkbutton(row1, text="Ensure inheritance enabled on root (/inheritance:e)", variable=self.enable_inheritance).pack(side="left")

        row2 = ttk.Frame(opt_frame); row2.pack(fill="x", padx=pad, pady=(2,8))
        ttk.Checkbutton(row2, text="Include the root folder itself (not just contents)", variable=self.include_root_folder).pack(side="left", padx=(0,18))
        ttk.Checkbutton(row2, text='Use "Everyone" SID (S-1-1-0) for localized systems', variable=self.use_everyone_sid).pack(side="left")

        # Actions
        act = ttk.Frame(self); act.pack(fill="x", padx=pad, pady=(4,6))
        self.btn_run = ttk.Button(act, text="Grant Full Control Recursively", command=self.on_run)
        self.btn_run.pack(side="left")
        self.btn_cancel = ttk.Button(act, text="Cancel", command=self.on_cancel, state="disabled")
        self.btn_cancel.pack(side="left", padx=(10,0))

        # Status + Log
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status_var, anchor="w").pack(fill="x", padx=pad)

        self.log = ScrolledText(self, wrap="word", height=20)
        self.log.pack(fill="both", expand=True, padx=pad, pady=(0, pad))
        self.log.configure(state="disabled")

        ttk.Label(self, text='This tool uses "icacls" (and optionally "takeown") to change ACLs.',
                  foreground="#666").pack(side="bottom", pady=(0, pad))

    def browse(self):
        folder = filedialog.askdirectory(title="Choose a folder")
        if folder:
            self.selected_path.set(folder)

    def append_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.update_idletasks()

    def set_busy(self, busy=True):
        if busy:
            self.btn_run.configure(state="disabled")
            self.btn_cancel.configure(state="normal")
        else:
            self.btn_run.configure(state="normal")
            self.btn_cancel.configure(state="disabled")

    def on_cancel(self):
        self._cancel_requested = True
        self.append_log("[!] Cancel requested. Will stop after current step…")
        self.status_var.set("Cancel requested…")

    def on_run(self):
        path = self.selected_path.get().strip()
        if not path:
            messagebox.showwarning("Select folder", "Please choose a target folder first.")
            return
        if not os.path.isdir(path):
            messagebox.showerror("Invalid folder", "The selected path is not a folder.")
            return

        self._cancel_requested = False
        self.set_busy(True)
        self.status_var.set("Working…")
        self.log.configure(state="normal"); self.log.delete("1.0", "end"); self.log.configure(state="disabled")

        threading.Thread(target=self._worker, args=(path,), daemon=True).start()

    def _run_cmd(self, args):
        self.append_log(f"$ {' '.join(args)}")
        try:
            proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=False)
            for line in proc.stdout:  # type: ignore[union-attr]
                self.append_log(line.rstrip("\n"))
            rc = proc.wait()
            self.append_log(f"[exit code: {rc}]")
            return rc
        except FileNotFoundError:
            self.append_log("Error: Command not found. Ensure Windows system tools are available.")
            return 127
        except Exception as e:
            self.append_log(f"Error running command: {e}")
            return 1

    def _worker(self, root_path):
        try:
            current_identity = whoami()
            self.append_log(f"Detected current user: {current_identity}")
            norm_root = os.path.normpath(root_path)
            self.append_log(f"Target root: {norm_root}")

            if self._cancel_requested:
                return self._finish("Cancelled.")

            if self.take_ownership.get():
                self.append_log("Taking ownership recursively (this may take a while)…")
                # /F target /R recursive /D Y assume Yes on prompts
                rc = self._run_cmd(["takeown", "/F", norm_root, "/R", "/D", "Y"])
                if rc != 0:
                    self.append_log("Warning: takeown returned a non-zero exit code. Proceeding…")

            if self._cancel_requested:
                return self._finish("Cancelled.")

            if self.enable_inheritance.get():
                self.append_log("Ensuring inheritance is enabled on the root…")
                rc_inh = self._run_cmd(["icacls", norm_root, "/inheritance:e"])
                if rc_inh != 0:
                    self.append_log("Warning: Could not enable inheritance on the root.")

            if self._cancel_requested:
                return self._finish("Cancelled.")

            # Build the target path pattern:
            # - Contents only: "<root>\*"
            # - Include root also: "<root>"
            apply_target = norm_root if self.include_root_folder.get() else os.path.join(norm_root, "*")
            self.append_log("Granting Full Control to current user and Everyone recursively…")

            everyone_token = "S-1-1-0" if self.use_everyone_sid.get() else "Everyone"

            icacls_args = [
                "icacls", apply_target,
                "/grant", f"{current_identity}:(F)",
                "/grant", f"{everyone_token}:(F)",
                "/T",  # traverse subfolders
                "/C"   # continue on errors
            ]

            rc = self._run_cmd(icacls_args)

            if rc == 0:
                self._finish("Done. Permissions applied.")
            else:
                self._finish(f"Completed with exit code {rc}. Check the log for details.")
        except Exception as e:
            self._finish(f"Error: {e}")

    def _finish(self, msg):
        self.status_var.set(msg)
        self.append_log(msg)
        self.set_busy(False)

def main():
    if os.name != "nt":
        messagebox.showerror(APP_TITLE, "This tool only runs on Windows.")
        return
    if not is_admin():
        relaunch_as_admin()
        return
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
