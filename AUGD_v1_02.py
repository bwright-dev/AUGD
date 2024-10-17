import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget, QHBoxLayout, QStatusBar
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, pyqtSignal, Qt
from datetime import datetime

# Define log folder path dynamically based on the current user
log_folder = os.path.join(os.path.expanduser("~"), "Documents", "AUGD Logs")

# Ensure the log folder exists
os.makedirs(log_folder, exist_ok=True)

# Log file path
log_file_path = os.path.join(log_folder, 'automation_log.txt')

# Set up logging configuration to write log messages to a file
logging.basicConfig(filename=log_file_path, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.info('Application started.')

# Function to get the current timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Define the stylesheet for the application's dark mode appearance
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

# Custom QWebEnginePage class to capture JavaScript console messages from the webpage
class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        """Handle JavaScript console messages and log them accordingly."""
        log_message = f"JavaScript Console - Level: {level}, Message: {message}, Line: {line}, Source: {source}"
        logging.info(log_message)

        # Log messages based on their severity level
        if level == 3:  # Error level messages
            logging.error(f"JS Error [{source}:{line}]: {message}")
        elif level == 2:  # Warning level messages
            logging.warning(f"JS Warning [{source}:{line}]: {message}")
        elif level == 1:  # Info level messages
            logging.info(f"JS Info [{source}:{line}]: {message}")
        else:  # Debug level messages
            logging.debug(f"JS Debug [{source}:{line}]: {message}")

# Main application window class
class MainWindow(QMainWindow):
    # Signal emitted when the page is fully loaded
    page_loaded_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AUGD - Automated User Group Deletion")
        self.setGeometry(100, 100, 1200, 800)
        
        # Apply dark mode styling to the window
        self.setStyleSheet(dark_mode_style)

        # Set up the main layout for the window
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # Set up the WebEngineView to display the webpage
        self.webview = QWebEngineView()
        self.webview.setFixedSize(1200, 800)

        # Use the custom WebEnginePage to capture JavaScript console messages
        self.page = WebEnginePage(self.webview)
        self.webview.setPage(self.page)

        # Load the target URL and connect the page load signal
        self.webview.setUrl(QUrl("https://cp.hivepbx.com"))
        self.webview.loadFinished.connect(self.on_page_load)
        layout.addWidget(self.webview)

        # Set up the horizontal layout for buttons and status label
        hbox = QHBoxLayout()

        # Create the Run Script button and connect it to its function
        self.run_button = QPushButton("Run Script", self)
        self.run_button.clicked.connect(self.run_script)
        hbox.addWidget(self.run_button)

        # Create the Stop Script button and connect it to its function
        self.stop_button = QPushButton("Stop Script", self)
        self.stop_button.clicked.connect(self.stop_script)
        hbox.addWidget(self.stop_button)

        # Status label to show the current state of the script
        self.status_label = QLabel(f"Status: Waiting for user action... [{get_timestamp()}]", self)
        hbox.addWidget(self.status_label)

        # Add the horizontal layout to the main layout
        layout.addLayout(hbox)

        # Add a status bar for additional feedback
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Flag to track if the script is currently running
        self.is_running = False

        # Connect the page loaded signal to trigger JavaScript injection
        self.page_loaded_signal.connect(self.inject_javascript)

    def on_page_load(self):
        """Handle actions when the page finishes loading."""
        logging.info("Page loaded successfully.")
        self.status_label.setText(f"Status: Page loaded... [{get_timestamp()}]")
        self.page_loaded_signal.emit()

    def inject_javascript(self):
        """Inject JavaScript code into the webpage to automate actions."""
        if not self.is_running:
            logging.info("JavaScript injection skipped because script is not running.")
            return

        # JavaScript code to automate navigation and deletion of user groups
        script = """
        (async function() {
            let stop = false;

            window.stopScript = function() { 
                stop = true; 
                console.log("Script stopped by user.");
            };

            console.log("Navigating to the User Groups page first...");

            function openDropdown() {
                let dropdownToggle = document.querySelector('a.dropdown-toggle.media-heading');
                if (dropdownToggle) {
                    console.log("Dropdown toggle found, triggering the dropdown.");
                    dropdownToggle.click();
                } else {
                    console.error("Dropdown toggle not found.");
                }
            }

            function waitFor(milliseconds) {
                return new Promise(resolve => setTimeout(resolve, milliseconds));
            }

            async function retryClick(selector, maxRetries = 5, baseDelay = 1000) {
                let attempt = 0;
                let backoff = baseDelay;

                while (attempt < maxRetries) {
                    let element = document.querySelector(selector);
                    if (element) {
                        console.log("User Groups link found, clicking...");
                        element.click();
                        return true;
                    } else {
                        console.log(`Attempt ${attempt + 1}: User Groups link not found, retrying in ${backoff}ms...`);
                        await waitFor(backoff);
                        attempt++;
                        backoff *= 2;  // Exponential backoff
                    }
                }

                console.error("User Groups link not found after max retries.");
                return false;
            }

            async function navigateToUserGroups() {
                openDropdown();

                // Retry clicking the User Groups link with dynamic backoff using the provided path
                return await retryClick("#header_nav > div > div.row.top-menu > div > ul > li.profile > div > div.media-body.dropdown.open > ul > li:nth-child(5) > a");
            }

            async function selectCompany(option) {
                let companySelect = document.querySelector('#company_data');
                if (companySelect) {
                    companySelect.value = option.value;
                    console.log(`Switching to company: ${option.textContent.trim()}`);
                    companySelect.dispatchEvent(new Event('change'));
                    return true;
                } else {
                    console.error("Company select element not found.");
                    return false;
                }
            }

            async function deleteUserGroups() {
                console.log("Starting to delete user groups for the current company...");

                let groups = document.querySelectorAll('a[role="button"][data-toggle="collapse"]');
                if (groups.length === 0) {
                    console.error("No user groups found.");
                    return;
                }

                console.log(`Found ${groups.length} user groups.`);

                for (let i = 0; i < groups.length; i++) {
                    if (stop) {
                        console.log("Script stopped by user.");
                        break;
                    }
                    let group = groups[i];
                    group.click();
                    console.log(`Expanded group ${i}`);

                    await waitFor(500);

                    let memberCounter = document.querySelector(`#memberCounter${i}`);
                    if (memberCounter && memberCounter.textContent === "0") {
                        let deleteButton = group.querySelector('button[onclick^="delete_group"]');
                        if (deleteButton) {
                            deleteButton.click();
                            console.log(`Deleted group ${i}`);
                        } else {
                            console.warn(`No delete button found for group ${i}`);
                        }

                        await waitFor(500);
                    } else {
                        console.warn(`Group ${i} has members and was not deleted.`);
                    }
                }

                console.log("Finished deleting all eligible user groups for the current company.");
            }

            async function switchCompaniesAndDeleteGroups() {
                let companySelect = document.querySelector('#company_data');
                let companyOptions = companySelect ? companySelect.querySelectorAll('option') : [];

                if (companyOptions.length === 0) {
                    console.error("No company options found.");
                    return;
                }

                console.log(`Found ${companyOptions.length} companies.`);

                for (let i = 0; i < companyOptions.length; i++) {
                    if (stop) {
                        console.log("Script stopped by user.");
                        break;
                    }
                    let option = companyOptions[i];
                    let success = await selectCompany(option);

                    if (!success) {
                        console.error(`Failed to switch to company: ${option.textContent.trim()}`);
                        continue;
                    }

                    console.log(`Processing company: ${option.textContent.trim()}`);

                    await waitFor(1500); 
                    await deleteUserGroups();  
                    await waitFor(1500); 
                }

                console.log("Finished iterating through all companies and deleting user groups.");
            }

            // Step 1: Navigate to the User Groups page
            if (await navigateToUserGroups()) {
                setTimeout(() => {
                    // Step 2: Start processing companies and deleting groups after navigating to the User Groups page
                    switchCompaniesAndDeleteGroups();
                }, 3000);  // Wait for 3 seconds to ensure User Groups page loads
            }

        })();
        """
        
        # Inject JavaScript to execute the actions on the webpage
        self.webview.page().runJavaScript(script)

    def run_script(self):
        """Start the script to automate user group deletion."""
        logging.info("Script started.")
        self.status_label.setText(f"Status: Running script... [{get_timestamp()}]")
        self.is_running = True
        self.inject_javascript()

    def stop_script(self):
        """Stop the running JavaScript script gracefully."""
        logging.info("Script stopped by user.")
        self.is_running = False
        self.status_label.setText(f"Status: Stopping script... [{get_timestamp()}]")

        # Set the stop flag in JavaScript to terminate the script
        self.webview.page().runJavaScript("window.stopScript();")
        self.status_label.setText(f"Status: Script stopped. Ready to run again. [{get_timestamp()}]")

    def py_script_finished(self):
        """Handle the completion of the script."""
        if self.is_running:
            logging.info("Script completed successfully.")
            self.status_label.setText(f"Status: Script completed. [{get_timestamp()}]")
            self.status_bar.showMessage(f"Automation completed at {get_timestamp()}")
        else:
            logging.info("Script stopped early by user.")
            self.status_label.setText(f"Status: Script stopped early. Ready to run again. [{get_timestamp()}]")
            self.status_bar.showMessage(f"Automation stopped at {get_timestamp()}")

def main():
    # Create the application instance
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)  # Enable high DPI scaling for better display on high-resolution screens
    
    # Create and show the main window
    window = MainWindow()
    window.show()

    # Execute the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
