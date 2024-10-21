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
    if (clickableElement && clickableElement.textContent.trim() !== "") {
        clickableElement.click();
        console.log(`Reopened group ID ${groupIndex}`);
        await waitForElementRemoved('#loadingIndicator', 10000);
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
    await waitForElementRemoved('#loadingIndicator', 10000);
    await delay(75);

    let userGroupsLink = await waitForElementAppear('#header_nav > div > div.row.top-menu > div > ul > li.profile > div > div.media-body.dropdown > ul > li:nth-child(5) > a');
    console.log(`User groups link found:`, userGroupsLink);
    userGroupsLink.click();  // Navigate to User Groups page
    console.log(`Navigated to User Groups page.`);
    await waitForElementRemoved('#loadingIndicator', 10000);
    await delay(75);

    await processAllCompanies();  // Start processing companies
}

// Function to process all companies
async function processAllCompanies() {
    console.log(`Inside processAllCompanies function...`);
    let companySelect = document.querySelector('#company_data');
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
        await waitForElementRemoved('#loadingIndicator', 10000);
        await delay(75);
        companySelect.dispatchEvent(new Event('change'));  // Trigger change event

        await waitForElementRemoved('#loadingIndicator', 10000);
        await delay(75);
        await processUserGroupsInCompany(i, companyName);  // Process user groups
    }
    console.log("Company processing loop finished.");
}

// Function to process user groups within a company
async function processUserGroupsInCompany(companyIndex, companyName) {
    console.log(`Processing user groups for company index: ${companyIndex}`);
    await waitForElementRemoved('#loadingIndicator', 10000);

    let groups = document.querySelectorAll('.panel-collapse');
        await waitForElementRemoved('#loadingIndicator', 10000);
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
            
            await waitForElementRemoved('#loadingIndicator', 10000);
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

    // Ensure the group is expanded before proceeding
    let groupCollapse = document.querySelector(`#collapse${groupIndex}`);
    if (!groupCollapse.classList.contains('in')) {
        console.log(`Group ID ${groupIndex} is collapsed. Reopening...`);
        await reopenGroup(groupIndex);
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
        await waitForElementRemoved('#loadingIndicator', 10000);
        
        // Wait for checkboxes with a longer timeout
        checkboxes = await waitForElementAppear(checkboxSelector, 5000);
        
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