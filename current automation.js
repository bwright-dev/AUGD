let hasProcessedEveryoneGroupWithMembers = false;
let savestate = null; // Load the savestate from Python if available

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
