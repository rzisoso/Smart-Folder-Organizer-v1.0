import os
import sys
import shutil
import json
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext



# --- 1. Logging Setup ---
# Configure the logger to save log messages to organizer.log
logging.basicConfig(
    filename='organizer.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8' # Use utf-8 to support non-ASCII characters in paths
)


# --- 2. Configuration Loading from JSON ---


def get_config_path():
    """
    获取config.json的绝对路径。
    这能确保在开发环境和PyInstaller打包后都能正确找到文件。
    """
    if getattr(sys, 'frozen', False):
        #如果程序被打包了
        application_path = os.path.dirname(sys.executable)
    else:
        #如果程序是在正常Python环境中运行
        application_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(application_path, 'config.json')


def load_config():
    """Loads the file type mapping configuration from a JSON file."""
    config_file_path = get_config_path() 
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # For consistency, convert all extensions to lowercase
            mappings = config.get("file_type_mappings", {})
            for category, extensions in mappings.items():
                mappings[category] = [ext.lower() for ext in extensions]
            return mappings
    except FileNotFoundError:
        logging.error(f"Configuration file '{config_file_path}' not found.")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error decoding the configuration file '{config_file_path}'. Please check its format.")
        return None

# --- 3. Core Organization Logic ---
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

# --- 4. Graphical User Interface (GUI) ---
class OrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Folder Organizer")
        self.root.geometry("600x450")

        # Frame for folder selection
        top_frame = tk.Frame(root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)

        tk.Label(top_frame, text="Target Folder:").pack(side=tk.LEFT)
        self.folder_path_var = tk.StringVar()
        tk.Entry(top_frame, textvariable=self.folder_path_var, width=50).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(top_frame, text="Browse...", command=self.browse_folder).pack(side=tk.LEFT)

        # Frame for options and actions
        action_frame = tk.Frame(root, padx=10, pady=5)
        action_frame.pack(fill=tk.X)
        
        self.recursive_var = tk.BooleanVar()
        tk.Checkbutton(action_frame, text="Organize Subfolders (Recursive)", variable=self.recursive_var).pack(side=tk.LEFT)
        
        tk.Button(action_frame, text="Start Organizing", command=self.start_organization, bg="lightblue", font=('Helvetica', 10, 'bold')).pack(side=tk.RIGHT, padx=10)

        # ScrolledText for logging output
        log_frame = tk.Frame(root, padx=10, pady=10)
        log_frame.pack(expand=True, fill=tk.BOTH)
        
        tk.Label(log_frame, text="Activity Log:").pack(anchor=tk.W)
        self.log_widget = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled')
        self.log_widget.pack(expand=True, fill=tk.BOTH)

    def browse_folder(self):
        """Opens a dialog to select a folder."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path_var.set(folder_selected)

    def update_log(self, message):
        """Thread-safely updates the log widget in the GUI."""
        self.log_widget.config(state='normal')
        self.log_widget.insert(tk.END, message)
        self.log_widget.see(tk.END) # Auto-scroll to the bottom
        self.log_widget.config(state='disabled')
        self.root.update_idletasks() # Refresh the UI

    def start_organization(self):
        """Starts the file organization process."""
        # Clear the log widget
        self.log_widget.config(state='normal')
        self.log_widget.delete('1.0', tk.END)
        self.log_widget.config(state='disabled')

        # Load configuration
        file_mappings = load_config()
        if file_mappings is None:
            messagebox.showerror("Error", "Could not load 'config.json'. Please ensure the file exists and is correctly formatted.")
            return
        
        folder_path = self.folder_path_var.get()
        if not folder_path:
            messagebox.showwarning("Warning", "Please select a target folder first.")
            return

        is_recursive = self.recursive_var.get()
        
        self.update_log("Starting organization...\n")
        self.update_log(f"Target Folder: {folder_path}\n")
        self.update_log(f"Recursive Mode: {'On' if is_recursive else 'Off'}\n")
        self.update_log("--------------------\n")
        
        # For large numbers of files, running this in a separate thread
        # would be a good improvement to prevent the UI from freezing.
        # For simplicity, we call it directly here.
        result = organize_folder(folder_path, file_mappings, is_recursive, self.update_log)

        if result:
            summary_report, total_files = result
            # Print the summary report
            summary_message = "\n--------------------\nOrganization Complete!\n"
            summary_message += f"Total files processed: {total_files}.\nSummary:\n"
            for category, count in summary_report.items():
                if count > 0:
                    summary_message += f"- {category}: {count} file(s)\n"
            self.update_log(summary_message)
            messagebox.showinfo("Success", "Folder organization has been completed!")
        else:
            messagebox.showerror("Failed", "An error occurred during organization. Please check organizer.log for details.")


if __name__ == "__main__":
    app_root = tk.Tk()
    app = OrganizerApp(app_root)
    app_root.mainloop()