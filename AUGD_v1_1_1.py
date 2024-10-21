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

# Set up the logging folder and file paths
log_folder = os.path.join(os.path.expanduser("~"), "Documents", "AUGD Logs")
os.makedirs(log_folder, exist_ok=True)  # Create the log folder if it doesn't exist
log_file_path = os.path.join(log_folder, "automation_log.txt")  # Path to the log file

# Configure log rotation: 5MB per file, 2 backups
log_handler = RotatingFileHandler(
    log_file_path, maxBytes=5 * 1024 * 1024, backupCount=2
)
logging.basicConfig(
    handlers=[log_handler],
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("Application started with detailed logging.")

# Function to get the current timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Define the stylesheet for dark mode
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
        """
        Override method to log JavaScript console messages with appropriate levels.
        """
        log_message = f"JavaScript Console - Level: {level}, Message: {message}, Line: {line}, Source: {source}"
        logging.info(log_message)

        # Log the message based on its level
        if level == 3:  # Error level
            logging.error(f"JS Error [{source}:{line}]: {message}")
        elif level == 2:  # Warning level
            logging.warning(f"JS Warning [{source}:{line}]: {message}")
        elif level == 1:  # Info level
            logging.info(f"JS Info [{source}:{line}]: {message}")
        else:
            logging.debug(f"JS Debug [{source}:{line}]: {message}")

# Main application window class
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AUGD - Automated User Group Deletion")
        self.setGeometry(100, 100, 1200, 800)  # Set the window size and position

        # Apply the dark mode stylesheet
        self.setStyleSheet(dark_mode_style)

        # Create the central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # Initialize the QWebEngineView to display the webpage
        self.webview = QWebEngineView()
        self.webview.setFixedSize(1200, 800)  # Set the size of the web view

        # Use the custom WebEnginePage to capture console messages
        self.page = WebEnginePage()
        self.webview.setPage(self.page)

        # Load the target URL into the web view
        self.webview.setUrl(QUrl("https://cp.hivepbx.com"))
        self.webview.loadFinished.connect(self.on_page_load)  # Connect the load signal
        layout.addWidget(self.webview)  # Add the web view to the layout

        # Create a horizontal layout for buttons and status label
        hbox = QHBoxLayout()

        # Run Script button
        self.run_button = QPushButton("Run Script", self)
        self.run_button.clicked.connect(self.run_script)  # Connect to run_script method
        hbox.addWidget(self.run_button)

        # Stop Script button
        self.stop_button = QPushButton("Stop Script", self)
        self.stop_button.clicked.connect(self.stop_script)  # Connect to stop_script method
        hbox.addWidget(self.stop_button)

        # Status label to display messages
        self.status_label = QLabel(
            f"Status: Waiting for user action... [{get_timestamp()}]", self
        )
        hbox.addWidget(self.status_label)

        # Add the horizontal layout to the main layout
        layout.addLayout(hbox)

        # Initialize the status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Flag to track if the script is running
        self.is_running = False

    def inject_javascript(self):
        """Directly inject JavaScript into the webpage."""
        logging.info("Injecting JavaScript...")
        self.status_label.setText(f"Status: Injecting JavaScript... [{get_timestamp()}]")

        # JavaScript code to automate user group management
        script = """
let hasProcessedEveryoneGroupWithMembers = false;

// Function to introduce a delay
async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Function to wait for an element to appear
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
        }, 100);
    });
}

// Function to wait for an element to be removed
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
        }, 100);
    });
}

// Function to reopen a group by its index
async function reopenGroup(groupIndex) {
    let clickableElement = document.querySelector(`#groupID${groupIndex} > div.panel-heading > h4 > a`);
    
    // Check if the group name is null
    await waitForElementRemoved('.spinner', 10000);
    if (clickableElement && clickableElement.textContent.trim() !== "") {
        clickableElement.click();
        console.log(`Reopened group ID ${groupIndex}`);
        await waitForElementRemoved('.spinner', 10000);
        await delay(75);
    } else {
        console.warn(`Skipping group ID ${groupIndex} because the group name is null or empty.`);
        return false;
    }
    return true;
}

// Main automation function
async function automateUserGroupManagement() {
    console.log(`Inside automateUserGroupManagement function...`);
    let dropdown = await waitForElementAppear('#header_nav > div > div.row.top-menu > div > ul > li.profile > div > div.media-body.dropdown > a');
    console.log(`Dropdown element found:`, dropdown);
    dropdown.click();  // Open the navigation dropdown
    console.log(`Opened navigation dropdown.`);
    await waitForElementRemoved('.spinner', 10000);
    await delay(75);

    let userGroupsLink = await waitForElementAppear('#header_nav > div > div.row.top-menu > div > ul > li.profile > div > div.media-body.dropdown > ul > li:nth-child(5) > a');
    console.log(`User groups link found:`, userGroupsLink);
    userGroupsLink.click();  // Navigate to User Groups page
    console.log(`Navigated to User Groups page.`);
    await waitForElementRemoved('.spinner', 10000);
    await delay(75);

    await processAllCompanies();  // Start processing companies
}

// Function to wait for user groups to appear
async function waitForUserGroups(timeout = 500) {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();
        const checkExist = setInterval(() => {
            let groups = document.querySelectorAll('.panel-collapse');  // Update this selector if needed
            if (groups.length > 0) {
                console.log(`User groups found: ${groups.length}`);
                clearInterval(checkExist);
                resolve(groups);
            } else if (Date.now() - startTime >= timeout) {
                clearInterval(checkExist);
                console.warn(`No user groups found within ${timeout} ms for this company.`);
                resolve(null);  // Resolve with null if no user groups found
            }
        }, 100); // Check every 100ms
    });
}

// Function to process all companies
async function processAllCompanies() {
    console.log(`Inside processAllCompanies function...`);
    let companySelect = document.querySelector('#company_data');
    await waitForElementRemoved('.spinner', 10000);  // Wait for the spinner to disappear before proceeding
    if (!companySelect) {
        console.error("Company select element not found!");
        return;
    }

    let companies = document.querySelectorAll('#company_data option');
    console.log(`Found ${companies.length} companies in the hidden dropdown.`);

    // Iterate over each company
    for (let i = 0; i < companies.length; i++) {
        const option = companies[i];
        const companyName = option.textContent.trim();
        const companyValue = option.value;

        console.log(`Processing company (${i + 1}/${companies.length}): ${companyName}`);

        // Reset the flag for each new company
        hasProcessedEveryoneGroupWithMembers = false;
        console.log(`Flag set: hasProcessedEveryoneGroupWithMembers = false for company: ${companyName}`);

        companySelect.value = companyValue;  // Select the company
        await waitForElementRemoved('.spinner', 10000);  // Wait for spinner to disappear
        await delay(500); // Added delay to ensure company data is fully loaded
        companySelect.dispatchEvent(new Event('change'));  // Trigger change event

        await waitForElementRemoved('.spinner', 10000);
        await delay(1000); // Extra delay after the spinner disappears

        // Wait for user groups to appear
        let groups = await waitForUserGroups(500);
        
        if (!groups) {
            console.log(`No user groups found for company index ${i}. Moving to the next company.`);
            continue;  // Move to the next company if no user groups are found
        }

        // Process the user groups
        await processUserGroupsInCompany(i, companyName, groups);
    }
    console.log("Company processing loop finished.");
}

// Function to process user groups within a company
async function processUserGroupsInCompany(companyIndex, companyName, groups) {
    console.log(`Processing user groups for company index: ${companyIndex}`);
    
    if (groups.length === 0) {
        console.log(`No user groups found for company index ${companyIndex}. Moving to the next company.`);
        return;
    }

    console.log(`Found ${groups.length} user groups for company index ${companyIndex}`);

    // Iterate over each group
    for (let i = 0; i < groups.length; i++) {
        let group = groups[i];
        if (!group) {
            console.error(`Group element not found for group ID ${i}. Skipping group.`);
            continue;
        }

        let groupReopened = await reopenGroup(i);
        if (!groupReopened) {
            console.error(`Could not reopen group ${i}. Skipping.`);
            continue;
        }

        let groupNameElement = document.querySelector(`#groupNameLabel${i}`);
        let groupName = groupNameElement ? groupNameElement.innerText.trim() : null;
        console.log(`Group ID ${i} Name: ${groupName ? groupName : 'No Name Found'}`);

        let memberCounter = document.querySelector(`#memberCounter${i}`);

        if (groupName === 'everyone') {
            // Special handling for 'everyone' group
            if (parseInt(memberCounter.value) > 0) {
                if (!hasProcessedEveryoneGroupWithMembers) {
                    console.log(`Processing 'everyone' group ${i} that already has members.`);
                    await handleEveryoneGroupWithMembers(i);
                    hasProcessedEveryoneGroupWithMembers = true;
                    console.log(`Flag set: hasProcessedEveryoneGroupWithMembers = true for group ID ${i}, group name: ${groupName}, company: ${companyName}`);
                } else {
                    console.log(`Deleting 'everyone' group ${i}, as another group has already been processed.`);
                    await deleteGroup(i);
                }
            } else {
                console.log(`Processing 'everyone' group ${i} with no members.`);
                await deleteGroup(i);
            }
        } else {
            // Handling for other groups
            console.log(`Processing non-'everyone' group ${i}: ${groupName}`);
            
            if (parseInt(memberCounter.value) === 0) {
                console.log(`Deleting non-'everyone' group ${i}: ${groupName} as it has no members.`);
                await deleteGroup(i);
            } else {
                console.log(`Skipping non-'everyone' group ${i}: ${groupName} as it has members.`);
            }
            
            await waitForElementRemoved('.spinner', 10000);
            await delay(75);
        }
    }
}


// Function to process user groups within a company
async function processUserGroupsInCompany(companyIndex, companyName) {
    console.log(`Processing user groups for company index: ${companyIndex}`);
    await waitForElementRemoved('.spinner', 10000);
    await delay(75)

    let groups = document.querySelectorAll('.panel-collapse');
        await waitForElementRemoved('.spinner', 10000);
    if (groups.length === 0) {
        console.log(`No user groups found for company index ${companyIndex}. Moving to the next company.`);
        return;
    }

    // Iterate over each group
    for (let i = 0; i < groups.length; i++) {
        let group = groups[i];
        if (!group) {
            console.error(`Group element not found for group ID ${i}. Skipping group.`);
            continue;
        }

        let groupReopened = await reopenGroup(i);
        if (!groupReopened) {
            console.error(`Could not reopen group ${i}. Skipping.`);
            continue;
        }

        let groupNameElement = document.querySelector(`#groupNameLabel${i}`);
        let groupName = groupNameElement ? groupNameElement.innerText.trim() : null;
        let memberCounter = document.querySelector(`#memberCounter${i}`);

        if (groupName === 'everyone') {
            // Special handling for 'everyone' group
            if (parseInt(memberCounter.value) > 0) {
                if (!hasProcessedEveryoneGroupWithMembers) {
                    console.log(`Processing 'everyone' group ${i} that already has members.`);
                    await handleEveryoneGroupWithMembers(i);
                    hasProcessedEveryoneGroupWithMembers = true;
                    console.log(`Flag set: hasProcessedEveryoneGroupWithMembers = true for group ID ${i}, group name: ${groupName}, company: ${companyName}`);
                } else {
                    console.log(`Deleting 'everyone' group ${i}, as another group has already been processed.`);
                    await deleteGroup(i);
                }
            } else {
                console.log(`Processing 'everyone' group ${i} with no members.`);
                await deleteGroup(i);
            }
        } else {
            // Handling for other groups
            console.log(`Processing non-'everyone' group ${i}: ${groupName}`);
            
            if (parseInt(memberCounter.value) === 0) {
                console.log(`Deleting non-'everyone' group ${i}: ${groupName} as it has no members.`);
                await deleteGroup(i);
            } else {
                console.log(`Skipping non-'everyone' group ${i}: ${groupName} as it has members.`);
            }
            
            await waitForElementRemoved('.spinner', 10000);
            await delay(75);
        }
    }
}

// Function to delete a group
async function deleteGroup(groupIndex) {
    console.log(`Deleting group ID: ${groupIndex}`);
    let groupReopened = await reopenGroup(groupIndex);
    if (!groupReopened) {
        console.error(`Could not reopen group ${groupIndex}. Skipping deletion.`);
        return;
    }
    let deleteButton = await waitForElementAppear(`#collapse${groupIndex} > div > div > div.col-lg-12.pull-right > button`);
    if (deleteButton) {
        deleteButton.click();
        console.log(`Clicked delete button for group ${groupIndex}.`);
        await waitForElementRemoved('.spinner', 10000);
        await delay(75);

        let confirmButton = await waitForElementAppear('#deleteGroup');
        if (confirmButton) {
            await waitForElementRemoved('.spinner', 10000);
            await delay(75);
            confirmButton.click();
            console.log(`Clicked confirm button for group deletion.`);
        }
    } else {
        console.error(`Delete button not found for group ID ${groupIndex}`);
    }
}

// Function to handle 'everyone' group with members
async function handleEveryoneGroupWithMembers(groupIndex) {
    await delay(150);

    // Local function to check if the modal is visible
    async function waitForModalVisible(selector, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            const checkExist = setInterval(() => {
                const modal = document.querySelector(selector);
                if (modal && modal.style.display === 'block' && modal.style.visibility !== 'hidden') {
                    clearInterval(checkExist);
                    resolve(modal);
                } else if (Date.now() - startTime >= timeout) {
                    clearInterval(checkExist);
                    console.error(`Modal ${selector} did not become visible within ${timeout} ms`);
                    reject(new Error(`Modal ${selector} did not become visible within ${timeout} ms`));
                }
            }, 100);
        });
    }

    // Wait for the "+" button to open the modal
    let addButton = await waitForElementAppear('.panel-collapse.in .indicator.glyphicon.glyphicon-plus[data-original-title="Add Member"]', 20000);
    if (addButton) {
        console.log(`Found the add button for group ID ${groupIndex}. Attempting to open modal.`);
        addButton.click();
        console.log(`Clicked add members button for group ID ${groupIndex}.`);

        // Wait for modal to be fully visible
        try {
            await waitForModalVisible('#availableUsers', 5000);
            console.log(`Modal is visible for group ID ${groupIndex}.`);
        } catch (error) {
            console.error(`Stopping script because modal failed to open for group ID ${groupIndex}.`);
            throw error;
        }
    }
        
    // Small wait for checkboxes to appear
    const checkboxSelector = '#availableUsersForm > div.modal-body > ul > li > label > input[type=checkbox]';
    let checkboxes;
    try {
        await waitForElementRemoved('.spinner', 10000);
        
        // Wait for checkboxes with a longer timeout
        checkboxes = await waitForElementAppear(checkboxSelector, 500);
        
        if (checkboxes.length > 0) {
            console.log(`Checkboxes found for group ID ${groupIndex}. Clicking them...`);

            // Adding a small delay before interacting with checkboxes
            await delay(200);

            checkboxes.forEach(checkbox => {
                // Ensure the checkbox is not disabled and interactable
                if (checkbox && !checkbox.disabled) {
                    checkbox.scrollIntoView();  // Scroll into view if needed
                    checkbox.click();
                    console.log(`Clicked checkbox for group ID ${groupIndex}`);
                } else {
                    console.warn(`Checkbox not clickable or is disabled:`, checkbox);
                }
            });

            // Find and click the add members confirmation button
            let submitButton = document.querySelector('#availableUsersForm > div.modal-footer > button.btn.btn-primary');
            if (submitButton) {
                submitButton.click();
                console.log(`Clicked add members confirmation button for group ID ${groupIndex}. Modal will close automatically.`);
                return;
            } else {
                console.error(`Add Members button not found.`);
            }
        } else {
            console.log(`No checkboxes found for group ID ${groupIndex} (already full). Proceeding to close the modal.`);
        }
    } catch (error) {
        console.error(`Error finding or clicking checkboxes for group ID ${groupIndex}:`, error);
    }

    // Ensure the modal is closed manually if no members were added
    let closeModalButton = document.querySelector('button.close[data-dismiss="modal"]');
    if (closeModalButton) {
        closeModalButton.click();
        console.log(`Attempted to close modal for group ID ${groupIndex}`);
        
        let modalClosed = false;
        const maxRetries = 5;
        let retryCount = 0;
        while (!modalClosed && retryCount < maxRetries) {
            await delay(250);
            let modalElement = document.querySelector('#availableUsers');
            if (!modalElement || modalElement.style.display === 'none') {
                modalClosed = true;
                console.log(`Modal successfully closed for group ID ${groupIndex}`);
            } else {
                retryCount++;
                console.log(`Retrying to close modal... attempt ${retryCount}`);
                closeModalButton.click();
            }
        }
        
        if (!modalClosed) {
            console.error(`Failed to close modal after ${maxRetries} attempts.`);
        }
    } else {
        console.error(`Close button not found for group ID ${groupIndex}.`);
    }
}


// Main entry point
(async function () {
    try {
        console.log("Starting automation process...");
        await automateUserGroupManagement();  // Start the automation
        console.log("Automation process completed successfully.");
    } catch (error) {
        console.error("An error occurred during the automation process:", error);
    }
})();
"""

        # Inject the JavaScript into the webpage
        self.webview.page().runJavaScript(script)

    def on_page_load(self):
        """Handle page load completion."""
        logging.info("Page loaded successfully.")
        self.status_bar.showMessage(f"Page loaded at {get_timestamp()}")

    def run_script(self):
        """Start the script."""
        logging.info("Script started.")
        self.status_label.setText(f"Status: Running script... [{get_timestamp()}]")
        self.is_running = True
        if not self.webview.page().url().isEmpty():
            self.inject_javascript()  # Inject JavaScript if the page is loaded
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
    app = QApplication(sys.argv)  # Create the application
    window = MainWindow()         # Instantiate the main window
    window.show()                 # Show the main window
    sys.exit(app.exec_())         # Run the application event loop

if __name__ == "__main__":
    main()
