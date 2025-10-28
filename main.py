import os
import shutil
import json
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import sys
import platform  # Used to detect the operating system
import subprocess # Used to open folders on different OSes

# --- 1. Cross-platform Path and Application Settings ---

APP_NAME = "SmartOrganizerPro"

# This is the default config file content that will be created in the user config directory
DEFAULT_CONFIG_CONTENT = """
{
  "file_type_mappings": {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".tiff"],
    "Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Audio": [".mp3", ".wav", ".ogg", ".flac"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv"],
    "Scripts": [".py", ".js", ".html", ".css", ".sh", ".json"]
  }
}
"""

def get_config_dir():
    """Gets the cross-platform, user-specific configuration folder path."""
    system = platform.system()
    if system == "Windows":
        # On Windows, place it alongside the .exe
        if getattr(sys, 'frozen', False):
            # Program is running as a bundled .exe
            return os.path.dirname(sys.executable)
        else:
            # Development mode
            return os.path.dirname(os.path.abspath(__file__))
    elif system == "Darwin": # macOS
        # On macOS, use the standard Application Support directory
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', APP_NAME)
    else: # Linux
        # On Linux, use the .config directory
        return os.path.join(os.path.expanduser('~'), '.config', APP_NAME)

def get_log_dir():
    """Gets the cross-platform standard log folder path."""
    system = platform.system()
    if system == "Windows":
        # Logs are placed alongside the .exe
        return get_config_dir()
    elif system == "Darwin": # macOS
        # Use the standard Logs directory
        return os.path.join(os.path.expanduser('~'), 'Library', 'Logs', APP_NAME)
    else: # Linux
        # Use the .cache directory
        return os.path.join(os.path.expanduser('~'), '.cache', APP_NAME, 'logs')

def get_config_file_path():
    """
    Gets the full path to the configuration file.
    If the file doesn't exist, it automatically creates a default one.
    """
    config_dir = get_config_dir()
    os.makedirs(config_dir, exist_ok=True) # Ensure the directory exists
    config_path = os.path.join(config_dir, 'config.json')

    if not os.path.exists(config_path):
        # If config.json doesn't exist, create a default one
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(DEFAULT_CONFIG_CONTENT)
        except Exception as e:
            # Use print() here, as logging might not be initialized yet
            print(f"Failed to create default config file: {e}")
            return None
    
    return config_path

# --- 2. Logging Setup ---

# Ensure log directory exists
log_dir = get_log_dir()
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, 'organizer.log')

# Configure logging
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# --- 3. Load Configuration from JSON File ---

def load_config():
    """Loads file type mapping configuration from the user's config folder."""
    config_file_path = get_config_file_path()
    if not config_file_path:
        logging.error("Config file path could not be determined.")
        return None

    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            mappings = config.get("file_type_mappings", {})
            for category, extensions in mappings.items():
                mappings[category] = [ext.lower() for ext in extensions]
            return mappings
    except FileNotFoundError:
        logging.error(f"Configuration file '{config_file_path}' not found (this shouldn't happen).")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error decoding config file '{config_file_path}'. Please check its format.")
        return None
    except Exception as e:
        logging.error(f"Unknown error loading config: {e}")
        return None

# --- 4. Core Organization Logic ---
def organize_folder(folder_path, file_mappings, recursive, update_log_widget):
    """
    The core function that organizes the folder.

    :param folder_path: The path of the folder to organize.
    :param file_mappings: A dictionary of file type mappings.
    :param recursive: A boolean indicating whether to organize subfolders.
    :param update_log_widget: A function to update the GUI's log widget.
    """
    if not folder_path or not os.path.isdir(folder_path):
        message = f"Error: The path '{folder_path}' is invalid or not a directory."
        logging.error(message)
        update_log_widget(message + "\n")
        return None

    summary_report = {category: 0 for category in file_mappings}
    summary_report['Others'] = 0
    total_files_processed = 0

    # Choose the traversal method based on the 'recursive' flag
    if recursive:
        # os.walk recursively traverses all subdirectories and files
        for root, dirs, files in os.walk(folder_path):
            # Exclude the category folders we create to avoid infinite loops
            dirs[:] = [d for d in dirs if d not in file_mappings.keys() and d != 'Others']
            
            for filename in files:
                process_file(root, filename, file_mappings, summary_report, update_log_widget)
                total_files_processed += 1
    else:
        # os.listdir only traverses the top-level directory
        for item_name in os.listdir(folder_path):
            source_path = os.path.join(folder_path, item_name)
            if os.path.isfile(source_path):
                process_file(folder_path, item_name, file_mappings, summary_report, update_log_widget)
                total_files_processed += 1
    
    return summary_report, total_files_processed

def process_file(current_folder, filename, file_mappings, summary_report, update_log_widget):
    """Handles the moving logic for a single file."""
    source_path = os.path.join(current_folder, filename)
    file_extension = os.path.splitext(filename)[1].lower()
    
    moved = False
    for category, extensions in file_mappings.items():
        if file_extension in extensions:
            # All destination folders are created in the current directory
            dest_folder = os.path.join(current_folder, category)
            os.makedirs(dest_folder, exist_ok=True)
            
            try:
                # Check if a file with the same name already exists in the destination
                if not os.path.exists(os.path.join(dest_folder, filename)):
                    shutil.move(source_path, dest_folder)
                    message = f"Moved: {filename} -> {category}/"
                    logging.info(message)
                    update_log_widget(message + "\n")
                    summary_report[category] += 1
                else:
                    message = f"Skipped (exists): {filename} in {category}/"
                    logging.warning(message)
                    update_log_widget(message + "\n")
                moved = True
                break
            except Exception as e:
                message = f"Error moving {filename}: {e}"
                logging.error(message)
                update_log_widget(message + "\n")
                moved = True # Mark as handled to avoid moving to 'Others'
                break
    
    if not moved:
        dest_folder = os.path.join(current_folder, 'Others')
        os.makedirs(dest_folder, exist_ok=True)
        try:
            if not os.path.exists(os.path.join(dest_folder, filename)):
                shutil.move(source_path, dest_folder)
                message = f"Moved: {filename} -> Others/"
                logging.info(message)
                update_log_widget(message + "\n")
                summary_report['Others'] += 1
            else:
                message = f"Skipped (exists): {filename} in Others/"
                logging.warning(message)
                update_log_widget(message + "\n")
        except Exception as e:
            message = f"Error moving {filename} to 'Others': {e}"
            logging.error(message)
            update_log_widget(message + "\n")

# --- 5. GUI Interface ---
class OrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Folder Organizer Pro")
        self.root.geometry("650x450")

        # Frame for folder selection
        top_frame = tk.Frame(root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)

        tk.Label(top_frame, text="Target Folder:").pack(side=tk.LEFT, padx=(0, 5))
        self.folder_path_var = tk.StringVar()
        tk.Entry(top_frame, textvariable=self.folder_path_var, width=50).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(top_frame, text="Browse...", command=self.browse_folder).pack(side=tk.RIGHT, padx=(5, 0))

        # Frame for options and actions
        action_frame = tk.Frame(root, padx=10, pady=5)
        action_frame.pack(fill=tk.X)
        
        self.recursive_var = tk.BooleanVar()
        tk.Checkbutton(action_frame, text="Organize Subfolders (Recursive)", variable=self.recursive_var).pack(side=tk.LEFT)
        
        # --- New Feature Buttons ---
        tk.Button(action_frame, text="Open Config Folder", command=self.open_config_folder).pack(side=tk.LEFT, padx=10)
        
        tk.Button(action_frame, text="Start Organizing", command=self.start_organization, bg="lightblue", font=('Helvetica', 10, 'bold')).pack(side=tk.RIGHT, padx=10)

        # ScrolledText for logging output
        log_frame = tk.Frame(root, padx=10, pady=10)
        log_frame.pack(expand=True, fill=tk.BOTH)
        
        tk.Label(log_frame, text="Activity Log:").pack(anchor=tk.W)
        self.log_widget = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled')
        self.log_widget.pack(expand=True, fill=tk.BOTH)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path_var.set(folder_selected)

    def update_log(self, message):
        self.log_widget.config(state='normal')
        self.log_widget.insert(tk.END, message)
        self.log_widget.see(tk.END)
        self.log_widget.config(state='disabled')
        self.root.update_idletasks()

    def open_config_folder(self):
        """New: Opens the configuration folder in the system file explorer."""
        config_dir = get_config_dir()
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(config_dir)
            elif system == "Darwin": # macOS
                subprocess.Popen(["open", config_dir])
            else: # Linux
                subprocess.Popen(["xdg-open", config_dir])
            self.update_log(f"Opened config folder: {config_dir}\n")
        except Exception as e:
            self.update_log(f"Error opening config folder: {e}\n")
            logging.error(f"Failed to open config folder: {e}")

    def start_organization(self):
        self.log_widget.config(state='normal')
        self.log_widget.delete('1.0', tk.END)
        self.log_widget.config(state='disabled')

        file_mappings = load_config()
        if file_mappings is None:
            message = "Fatal Error: Could not load config.json. Check logs for details."
            self.update_log(message + "\n")
            messagebox.showerror("Error", message)
            return
        
        folder_path = self.folder_path_var.get()
        if not folder_path:
            messagebox.showwarning("Warning", "Please select a target folder first.")
            return

        is_recursive = self.recursive_var.get()
        
        self.update_log("Starting organization...\n")
        self.update_log(f"Target Folder: {folder_path}\n")
        self.update_log(f"Recursive Mode: {'On' if is_recursive else 'Off'}\n")
        self.update_log(f"Log file location: {log_file_path}\n")
        self.update_log("--------------------\n")
        
        result = organize_folder(folder_path, file_mappings, is_recursive, self.update_log)

        if result:
            summary_report, total_files = result
            summary_message = "\n--------------------\nOrganization Complete!\n"
            summary_message += f"Total files processed: {total_files}.\nSummary:\n"
            for category, count in summary_report.items():
                if count > 0:
                    summary_message += f"- {category}: {count} file(s)\n"
            self.update_log(summary_message)
            messagebox.showinfo("Success", "Folder organization has been completed!")
        else:
            self.update_log("Error during organization. Check log for details.\n")
            messagebox.showerror("Failed", "An error occurred. Please check the log file for details.")


if __name__ == "__main__":
    # Ensure we log the application start before the mainloop
    logging.info("Application started.")
    app_root = tk.Tk()
    app = OrganizerApp(app_root)
    app_root.mainloop()
    logging.info("Application closed.")