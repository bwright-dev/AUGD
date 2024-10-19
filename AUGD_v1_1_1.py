import sys
import os
os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"
import logging
import webbrowser
from logging.handlers import RotatingFileHandler
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton,
    QLabel, QWidget, QHBoxLayout, QStatusBar
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, pyqtSlot, QObject
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from datetime import datetime
import json

# Define a class to handle interaction between Python and JavaScript
class WebBridge(QObject):
    @pyqtSlot(int, int)
    def saveState(self, company_index, group_index):
        """Method called from JavaScript to save state to a file."""
        logging.info("Entering saveState function in Python.")
        logging.info(f"Received company_index={company_index}, group_index={group_index}.")

        state = {
            'company_index': company_index,
            'group_index': group_index
        }

        # Custom path for saving the state file
        save_file_path = os.path.join(os.path.expanduser("~"), "Documents", "AUGD Logs", "savestate.txt")
        logging.info(f"Saving state to {save_file_path}.")
        os.makedirs(os.path.dirname(save_file_path), exist_ok=True)  # Ensure the directory exists

        try:
            # Save the state to a JSON file
            with open(save_file_path, 'w') as f:
                json.dump(state, f)
            logging.info(f"State successfully saved: company_index={company_index}, group_index={group_index}.")
        except Exception as e:
            logging.error(f"Error saving state: {str(e)}")

# Set up logging folder and file
log_folder = os.path.join(os.path.expanduser("~"), "Documents", "AUGD Logs")
os.makedirs(log_folder, exist_ok=True)
log_file_path = os.path.join(log_folder, "automation_log.txt")

# Set up log rotation (5MB per file, 2 backups)
log_handler = RotatingFileHandler(log_file_path, maxBytes=5 * 1024 * 1024, backupCount=2)
logging.basicConfig(handlers=[log_handler], level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Application started with detailed logging.")

# Get the current timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Custom class to capture JavaScript console messages
class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        log_message = f"JavaScript Console - Level: {level}, Message: {message}, Line: {line}, Source: {source}"
        logging.info(log_message)

        if level == 3:  # Error level
            logging.error(f"JS Error [{source}:{line}]: {message}")
        elif level == 2:  # Warning level
            logging.warning(f"JS Warning [{source}:{line}]: {message}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
    # Set up the main window
        self.setWindowTitle("AUGD - Automated User Group Deletion")
        self.setGeometry(100, 100, 1200, 800)

        # Set up the central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Set up the QWebEngineView
        self.webview = QWebEngineView(self)
        self.webview.setFixedSize(1200, 800)
        self.layout.addWidget(self.webview)  # Add the WebView to the layout

        # Set up QWebChannel
        self.web_channel = QWebChannel(self.webview.page())  # Attach to the web page
        self.bridge = WebBridge()  # The Python object to be exposed to JavaScript
        self.web_channel.registerObject("pyqtBoundObject", self.bridge)
        self.webview.page().setWebChannel(self.web_channel)  # Attach channel to the web page

        # Load target URL
        self.webview.setUrl(QUrl("https://cp.hivepbx.com"))
        
        # Inject QWebChannel setup JS immediately when the page is loaded
        self.webview.loadFinished.connect(self.inject_qwebchannel_js)

        # Add buttons and status bar
        self.setup_ui()

        # Status bar and state tracking
        self.is_running = False
        self.company_index = 0
        self.load_state()

    def setup_ui(self):
        # Add horizontal layout for buttons
        hbox = QHBoxLayout()

        # Run Script button
        self.run_button = QPushButton("Run Script", self)
        self.run_button.clicked.connect(self.run_script)
        hbox.addWidget(self.run_button)

        # Stop Script button
        self.stop_button = QPushButton("Stop Script", self)
        self.stop_button.clicked.connect(self.stop_script)
        hbox.addWidget(self.stop_button)

        # Restart Button to restart from last saved state
        self.restart_button = QPushButton("Restart Script", self)
        self.restart_button.clicked.connect(self.restart_script)
        hbox.addWidget(self.restart_button)

        # Status label
        self.status_label = QLabel(f"Status: Waiting for user action... [{get_timestamp()}]", self)
        hbox.addWidget(self.status_label)

        # Add layout to the main layout
        self.layout.addLayout(hbox)

        # Add DevTools button
        dev_tools_button = QPushButton("Open DevTools", self)
        dev_tools_button.clicked.connect(self.open_remote_dev_tools)
        self.layout.addWidget(dev_tools_button)

        # Shortcut for opening DevTools (F12)
        self.devtools_shortcut = QShortcut(QKeySequence("F12"), self)
        self.devtools_shortcut.activated.connect(self.open_remote_dev_tools)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def inject_qwebchannel_js(self):
        """Inject JavaScript to set up the QWebChannel when the page loads."""
        js_code = """
        var script = document.createElement('script');
        script.src = 'qrc:///qtwebchannel/qwebchannel.js';  // Correct resource path for qwebchannel.js
        script.onload = function() {
            console.log('QWebChannel JS loaded.');
            
            // Check if qt and qt.webChannelTransport are defined
            if (typeof qt !== 'undefined' && qt.webChannelTransport) {
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    window.pyqtBoundObject = channel.objects.pyqtBoundObject;
                    console.log('QWebChannel initialized and pyqtBoundObject available.');
                });
            } else {
                console.error('qt.webChannelTransport is not available.');
            }
        };
        script.onerror = function() {
            console.error('Failed to load QWebChannel JS.');
        };
        document.head.appendChild(script);
        """
        self.webview.page().runJavaScript(js_code)

    def open_remote_dev_tools(self):
        """Opens the Chrome DevTools interface via the remote debugging URL."""
        dev_tools_url = "http://localhost:9222"
        webbrowser.open(dev_tools_url)

    def inject_javascript(self, state=None):
        """Inject JavaScript and set up interaction with Python."""
        logging.info("Injecting JavaScript into the web page.")
        state_js = json.dumps(state) if state else 'null'
        savestate_script = f"let savestate = {state_js};"
        logging.info(f"Injecting savestate: {savestate_script}")

        # JavaScript code to interact with Python
        script = """
            new QWebChannel(qt.webChannelTransport, function(channel) {
        window.pyqtBoundObject = channel.objects.pyqtBoundObject;
        console.log('QWebChannel initialized.');

        if (window.pyqtBoundObject) {
            console.log("pyqtBoundObject is available and ready.");
        } else {
            console.error("pyqtBoundObject is NOT available. Web channel may not be set up.");
        }

        async function saveStateToPython(companyIndex, groupIndex) {
            console.log(`saveStateToPython called with companyIndex=${companyIndex}, groupIndex=${groupIndex}`);
            try {
                window.pyqtBoundObject.saveState(companyIndex, groupIndex);
                console.log(`saveState called successfully with companyIndex=${companyIndex}, groupIndex=${groupIndex}`);
            } catch (error) {
                console.error(`Error calling saveState: ${error.message}`);
            }
        }

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
                        console.error(`Element {selector} did not appear within {timeout} ms`);
                        reject(new Error(`Element {selector} did not appear within {timeout} ms`));
                    }
                }, 100); 
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

async function reopenGroup(groupIndex) {
    let clickableElement = document.querySelector(`#groupID${groupIndex} > div.panel-heading > h4 > a`);
    if (clickableElement) {
        clickableElement.click();
        console.log(`Reopened group ID ${groupIndex}`);
        await waitForElementRemoved('#loadingIndicator', 10000);
        await delay(75);
    } else {
        console.error(`Could not find clickable element for group ID ${groupIndex}.`);
        return false;
    }
    return true;
}

async function saveStateToPython(companyIndex, groupIndex) {
    // Call Python to save state to disk
    window.pyqtBoundObject.saveState(companyIndex, groupIndex);
}

async function automateUserGroupManagement() {
    console.log(`Inside automateUserGroupManagement function...`);
    let dropdown = await waitForElementAppear('#header_nav > div > div.row.top-menu > div > ul > li.profile > div > div.media-body.dropdown > a');
    console.log(`Dropdown element found:`, dropdown);
    dropdown.click();
    console.log(`Opened navigation dropdown.`);
    await waitForElementRemoved('#loadingIndicator', 10000);
    await delay(75);

    let userGroupsLink = await waitForElementAppear('#header_nav > div > div.row.top-menu > div > ul > li.profile > div > div.media-body.dropdown > ul > li:nth-child(5) > a');
    console.log(`User groups link found:`, userGroupsLink);
    userGroupsLink.click();
    console.log(`Navigated to User Groups page.`);
    await waitForElementRemoved('#loadingIndicator', 10000);
    await delay(75);

    await processAllCompanies();
}

async function processAllCompanies() {
    console.log(`Inside processAllCompanies function...`);
    let companySelect = document.querySelector('#company_data');
    if (!companySelect) {
        console.error("Company select element not found!");
        return;
    }
    await waitForElementRemoved('#loadingIndicator', 10000);
    await delay(75);
    let companies = document.querySelectorAll('#company_data option');
    console.log(`Found ${companies.length} companies in the hidden dropdown.`);
    await waitForElementRemoved('#loadingIndicator', 10000);
    await delay(75);

    let currentCompanyIndex = savestate ? savestate.companyIndex : 0; // Start from saved state or 0

    for (let i = currentCompanyIndex; i < companies.length; i++) {
        const option = companies[i];
        const companyName = option.textContent.trim();
        const companyValue = option.value;

        console.log(`Processing company (${i + 1}/${companies.length}): ${companyName}`);

        // Reset the flag when starting a new company
        hasProcessedEveryoneGroupWithMembers = false;
        console.log(`Flag set: hasProcessedEveryoneGroupWithMembers = false for company ${companyName}`);

        companySelect.value = companyValue;
        await waitForElementRemoved('#loadingIndicator', 10000);
        await delay(75);
        companySelect.dispatchEvent(new Event('change'));

        await waitForElementRemoved('#loadingIndicator', 10000);
        await delay(75);
        await processUserGroupsInCompany(i, companyName);

        // Save state every 5 companies
        if (i % 5 === 0) {
            await saveStateToPython(i, 0);  // Save company and group index
        }

        // Reload after 30 companies
        if (i % 30 === 0 && i !== 0) {
            console.log('Reloading page to prevent performance issues...');
            location.reload();  // Reload the page to reset JS execution
            return;
        }
    }
}

async function processUserGroupsInCompany(companyIndex, companyName) {
    console.log(`Processing user groups for company index: ${companyIndex}`);
    await waitForElementRemoved('#loadingIndicator', 10000);
    await delay(2500);

    let groups = document.querySelectorAll('.panel-collapse');
    if (groups.length === 0) {
        console.log(`No user groups found for company index ${companyIndex}. Moving to the next company.`);
        return;
    }

    let currentGroupIndex = savestate ? savestate.groupIndex : 0; // Start from saved group state

    for (let i = currentGroupIndex; i < groups.length; i++) {
        let group = groups[i];
        let groupReopened = await reopenGroup(i);
        if (!groupReopened) {
            console.error(`Could not reopen group ${i}. Skipping.`);
            continue;
        }

        let groupNameElement = document.querySelector(`#groupNameLabel${i}`);
        let groupName = groupNameElement ? groupNameElement.innerText.trim() : null;
        let memberCounter = document.querySelector(`#memberCounter${i}`);

        if (groupName === 'everyone') {
            if (parseInt(memberCounter.value) > 0) {
                if (!hasProcessedEveryoneGroupWithMembers) {
                    console.log(`Processing 'everyone' group ${i} that already has members.`);
                    await handleEveryoneGroupWithMembers(i);
                    hasProcessedEveryoneGroupWithMembers = true;
                    console.log(`Flag set: hasProcessedEveryoneGroupWithMembers = true for group ID ${i}, company: ${companyName}`);
                } else {
                    console.log(`Skipping modal for 'everyone' group ${i}, already processed another 'everyone' group.`);
                }
            } else {
                console.log(`Processing 'everyone' group ${i} with no members.`);
                await deleteGroup(i);
            }
        } else {
            console.log(`Processing non-'everyone' group ${i}: ${groupName}`);
            await waitForElementRemoved('#loadingIndicator', 10000);
            await delay(75);
        }
    }
}

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
        await waitForElementRemoved('#loadingIndicator', 10000);
        await delay(75);

        let confirmButton = await waitForElementAppear('#deleteGroup');
        if (confirmButton) {
            await waitForElementRemoved('#loadingIndicator', 10000);
            await delay(75);
            confirmButton.click();
            console.log(`Clicked confirm button for group deletion.`);
        }
    } else {
        console.error(`Delete button not found for group ID ${groupIndex}`);
    }
}

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
            }, 100); // Check every 100 ms
        });
    }

    // Ensure the group is expanded before proceeding
    let groupCollapse = document.querySelector(`#collapse${groupIndex}`);
    if (!groupCollapse.classList.contains('in')) {
        console.log(`Group ID ${groupIndex} is collapsed. Reopening...`);
        await reopenGroup(groupIndex);
    }

    // Wait for the "+" button to open the modal (20-second timeout)
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
            throw error;  // Stop script execution for debugging purposes
        }

        // Small wait for checkboxes to appear
        const checkboxSelector = '#availableUsersForm > div.modal-body > ul > li > label > input[type=checkbox]';
        let checkboxes;
        try {
            checkboxes = await waitForElementAppear(checkboxSelector, 1000);
            console.log(`Checkboxes found for group ID ${groupIndex}. Clicking them...`);
            checkboxes.forEach(checkbox => checkbox.click());

            let submitButton = document.querySelector('#availableUsersForm > div.modal-footer > button.btn.btn-primary');
            if (submitButton) {
                submitButton.click();
                console.log(`Clicked add members confirmation button for group ID ${groupIndex}. Modal will close automatically.`);
                return;
            } else {
                console.error(`Add Members button not found.`);
            }
        } catch (error) {
            console.log(`No checkboxes found for group ID ${groupIndex} (already full). Proceeding to close the modal.`);
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
                await delay(750);
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
        }
    } else {
        console.error(`Add button not found for group ID ${groupIndex}.`);
    }
    await waitForElementRemoved('#loadingIndicator', 10000);
    await delay(75);
}

(async function () {
    try {
        console.log("Starting automation process...");
        await automateUserGroupManagement();
        console.log("Automation process completed successfully.");
    } catch (error) {
        console.error("An error occurred during the automation process:", error);
    }
})();
    saveStateToPython(1, 0);
    """

        logging.info("Running JavaScript in the web page.")
        self.webview.page().runJavaScript(savestate_script)
        self.webview.page().runJavaScript(script)

    def run_script(self):
        """Start the script."""
        logging.info("Script started.")
        self.is_running = True
        self.inject_javascript()

    def restart_script(self):
        """Restart script from last saved state."""
        logging.info("Script restarted from saved state.")
        self.is_running = True
        state = self.load_state()
        self.inject_javascript(state)

    def stop_script(self):
        """Stop the running script."""
        logging.info("Script stopped by user.")
        self.is_running = False
        self.webview.page().runJavaScript("window.stop = true;")
    
    def save_state(self, company_index):
        """Save current progress."""
        state = {
            'company_index': company_index,
            'is_running': self.is_running,
        }
        with open('savestate.txt', 'w') as f:
            json.dump(state, f)
        logging.info(f"State saved at company index {company_index}.")

    def load_state(self):
        """Load the last saved state from the custom location in Documents/AUGD Logs."""
        # Custom path for loading the state file
        save_file_path = os.path.join(os.path.expanduser("~"), "Documents", "AUGD Logs", "savestate.txt")
        
        if os.path.exists(save_file_path):
            with open(save_file_path, 'r') as f:
                state = json.load(f)
            self.company_index = state.get('company_index', 0)
            logging.info(f"Resuming from company index {self.company_index} from {save_file_path}.")
            return state
        else:
            logging.info("No saved state found. Starting fresh.")
            return None

    def on_page_load(self):
        """Handle page load completion."""
        logging.info("Page loaded successfully.")
        self.status_bar.showMessage(f"Page loaded at {get_timestamp()}")

@pyqtSlot()
def on_script_finished(self):
    """Handle script completion."""
    if self.is_running:
        logging.info("Script completed successfully.")
        timestamp = get_timestamp()
        os.rename('savestate.txt', f'savestate_completed_{timestamp}.txt')
        self.status_label.setText(f"Script completed. State saved as savestate_completed_{timestamp}.txt")
    else:
        logging.info("Script stopped early.")

# Main entry point
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()