# AUGD v1.1

### Overview

**AUGD (Automated User Group Deletion)** is a Python-based automation framework designed to facilitate the identification and removal of inactive or redundant user groups within enterprise-level systems. This tool leverages a robust combination of algorithmic analysis and a user-driven graphical interface to optimize system performance and ensure effective management of large-scale user environments.

Version 1.1 introduces augmented capabilities with a focus on scalability, performance optimization, and refined user interaction mechanisms.

---

## Features

### 1. Automated User Group Deletion
Implements advanced algorithms capable of identifying and removing inactive or redundant user groups, thereby reducing overhead and improving system efficiency.

### 2. User-Guided Customization Tools
Enables comprehensive user group management customization through flexible parameter settings, providing precise control over deletion criteria and process automation.

### 3. Graphical User Interface (GUI)
The GUI, developed using **PyQt5**, allows for intuitive and visual interaction with the system, supporting real-time adjustments and command initiation.

### 4. Comprehensive Logging and Tracking
- Utilizes a rotating log file system with a capacity of **5MB per file** and up to **two backup logs**, ensuring efficient log management and data retention.
- Logging data is stored in the user's **"Documents/AUGD Logs"** directory, featuring comprehensive audit trails for all script actions, including timestamps and action-specific metadata.

---

## Version 1.1 Enhancements

- **Improved User Group Analysis**: More sophisticated algorithms for enhanced precision in identifying redundant user groups.
- **Optimized GUI**: A smoother user experience, including asynchronous handling of user inputs to maintain interface responsiveness.
- **Bug Fixes & Performance Enhancements**: Improved runtime efficiency and the overall robustness of the tool.

---

## Logic Flow

### 1. Script Initialization

- **Goal**: Initialize the automation framework, configure operational flags, and establish the logging infrastructure.
- **Status**: Fully implemented. Initialization includes setting flags such as `hasAddedMembersToEveryoneGroup` and initiating the logging subsystem.

### 2. Navigate to the User Groups Page

- **Goal**: Programmatically navigate to the User Groups page within the management console.
- **Selectors**:
  - Navigation dropdown: `#header_nav > div > div.row.top-menu > div > ul > li.profile > div > div.media-body.dropdown > a`
  - User Groups link: `#header_nav > div > div.row.top-menu > div > ul > li.profile > div > div.media-body.dropdown > ul > li:nth-child(5) > a`
- **Status**: Implemented via the `automateUserGroupManagement` function with error handling and retries. 

### 3. Identify the First and Last Company

- **Goal**: Determine the first and last available companies from the dropdown list.
- **Selectors**:
  - Company dropdown: `#company_data`
- **Status**: Fully implemented via the `processAllCompanies` function.

### 4. Iterate Over Companies

- **Goal**: Sequentially process companies located between the first and last identified entries.
- **Status**: Implemented using throttling to prevent system lock-ups. Detailed log entries document each iteration.

### 5. Iterate Over User Groups

- **Goal**: Iterate through all user groups within a selected company.
- **Selectors**:
  - Group collapse element: `#groupID${i} > div.panel-heading > h4 > a`
- **Status**: Implemented via `processUserGroupsInCompany`. Each group’s status is logged.

### 6. Check Membership Status

- **Goal**: Assess each user group based on the number of members and group type (e.g., 'everyone').
- **Selectors**:
  - Member counter: `#memberCounter${i}`
  - Group name: `#groupNameLabel${i}`
- **Status**: Implemented. Groups with zero members are flagged for deletion, while ‘everyone’ groups are handled conditionally.

### 7. Process the 'Everyone' Group

- **Goal**: Add users to one 'Everyone' group per company.
- **Selectors**:
  - Add members button: `#directionext_result > a`
  - Checkboxes in modal: `#availableUsersForm > div.modal-body > ul > li > label > input[type=checkbox]`
  - Confirm button: `#availableUsersForm > div.modal-footer > button.btn.btn-primary`
  - Modal close button: `#availableUsersForm > div.modal-header > button`
- **Status**: Implemented with retries for modal interactions in the `handleEveryoneGroupWithMembers` function.

### 8. Wait for Group Deletion

- **Goal**: Ensure user groups marked for deletion are completely removed from the DOM.
- **Selectors**:
  - Group collapse element for deletion: `#collapse${i}`
- **Status**: Implemented with an explicit wait strategy to confirm deletion.

### 9. Delete Remaining 'Everyone' Groups

- **Goal**: Delete empty 'everyone' groups, excluding the one with users added.
- **Status**: Implemented and documented with comprehensive logging.

### 10. Delete Non-'Everyone' Groups

- **Goal**: Remove all non-'everyone' user groups that have zero members.
- **Status**: Implemented. Each deletion is logged for audit purposes.

### 11. Script Completion

- **Goal**: Complete the script after all user groups across all companies have been processed.
- **Status**: Implemented. The script concludes with a completion message and logs a summary of all operations.

---

## Installation

1. Download the latest release from the [Releases page](https://github.com/bwright-dev/AUGD/releases).

---

## Usage

- After installation, run the executable (`AUGD_v1_1.exe`) to initiate the user group management process.
- Interact with the **PyQt5 GUI** to guide the automated user group deletion process.

---

## Logging

AUGD maintains detailed logs in the **"Documents/AUGD Logs"** folder. Logs include:
- Timestamps
- Actions performed
- Metadata for auditing and troubleshooting.

---

## Contributing

We encourage contributions that further enhance AUGD’s functionality. Feel free to open issues or submit pull requests for:
- New features
- Optimizations
- Bug fixes

---

## License

This project is licensed under the **MIT License**. See the LICENSE file for more information.

---

## Contact

For questions or suggestions, please reach out to [@bwright-dev](https://github.com/bwright-dev).

---

Thank you for using AUGD! Your feedback is instrumental in driving continuous improvement.
