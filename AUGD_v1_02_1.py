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
        self.page = WebEnginePage(self.webview)
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

        # Full JavaScript injection without hard waits
        script = """
      const delay = (durationMs) => {
  return new Promise(resolve => setTimeout(resolve, durationMs));
}
(async function() {
    let stop = false;

    // Helper function to introduce a delay (wait)
    const delay = (durationMs) => {
        return new Promise(resolve => setTimeout(resolve, durationMs));
    }

    // Unified waitForElement function to handle both appearing and disappearing elements
    async function waitForElement(selector, timeout = 20000, shouldAppear = true) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            const interval = setInterval(() => {
                const element = document.querySelector(selector);
                const timeElapsed = Date.now() - startTime;

                if (shouldAppear && element) {
                    clearInterval(interval);
                    console.log(`Element appeared: ${selector}`);
                    resolve(element);
                } else if (!shouldAppear && !element) {
                    clearInterval(interval);
                    console.log(`Element disappeared: ${selector}`);
                    resolve(true);
                } else if (timeElapsed > timeout) {
                    clearInterval(interval);
                    reject(new Error(`Timeout waiting for selector: ${selector}`));
                }
            }, 100);
        });
    }

    async function closeModalIfNoCheckboxes() {
        try {
            console.log("Checking if modal has no checkboxes...");

            // Wait for the modal to appear
            await waitForElement('#availableUsersForm', 5000);

            // Check if there are no checkboxes
            let checkboxes = document.querySelectorAll('input[type="checkbox"][name="userUuid[]"]');
            if (checkboxes.length === 0) {
                console.log("No available users to add, closing the modal by clicking on the screen.");

                // Simulate a click in the middle of the screen to close the modal
                let middleOfScreen = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: window.innerWidth / 2,
                    clientY: window.innerHeight / 2
                });
                document.dispatchEvent(middleOfScreen);

                // Wait for the modal to disappear
                await waitForElement('.modal.show', 5000, false);
                console.log("Modal successfully closed by clicking the screen.");
                
                // Ensure there is a delay before continuing
                await delay(300);
            } else {
                console.log("Found checkboxes, proceeding with user addition.");
            }
        } catch (error) {
            console.error("Error closing modal:", error);
        }
    }

    async function navigateToUserGroups() {
        try {
            console.log("Attempting to find and click the dropdown...");

            let dropdown = await waitForElement('a.dropdown-toggle.media-heading');
            dropdown.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            await delay(300); // Delay before clicking the dropdown
            
            let event = new MouseEvent('click', {
                view: window,
                bubbles: true,
                cancelable: true
            });
            dropdown.dispatchEvent(event);
            console.log("Successfully clicked the dropdown menu.");

            let userGroupsLink = await waitForElement('li.sub:nth-child(5) > a:nth-child(1)');
            await delay(500); // Delay before navigating to user groups page
            
            userGroupsLink.click();
            console.log("Successfully navigated to 'User Groups'.");

            await delay(200); // Delay before starting company processing

            await processCompanies();

        } catch (error) {
            console.error("Error navigating to 'User Groups':", error);
        }
    }

    async function processCompanies() {
        try {
            console.log("Attempting to find the company dropdown...");

            let companySelect = await waitForElement('#company_data');
            let companies = companySelect.querySelectorAll('option');

            if (companies.length === 0) {
                console.error("No companies found.");
                return;
            }

            console.log(`Found ${companies.length} companies.`);

            for (let i = 0; i < companies.length; i++) {
                if (stop) {
                    console.log("Script stopped by user.");
                    break;
                }

                let option = companies[i];
                let companyName = option.textContent.trim();
                console.log(`Selecting the company: ${companyName}`);

                await selectCompany(option);

                await delay(2200);  // Delay before processing user groups

                let allGroupsProcessed = await processUserGroupsInCompany();

                if (!allGroupsProcessed) {
                    console.warn("Error occurred while processing user groups, skipping to the next company.");
                } else {
                    console.log(`Successfully processed all user groups for company: ${companyName}`);
                }
            }

            console.log("Finished processing all companies.");
        } catch (error) {
            console.error("Error processing companies:", error);
        }
    }

    async function selectCompany(option) {
        try {
            let companySelect = document.querySelector('#company_data');
            if (companySelect) {
                companySelect.value = option.value;
                companySelect.dispatchEvent(new Event('change'));

                await waitForElement('#loadingIndicator', 10000, false);
                console.log(`Selected company: ${option.textContent.trim()}`);

                await delay(300); // Delay after company selection
            } else {
                console.error("Company select element not found.");
            }
        } catch (error) {
            console.error("Error selecting company:", error);
        }
    }

    async function processUserGroupsInCompany() {
        try {
            console.log("Starting to process user groups in the company...");

            let groups = document.querySelectorAll('a[role="button"][data-toggle="collapse"]');

            if (groups.length === 0) {
                console.error("No user groups found.");
                return false;
            }

            console.log(`Found ${groups.length} user groups.`);

            for (let i = 0; i < groups.length; i++) {
                if (stop) {
                    console.log("Script stopped by user.");
                    return false;
                }

                let group = groups[i];
                group.click();
                console.log(`Expanded group ${i}`);

                await delay(300); // Short delay after expanding group

                let groupNameElement = await waitForElement(`input[id^="groupName"][id$="${i}"]`);
                let groupName = groupNameElement.value.trim().toLowerCase();
                console.log(`Group ${i} name parsed as: '${groupName}'`);

                if (groupName === 'everyone') {
                    let memberCounter = document.querySelector(`#memberCounter${i}`);
                    if (memberCounter && parseInt(memberCounter.value) > 0) {
                        console.log(`Found 'Everyone' group with members (group ${i}).`);
                        await handleFirstEveryoneGroupWithMembers();
                    }
                }

                let memberCounter = document.querySelector(`#memberCounter${i}`);
                if (memberCounter && memberCounter.value === "0") {
                    let deleteButtonSelector = `#collapse${i} .panel-body button.btn.btn-danger.pull-right`;
                    let deleteButton = await waitForElement(deleteButtonSelector, 10000, true);

                    await delay(300); // Delay before clicking the delete button
                    
                    if (deleteButton) {
                        deleteButton.click();
                        console.log(`Deleted group ${i}`);
                        await waitForElement(`#group_${i}`, 5000, false);
                    } else {
                        console.warn(`Delete button for group ${i} not found or not visible.`);
                    }
                } else {
                    console.log(`Group ${i} has members and was not deleted.`);
                }
            }

            return true;
        } catch (error) {
            console.error("Error processing user groups in company:", error);
            return false;
        }
    }

    async function handleFirstEveryoneGroupWithMembers() {
        console.log("Handling the first 'Everyone' group with members...");
        let groups = document.querySelectorAll('a[role="button"][data-toggle="collapse"]');
        let foundGroup = false;

        for (let i = 0; i < groups.length; i++) {
            if (stop) break;

            let groupNameElement = document.querySelector(`input[id^="groupName"][id$="${i}"]`);
            if (groupNameElement && groupNameElement.value.trim().toLowerCase() === 'everyone') {
                let memberCounter = document.querySelector(`#memberCounter${i}`);
                if (memberCounter && parseInt(memberCounter.value) > 0) {
                    console.log(`Found 'Everyone' group with members (group ${i}), interacting with 'Add Member' button.`);

                    let addButton = document.querySelector('a.add_button[onclick="add_group_user(1);"]');
                    if (addButton) {
                        addButton.click();
                        
                        // Wait for the modal to appear
                        await waitForElement('#availableUsersForm', 5000);

                        // Check if there are no checkboxes
                        let checkboxes = document.querySelectorAll('input[type="checkbox"][name="userUuid[]"]');
                        if (checkboxes.length === 0) {
                            console.log("No available users to add, closing the modal by clicking on the screen.");

                            // Simulate a click in the middle of the screen to close the modal
                            let middleOfScreen = new MouseEvent('click', {
                                view: window,

                                bubbles: true,
                                cancelable: true,
                                clientX: window.innerWidth / 2,
                                clientY: window.innerHeight / 2
                            });
                            document.dispatchEvent(middleOfScreen);
                            
                            await waitForElement('.modal.show', 5000, false); // Wait for modal to disappear
                            console.log("Modal successfully closed by clicking the screen.");
                        } else {
                            // If checkboxes are present, proceed to select them and add members
                            checkboxes.forEach(checkbox => checkbox.click());

                            let submitButton = document.querySelector('button.btn.btn-primary[type="submit"]');
                            if (submitButton) {
                                submitButton.click();
                                console.log("All members added and confirmed.");
                                await waitForElement('.modal.show', 5000, false); // Wait for modal to disappear
                            }
                        }
                        foundGroup = true;
                        break;
                    } else {
                        console.error("'Add Member' button not found.");
                    }
                }
            }
        }

        if (!foundGroup) {
            console.warn("'Everyone' group with members not found.");
        }
        return foundGroup;
    }

    async function deleteEveryOtherEveryoneGroup() {
        console.log("Starting to delete every other 'Everyone' group...");
        let groups = document.querySelectorAll('a[role="button"][data-toggle="collapse"]');
        let deleteNext = false;

        for (let i = 0; i < groups.length; i++) {
            if (stop) break;

            let groupNameElement = document.querySelector(`input[id^="groupName"][id$="${i}"]`);
            if (groupNameElement && groupNameElement.value.trim().toLowerCase() === 'everyone') {
                if (deleteNext) {
                    console.log(`Deleting 'Everyone' group (group ${i})`);

                    let deleteButton = document.querySelector(`#deleteButton${i}`);
                    if (deleteButton) {
                        deleteButton.click();
                        await delay(1000); // Short wait before moving on
                    } else {
                        console.error(`Delete button for group ${i} not found.`);
                    }
                }
                deleteNext = !deleteNext;
            }
        }

        console.log("Finished deleting every other 'Everyone' group.");
    }

    await navigateToUserGroups();

})();
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
