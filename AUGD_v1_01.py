import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget, QHBoxLayout, QStatusBar
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from datetime import datetime

# Define log folder path dynamically based on the current user
log_folder = os.path.join(os.path.expanduser("~"), "Documents", "AUGD Logs")

# Ensure the log folder exists
os.makedirs(log_folder, exist_ok=True)

# Log file path
log_file_path = os.path.join(log_folder, 'automation_log.txt')

# Logging setup
logging.basicConfig(filename=log_file_path, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.info('Application started.')

# Function to get the current timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Modern, sleek dark mode stylesheet
dark_mode_style = """
    QMainWindow {
        background-color: #2b2b2b;
        color: #ffffff;
    }
    QLabel, QPushButton {
        font-size: 16px;
        color: #ffffff;
    }
    QPushButton {
        background-color: #3a3f44;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
    }
    QPushButton:hover {
        background-color: #50575d;
    }
    QPushButton:pressed {
        background-color: #696f75;
    }
    QStatusBar {
        background-color: #2b2b2b;
        color: #ffffff;
    }
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AUGD - Automated User Group Deletion")
        self.setGeometry(100, 100, 800, 600)
        
        # Apply dark mode styling
        self.setStyleSheet(dark_mode_style)

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # WebView to show the web page
        self.webview = QWebEngineView()
        self.webview.setUrl(QUrl("https://cp.hivepbx.com"))  # Load the target URL
        layout.addWidget(self.webview)

        # Horizontal Layout for Buttons and Status
        hbox = QHBoxLayout()

        # Run Script Button
        self.run_button = QPushButton("Run Script", self)
        self.run_button.clicked.connect(self.run_script)
        hbox.addWidget(self.run_button)

        # Stop Script Button
        self.stop_button = QPushButton("Stop Script", self)
        self.stop_button.clicked.connect(self.stop_script)
        hbox.addWidget(self.stop_button)

        # Status label for current operation
        self.status_label = QLabel(f"Status: Waiting for user action... [{get_timestamp()}]", self)
        hbox.addWidget(self.status_label)

        # Add HBox to main layout
        layout.addLayout(hbox)

        # Add a status bar for better feedback
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Flag to track script running state
        self.is_running = False

    def run_script(self):
        """Inject JavaScript to click buttons and interact with the page."""
        logging.info("Script started.")
        self.status_label.setText(f"Status: Running script... [{get_timestamp()}]")
        self.is_running = True
        
        # JavaScript to click buttons and interact with the page
        script = """
        (function() {
            if (typeof window.stopScript !== "undefined") {
                window.stopScript();  // Reset the stop flag if the script is being restarted
            }

            let stop = false;
            window.stopScript = function() { stop = true; };

            (async function() {
                let groups = document.querySelectorAll('a[role="button"][data-toggle="collapse"]');
                
                for (let index = 0; index < groups.length; index++) {
                    if (stop) {
                        console.log('Script stopped');
                        break;
                    }
                    
                    let group = groups[index];
                    group.click();  // Expand the group
                    console.log(`Expanded group at index ${index}`);
                    
                    // Simulate a delay for the group content to load
                    await new Promise(resolve => setTimeout(resolve, 500));

                    let memberCounter = document.querySelector(`#memberCounter${index}`);
                    if (memberCounter && memberCounter.value === "0") {
                        // Find and click the delete button
                        let deleteButton = document.querySelector(`button[onclick="delete_group(${index});"]`);
                        if (deleteButton) {
                            deleteButton.click();  // Click the delete button
                            console.log(`Clicked delete button for group ${index}`);
                            await new Promise(resolve => setTimeout(resolve, 500));  // Wait for the confirmation dialog

                            // Confirm the deletion by clicking the confirm button
                            let confirmButton = document.querySelector('#deleteGroup');
                            if (confirmButton) {
                                confirmButton.click();
                                console.log(`Group at index ${index} deleted successfully.`);
                            }
                        }
                    }
                }

                // Notify Python that the script is finished (only if Python callback is available)
                if (typeof window.py_script_finished === "function") {
                    window.py_script_finished();
                } else {
                    console.log("Python callback not available.");
                }
            })();
        })();
        """
        
        # Inject JavaScript to execute the actions
        self.webview.page().runJavaScript(script)

    def stop_script(self):
        """Stop the running JavaScript and allow restart."""
        logging.info("Script stopped by user.")
        self.is_running = False
        self.status_label.setText(f"Status: Stopping script... [{get_timestamp()}]")
        
        # Stop the running script by setting stop flag in JS
        self.webview.page().runJavaScript("window.stopScript();")
        self.status_label.setText(f"Status: Script stopped. Ready to run again. [{get_timestamp()}]")

    def py_script_finished(self):
        """Callback when the script finishes executing."""
        if self.is_running:
            logging.info("Script completed successfully.")
            self.status_label.setText(f"Status: Script completed. [{get_timestamp()}]")
            self.status_bar.showMessage(f"Automation completed at {get_timestamp()}")
        else:
            logging.info("Script stopped early by user.")
            self.status_label.setText(f"Status: Script stopped early. Ready to run again. [{get_timestamp()}]")
            self.status_bar.showMessage(f"Automation stopped at {get_timestamp()}")

def main():
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
