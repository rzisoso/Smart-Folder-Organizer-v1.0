# Smart Folder Organizer

A cross-platform desktop application that automatically organizes files into categorized subfolders, preserving your original directory structure.

![Smart Folder Organizer Pro Demo](SmartFolderOrganizer.gif)

---

`Smart Folder Organizer` is a desktop utility designed to automatically tidy up any directory. It intelligently sorts files (like images, documents, and archives) into categorized subfolders based on customizable rules.

Stop wasting time manually cleaning your "Downloads" or "Projects" folder—this tool does it for you with one click, while **respecting and preserving your original folder structure.**

## Key Features

* ** Intuitive GUI:** A clean and simple graphical interface built with Python's native Tkinter library.
* ** Cross-Platform:** Packaged to run as a standalone native app on both **Windows (`.exe`)** and **macOS (`.app`)**.
* ** Structure-Preserving Logic:** When organizing recursively, it creates category folders *inside* each subfolder (e.g., `Project/Notes/Images/`), keeping your original structure intact.
* ** Fully Customizable:** Easily edit the `config.json` file to add new file types or create your own categories (e.g., "Ebooks", "Fonts").
* ** One-Click Config:** A built-in **"Open Config Folder"** button instantly opens the correct system folder for you to edit the `config.json` file.
* ** Recursive Organizing:** Optionally clean up files in all subfolders, not just the top level.
* ** Activity Logging:** A real-time log in the app shows you exactly what's being moved, and a persistent `organizer.log` file is saved for troubleshooting.

## Tech Stack

* **Python 3**
* **Tkinter** (for the GUI)
* **PyInstaller** (for packaging into `.exe` and `.app`)
* **Standard Libraries:** `os`, `shutil`, `json`, `logging`, `platform`, `subprocess`

## How to Use (For End-Users)

This application is delivered as a standalone executable. No installation is needed.

1.  Download the latest release (`SmartOrganizerPro.exe` for Windows or `SmartOrganizerPro.app` for macOS) from the [Releases Page](https://github.com/rzisoso/Smart-Folder-Organizer-Mac/releases/tag/v1.0).
2.  (macOS Only) The first time you run it, you may need to **right-click the app icon and select "Open"** from the menu to bypass the security warning.
3.  On first launch, the app automatically creates a default `config.json` file in your system's user configuration directory.
4.  Click **"Browse..."** to select the folder you want to organize.
5.  Check **"Organize Subfolders (Recursive)"** if you want it to also clean up all folders *inside* the one you selected.
6.  Click **"Start Organizing"**.

#### How to Customize Categories:

1.  In the app, click the **"Open Config Folder"** button.
2.  Your file explorer will open to the correct location.
3.  Open `config.json` with any text editor (like Notepad or TextEdit).
4.  Add or remove file extensions (e.g., add `".webp"` to the "Images" list).
5.  Save the `config.json` file and **restart the application** for your changes to take effect.
