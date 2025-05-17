import json
import os
import datetime
TODO_FILE = 'todo_list.json'
def load_todo_list():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, 'r') as f:
            return json.load(f)
    return []

def save_todo_list(todo_list):
    with open(TODO_FILE, 'w') as f:
        json.dump(todo_list, f)

def add_todo_item(item):
    todo_list = load_todo_list()
    todo_list.append({
        'task': item,
        'completed': False,
        'created_at': datetime.datetime.now().isoformat()
    })
    save_todo_list(todo_list)
    return f"Added '{item}' to your todo list."

def list_todo_items():
    todo_list = load_todo_list()
    if not todo_list:
        return "Your todo list is empty."
    
    response = "Here's your todo list:\n"
    for i, item in enumerate(todo_list, 1):
        status = "✓" if item['completed'] else "□"
        response += f"{i}. [{status}] {item['task']}\n"
    return response

def complete_todo_item(index):
    todo_list = load_todo_list()
    try:
        index = int(index) - 1
        if 0 <= index < len(todo_list):
            todo_list[index]['completed'] = True
            save_todo_list(todo_list)
            return f"Marked '{todo_list[index]['task']}' as completed."
        return "Invalid todo item number."
    except ValueError:
        return "Please provide a valid number."

def delete_todo_item(index):
    todo_list = load_todo_list()
    try:
        index = int(index) - 1
        if 0 <= index < len(todo_list):
            deleted_item = todo_list.pop(index)
            save_todo_list(todo_list)
            return f"Deleted '{deleted_item['task']}' from your todo list."
        return "Invalid todo item number."
    except ValueError:
        return "Please provide a valid number."