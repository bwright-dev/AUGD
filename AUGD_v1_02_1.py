import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton,
    QLabel, QWidget, QHBoxLayout, QStatusBar
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, pyqtSlot
from datetime import datetime

# Set up logging folder and file
log_folder = os.path.join(os.path.expanduser("~"), "Documents", "AUGD Logs")
os.makedirs(log_folder, exist_ok=True)
log_file_path = os.path.join(log_folder, "automation_log.txt")

# Set up log rotation (5MB per file, 2 backups)
log_handler = RotatingFileHandler(log_file_path, maxBytes=5 * 1024 * 1024, backupCount=2)
logging.basicConfig(handlers=[log_handler], level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Application started.")

# Get the current timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Define stylesheet for dark mode
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

# Custom class to capture JavaScript console messages
class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        log_message = f"JavaScript Console - Level: {level}, Message: {message}, Line: {line}, Source: {source}"
        logging.info(log_message)

        if level == 3:  # Error level
            logging.error(f"JS Error [{source}:{line}]: {message}")
        elif level == 2:  # Warning level
            logging.warning(f"JS Warning [{source}:{line}]: {message}")
        elif level == 1:  # Info level
            logging.info(f"JS Info [{source}:{line}]: {message}")
        else:
            logging.debug(f"JS Debug [{source}:{line}]: {message}")

# Main application window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AUGD - Automated User Group Deletion")
        self.setGeometry(100, 100, 1200, 800)

        # Apply dark mode styling
        self.setStyleSheet(dark_mode_style)

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # WebEngineView to display webpage
        self.webview = QWebEngineView()
        self.webview.setFixedSize(1200, 800)

        # Custom page to capture console messages
        self.page = WebEnginePage()
        self.webview.setPage(self.page)

        # Load target URL
        self.webview.setUrl(QUrl("https://cp.hivepbx.com"))
        self.webview.loadFinished.connect(self.on_page_load)
        layout.addWidget(self.webview)

        # Horizontal layout for buttons and status label
        hbox = QHBoxLayout()

        # Run Script button
        self.run_button = QPushButton("Run Script", self)
        self.run_button.clicked.connect(self.run_script)
        hbox.addWidget(self.run_button)

        # Stop Script button
        self.stop_button = QPushButton("Stop Script", self)
        self.stop_button.clicked.connect(self.stop_script)
        hbox.addWidget(self.stop_button)

        # Status label
        self.status_label = QLabel(f"Status: Waiting for user action... [{get_timestamp()}]", self)
        hbox.addWidget(self.status_label)

        # Add hbox to main layout
        layout.addLayout(hbox)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Script running flag
        self.is_running = False

    def inject_javascript(self):
        """Directly inject JavaScript into the webpage."""
        logging.info("Injecting JavaScript...")
        self.status_label.setText(f"Status: Injecting JavaScript... [{get_timestamp()}]")

        script = """
        console.log("JavaScript injection started");

        async function delay(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        async function waitForElementAppear(selector, timeout = 20000) {
            return new Promise((resolve, reject) => {
                const startTime = Date.now();
                const checkExist = setInterval(() => {
                    const element = document.querySelector(selector);
                    if (element) {
                        clearInterval(checkExist);
                        resolve(element);
                    } else if (Date.now() - startTime >= timeout) {
                        clearInterval(checkExist);
                        console.error(`Element ${selector} did not appear within ${timeout} ms`);
                        reject(new Error(`Element ${selector} did not appear within ${timeout} ms`));
                    }
                }, 100); // Check every 100 ms
            });
        }

        async function waitForElementRemoved(selector, timeout = 10000) {
            return new Promise((resolve, reject) => {
                const startTime = Date.now();
                const checkExist = setInterval(() => {
                    const element = document.querySelector(selector);
                    if (!element) {
                        clearInterval(checkExist);
                        resolve();
                    } else if (Date.now() - startTime >= timeout) {
                        clearInterval(checkExist);
                        reject(new Error(`Element ${selector} did not disappear within ${timeout} ms`));
                    }
                }, 100); // Check every 100 ms
            });
        }

        async function automateUserGroupManagement() {
            console.log("Inside automateUserGroupManagement function...");
            // Open the navigation dropdown
            let dropdown = await waitForElementAppear('#header_nav > div > div.row.top-menu > div > ul > li.profile > div > div.media-body.dropdown > a');
            console.log("Dropdown element found:", dropdown);
            dropdown.click();
            console.log("Opened navigation dropdown.");
            await delay(2500); // Wait for 2.5 seconds

            // Go to User Groups page
            let userGroupsLink = await waitForElementAppear('#header_nav > div > div.row.top-menu > div > ul > li.profile > div > div.media-body.dropdown > ul > li:nth-child(5) > a');
            console.log("User groups link found:", userGroupsLink);
            userGroupsLink.click();
            console.log("Navigated to User Groups page.");
            await delay(2500); // Wait for 2.5 seconds
        }

        async function processAllCompanies() {
            let companies = document.querySelectorAll('#select2-company_data-container option');
            let totalCompanies = companies.length;

            // Assuming progress starts at 0
            let startFrom = 0;  // Set this to a higher value to resume from a specific company if needed

            for (let i = startFrom; i < totalCompanies; i++) {
                try {
                    let companySelect = document.querySelector('#select2-company_data-container');
                    companySelect.value = companies[i].value;
                    companySelect.dispatchEvent(new Event('change'));
                    console.log(`Processing company (${i + 1}/${totalCompanies}): ${companies[i].textContent.trim()}`);

                    // Wait for 2.5 seconds between each selection
                    await delay(2500);

                    // Wait for the loading indicator to disappear
                    await waitForElementRemoved('#loadingIndicator', 10000);

                    // Process user groups within the selected company
                    await processUserGroupsInCompany(i);

                } catch (error) {
                    console.error(`Error processing company ${i + 1}: ${error.message}`);
                    // Optionally, retry logic or continue to the next company
                    continue;  // Skip this company and move to the next
                }
            }

    }

        function on_script_finished() {
            console.log("All companies processed. Script completed successfully.");
            // You can add additional code to handle post-processing here
    }

        function delay(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
    }

        async function waitForElementRemoved(selector, timeout) {
            return new Promise((resolve, reject) => {
                let timer;
                let observer = new MutationObserver((mutations, obs) => {
                    if (!document.querySelector(selector)) {
                        obs.disconnect();
                        clearTimeout(timer);
                        resolve();
                    }
                });

                observer.observe(document.body, { childList: true, subtree: true });

                // Timeout after specified time
                timer = setTimeout(() => {
                    observer.disconnect();
                    reject(new Error(`Timeout waiting for ${selector} to be removed.`));
                }, timeout);
            });
    }


        async function processUserGroupsInCompany(companyIndex) {
            console.log("Processing user groups for company index:", companyIndex);
            let groups = document.querySelectorAll('a[role="button"][data-toggle="collapse"]');

            if (groups.length === 0) {
                console.log("No user groups found for company index:", companyIndex);
                return; // No groups found, go to the next company
            }

            for (let i = 0; i < groups.length; i++) {
                let group = groups[i];
                group.click(); // Click the group to expand
                console.log(`Expanded group: ${group.textContent.trim()}`);
                await delay(2500); // Wait for 2.5 seconds

                let memberCounter = document.querySelector(`#memberCounter${i}`);
                if (memberCounter && memberCounter.value === "0") {
                    // Group has no members, delete it
                    await deleteGroup(group);
                } else {
                    // Check if it's an 'Everyone' group with members
                    let groupNameElement = document.querySelector("#groupNameLabel" + (i + 1));
                    if (groupNameElement && groupNameElement.value.trim().toLowerCase() === 'everyone') {
                        await handleEveryoneGroupWithMembers(group);
                    }
                }
                // Wait for the group to be fully processed before moving to the next one
                await waitForElementRemoved(`#collapse${i}`);
            }

            // After processing, delete all other 'Everyone' groups regardless of members
            await deleteAllOtherEveryoneGroups();
        }

        async function deleteGroup(group) {
            console.log(`Deleting group: ${group.textContent.trim()}`);
            let deleteButton = await waitForElementAppear(`#collapse${i} > div > div > div.col-lg-12.pull-right > button`);
            deleteButton.click();
            console.log("Clicked delete button.");
            await delay(2500); // Wait for 2.5 seconds

            let confirmButton = await waitForElementAppear('#deleteGroup');
            confirmButton.click();
            console.log("Clicked confirm button for deletion.");
            await delay(2500); // Wait for 2.5 seconds
        }

        async function handleEveryoneGroupWithMembers(group) {
            console.log(`Handling 'Everyone' group with members: ${group.textContent.trim()}`);
            let addButton = document.querySelector("#directionext_result > a > span");
            addButton.click();
            console.log("Clicked add members button.");
            await delay(2500); // Wait for 2.5 seconds

            let checkboxes = document.querySelectorAll('#availableUsersForm > div.modal-body > ul > li:nth-child(4) > label > input[type=checkbox]');
            checkboxes.forEach(checkbox => checkbox.click());
            console.log("Clicked all checkboxes.");

            let submitButton = document.querySelector('#availableUsersForm > div.modal-footer > button.btn.btn-primary');
            submitButton.click();
            console.log("Clicked add members confirmation button.");
            await delay(2500); // Wait for 2.5 seconds
        }

        async function deleteAllOtherEveryoneGroups() {
            console.log("Deleting all other 'Everyone' groups regardless of members.");
            let allGroups = document.querySelectorAll('a[role="button"][data-toggle="collapse"]');
            for (let i = 0; i < allGroups.length; i++) {
                let groupNameElement = document.querySelector("#groupNameLabel" + (i + 1));
                if (groupNameElement && groupNameElement.value.trim().toLowerCase() === 'everyone') {
                    await deleteGroup(allGroups[i]);
                }
            }
        }

        (async function() {
            try {
                console.log("Starting automation process...");
                // Start the automation process
                await automateUserGroupManagement();
                console.log("Automation process completed successfully.");
            } catch (error) {
                console.error("An error occurred during the automation process:", error);
            }
        })();

        console.log("JavaScript injection completed");
        """

        # Inject the JavaScript into the webpage
        self.webview.page().runJavaScript(script, self.on_script_finished)

    def on_page_load(self):
        """Handle page load completion."""
        logging.info("Page loaded successfully.")
        self.status_bar.showMessage(f"Page loaded at {get_timestamp()}")

    def run_script(self):
        """Start script."""
        logging.info("Script started.")
        self.status_label.setText(f"Status: Running script... [{get_timestamp()}]")
        self.is_running = True
        if not self.webview.page().url().isEmpty():
            self.inject_javascript()
        else:
            logging.error("Web page not loaded.")
            self.status_label.setText(f"Error: Web page not loaded. [{get_timestamp()}]")

    def stop_script(self):
        """Stop the running script."""
        logging.info("Script stopped by user.")
        self.is_running = False
        # Inject a stop flag directly into the JavaScript code
        self.webview.page().runJavaScript("window.stop = true;")
        self.status_label.setText(f"Status: Script stopped. [{get_timestamp()}]")

    @pyqtSlot()
    def on_script_finished(self, result):
        """Handle script completion."""
        if self.is_running:
            logging.info("Script completed successfully.")
            self.status_label.setText(f"Status: Script completed. [{get_timestamp()}]")
        else:
            logging.info("Script stopped early by user.")
            self.status_label.setText(f"Status: Script stopped early. [{get_timestamp()}]")

# Main entry point
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
