**INF1103 Team 6**  
**AI SIT Helpdesk Ticket Triage System**  
[https://github.com/mbszmn/INF1103-Team-6.git](https://github.com/mbszmn/INF1103-Team-6.git) 

**1\. Problem Statement and Target Users**

- SIT helpdesk receives many support tickets describing different technical problems  
- Users may provide unclear descriptions such as “internet not working” or “computer very slow”  
- IT staff must manually read each ticket, determine the issue category, urgency, and which support team should handle it.  
- Important incidents may be delayed because they are mixed with minor problems.  
- Intended Users:   
  - SIT helpdesk staff  
  - Schools/companies with internal IT support  
  - Employees/students submitting technical issues

**2\. User Inputs**

- What information or data will users provide to the system?  
  - Type of issue they are encountering  
  - Steps they have taken to solve the issue before coming to the IT helpdesk  
  - Name/Username  
  - The device they are having an issue on   
  - Self-assessed priority level (is it urgent for them?)  
  - Ticket title  
  - Department / Role  
  - Screenshot or error message that may provide additional information

**3\. Use of AI**

- How will AI be utilized within the application?  
  Categorizes the different technical difficulties: basic (can be solved with automated responses) and more advanced problems (maybe a way to direct users to tech support), e.g., Network / Hardware / Software / Account / Security  
  Basic Identification (sorts out proper requests for identified individuals, removes spam/invalid requests)     
    
- What outputs, insights, or recommendations will the AI generate from the user inputs?  
    
  Outputs: Automated solution responses, basic troubleshooting/recommended solutions  
- Determines severity/priority  
- Summarises long problem descriptions  
- Identifies the likely affected system  
- Determines whether escalation may be required  
  

**4\. Business Rules**

| Data Manager | Each ticket requires a unique ticket ID Closed tickets cannot be modified unless reopened. Original ticket \+ AI output are stored and saved consistently in a JSON/CSV file. |
| :---- | :---- |
| Logic Manager | Priority can only be: Low Medium High Critical Security-related tickets are automatically marked for escalation. Critical tickets are automatically placed at the top of the queue. |
| AI Manager | Every valid ticket must successfully pass through the AI API. AI responses must contain all required JSON fields before being accepted. Invalid AI responses are rejected/retried rather than directly stored. |
| IO Manager | Required user input cannot be empty Category must belong to an approved list. Every ticket must contain a description before processing. |

- how is it different from existing solutions? (eg. chatbots, chatgpt etc)  
- 

