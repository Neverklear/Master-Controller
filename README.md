# MasterControl — Grant Full Control (Windows GUI Tool)

**MasterControl** is a Python-based Windows GUI utility for quickly and recursively granting **Full Control** file permissions to:
- The **current user**
- **Everyone** (or the SID `S-1-1-0` for localized systems)

It uses built-in Windows tools (`icacls` and optionally `takeown`) and runs with **Administrator privileges**.

---

## ✨ Features

- **Administrator elevation** — Self-elevates if not already running as admin.
- **Recursive permissions** — Applies to all files and subfolders.
- **Target selection** — Choose the folder you want to modify.
- **Ownership** — Optional "Take ownership first" mode.
- **Inheritance** — Option to enable ACL inheritance on the root folder.
- **Localization support** — Use the `Everyone` SID for non-English Windows installations.
- **Selective scope** — Apply changes to:
  - Folder contents only
  - The folder **and** its contents
- **Live log output** — Displays every command executed and its results.

---

## 📦 Requirements

- **Operating System**: Windows 10, Windows 11, or Windows Server (with GUI)
- **Python**: Version **3.8 or newer**
- **Built-in Windows utilities**: `icacls` and `takeown` (included in Windows)
- **Python packages**:  
  This script uses only **standard library modules**, so there are **no external Python packages** required.  
  To ensure your Python environment is up-to-date:
  ```bash
  python -m pip install --upgrade pip
  ```

---

## 🚀 Installation

1. **Clone the repository** or download the `.py` file:

   ```bash
   git clone https://github.com/yourusername/MasterControl.git
   cd MasterControl
   ```

2. Ensure Python is installed:

   ```bash
   python --version
   ```

3. (Optional) Upgrade `pip`:

   ```bash
   python -m pip install --upgrade pip
   ```

---

## 🖥 Usage

If not run as admin, the tool will automatically re-launch with elevated privileges.

1. **Run the script**:
   ```bash
   python MasterControl.py
   ```

2. **Select the target folder** in the GUI.

3. **Choose your options**:
   - ✅ **Take ownership first** — Runs `takeown` before modifying ACLs.
   - ✅ **Enable inheritance on root** — Ensures ACL inheritance is enabled.
   - ✅ **Include root folder itself** — Modifies the folder’s ACL as well as its contents.
   - ✅ **Use Everyone SID** — Uses `S-1-1-0` for compatibility with non-English Windows.

4. **Click** `Grant Full Control Recursively`.

5. **Watch the live log** for progress and results.

---

## ⚠ Warnings

- **This will permanently modify ACLs** on all selected files and subfolders.
- Granting **Everyone: Full Control** is **not secure** in most environments.  
  Use with caution, especially on shared or networked drives.
- The tool modifies permissions **in place** — there’s **no undo**.  
  To revert, you will need to manually adjust permissions using Windows security settings.
- Some files/folders may still be inaccessible if they have special system protection.

---

## 📜 License

This project is released under the [MIT License](LICENSE).

