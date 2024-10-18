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
    console.log(`Inside automateUserGroupManagement function...`);
    let dropdown = await waitForElementAppear('#header_nav > div > div.row.top-menu > div > ul > li.profile > div > div.media-body.dropdown > a');
    console.log(`Dropdown element found:`, dropdown);
    dropdown.click();
    console.log(`Opened navigation dropdown.`);
    await delay(2500); // Wait for 2.5 seconds

    let userGroupsLink = await waitForElementAppear('#header_nav > div > div.row.top-menu > div > ul > li.profile > div > div.media-body.dropdown > ul > li:nth-child(5) > a');
    console.log(`User groups link found:`, userGroupsLink);
    userGroupsLink.click();
    console.log(`Navigated to User Groups page.`);
    await delay(2500); // Wait for 2.5 seconds

    await processAllCompanies();
}

async function processAllCompanies() {
    let hasAddedMembersToEveryoneGroup = false;
    console.log(`Inside processAllCompanies function...`);
    let companySelect = document.querySelector('#company_data');
    if (!companySelect) {
        console.error("Company select element not found!");
        return;
    }

    await delay(2500);
    let companies = document.querySelectorAll('#company_data option');
    console.log(`Found ${companies.length} companies in the hidden dropdown.`);
    await delay(2500); // Wait for 2.5 seconds

    for (let i = 0; i < companies.length; i++) {
        const option = companies[i];  // Current company option
        const companyName = option.textContent.trim();  // Company name
        const companyValue = option.value;  // Company value

        console.log(`Processing company (${i + 1}/${companies.length}): ${companyName}`);

        companySelect.value = companyValue;
        await delay(2500);
        companySelect.dispatchEvent(new Event('change'));

        await delay(2500);
        await waitForElementRemoved('#loadingIndicator', 10000);

        await processUserGroupsInCompany(i, hasAddedMembersToEveryoneGroup);
    }
}

async function processUserGroupsInCompany(companyIndex, hasAddedMembersToEveryoneGroup) {
    console.log(`Processing user groups for company index:`, companyIndex);

    let groups = document.querySelectorAll('a[role="button"][data-toggle="collapse"]');

    if (groups.length === 0) {
        console.log(`No user groups found for company index ${companyIndex}. Moving to the next company.`);
        await delay(1000);  // Optional: Add a delay before continuing
        return;
    }

    for (let i = 0; i < groups.length; i++) {
        let group = groups[i];
        group.click();
        let groupName = document.querySelector([id^="groupName${i}"]);
        if (groupName) {
            console.log(`Expanded group: ${groupName}`);
            await delay(2500);

            let memberCounter = document.querySelector(`#memberCounter${i}`);
            if (memberCounter && memberCounter.value === "0") {
                await deleteGroup(group);
            } else {
                // Check if it's not the 'everyone' group and has members, then skip it
                if (groupName !== 'everyone' && parseInt(memberCounter.value) > 0) {
                    console.log(`Group "${groupName}" has members and is not 'everyone', skipping.`);
                    continue; // Skip to the next group
                }

                // Handle 'everyone' group if necessary
                if (groupName === 'everyone' && !hasAddedMembersToEveryoneGroup) {
                    if (parseInt(memberCounter.value) > 0) {
                        await handleEveryoneGroupWithMembers(group);
                        hasAddedMembersToEveryoneGroup = true;  // Set flag to true after handling the first 'Everyone' group
                    }
                }
            }
        }
    }

    // After processing, delete all other 'Everyone' groups, regardless of members
    await deleteAllOtherEveryoneGroups();
}

async function deleteGroup(group) {
    console.log(`Deleting group: ${group.textContent.trim()}`);
    let deleteButton = await waitForElementAppear(`#collapse${i} > div > div > div.col-lg-12.pull-right > button`);
    deleteButton.click();
    console.log(`Clicked delete button.`);
    await delay(2500); // Wait for 2.5 seconds

    let confirmButton = await waitForElementAppear('#deleteGroup');
    confirmButton.click();
    console.log(`Clicked confirm button for deletion.`);
    await delay(2500); // Wait for 2.5 seconds
}

async function handleEveryoneGroupWithMembers(group) {
    console.log(`Handling 'Everyone' group with members: ${group.textContent.trim()}`);
    let addButton = document.querySelector("#directionext_result > a > span");
    addButton.click();
    console.log(`Clicked add members button.`);
    await delay(2500);

    let checkboxes = document.querySelectorAll('#availableUsersForm > div.modal-body > ul > li > label > input[type=checkbox]');
    checkboxes.forEach(checkbox => checkbox.click());
    console.log(`Clicked all checkboxes.`);

    let submitButton = document.querySelector('#availableUsersForm > div.modal-footer > button.btn.btn-primary');
    submitButton.click();
    console.log(`Clicked add members confirmation button.`);
    await delay(2500); // Wait for 2.5 seconds
}

async function deleteAllOtherEveryoneGroups() {
    console.log(`Deleting all other 'Everyone' groups regardless of members.`);
    let allGroups = document.querySelectorAll('.panel-collapse');
    for (let i = 0; i < allGroups.length; i++) {
        let groupNameElement = document.querySelector(`[id^="groupName${i}"]`);
        if (groupNameElement === 'everyone') {
            await deleteGroup(allGroups[i]);
        }
    }
}

(async function() {
    try {
        console.log(`Starting automation process...`;
        await automateUserGroupManagement();
        console.log(`Automation process completed successfully.");
    } catch (error) {
        console.error("An error occurred during the automation process:", error);
    }