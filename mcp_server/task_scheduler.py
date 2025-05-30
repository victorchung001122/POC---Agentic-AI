from mcp.server.fastmcp import FastMCP
import json
import os
from datetime import datetime


mcp = FastMCP("task scheduler")

@mcp.tool()
def task_scheduler(task: str, loan_amount: str, purpose: str, urgency: str = "low", user_id: str = None, system: str = "loan process system"):
    """ This function is used to schedule a task for the loan process. It requires the following parameters:
    
    - task: The task to be scheduled (in string).
    - loan_amount: The amount of loan requested (in string).
    - purpose: The purpose of the loan (in string).
    - urgency: The urgency of the task (in string, default is "low").
    - user_id: The user ID (in string, default is none, you can provide the user name instead).
    - system: The system from which the task originates (in string, default is "loan process system").
    
    you need to provide the task (in string), loan amount (in string), purpose , urgency (should be provided by the user, will be set to low by default), user_id (user name plus loan amount as user_id) and what agent or system does the task comes from."""
    # Get the current timestamp
    timestamp = datetime.now().isoformat()
    
    base_path = os.path.dirname(__file__)  # Get the directory of the current script (mcp_server)
    file_name = os.path.join(base_path, "..", "task_scheduler", "task.json")
    
    # Create a message dictionary
    message = {
        'task': task,
        "loan amount" : loan_amount,
        'purpose': purpose,
        'urgency': urgency,
        'user_id': user_id,
        'system': system,
        'timestamp': timestamp
    }
    
    # Ensure the file exists and is not empty
    if not os.path.exists(file_name) or os.path.getsize(file_name) == 0:
        data = []  # Initialize with an empty list if file doesn't exist or is empty
        with open(file_name, 'w') as file:  # Create the file or clear it if it's corrupt
            json.dump(data, file)
    else:
        with open(file_name, 'r') as file:
            data = json.load(file)

    # Append the new message
    data.append(message)

    # Save the updated data back to the JSON file
    try:
        with open(file_name, 'w') as file:
            json.dump(data, file, indent=4)
        return {"status": "success", "message": "Task scheduled successfully."}
    except Exception as e:
        print(f"Error writing to file: {e}")
        return {"status": "error", "message": "Failed to write to file."}
        
    

if __name__ == "__main__":
    mcp.run(transport= "stdio")
    