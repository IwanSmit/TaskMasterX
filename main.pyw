import tkinter as tk
import tkinter.ttk as ttk
import sqlite3
import datetime
from tkinter import simpledialog

# Create a SQLite database to store tasks and notes
conn = sqlite3.connect('tasks.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT,
        status TEXT,
        notes TEXT,
        date_reset TEXT
    )
''')
conn.commit()

# Function to reset tasks to 'Unfinished' on Monday
def reset_tasks():
    today = datetime.date.today()
    if today.weekday() == 0:  # Monday corresponds to 0 in the weekday() function
        cursor.execute("SELECT date_reset FROM tasks LIMIT 1")
        last_reset_date = cursor.fetchone()
        if not last_reset_date or last_reset_date[0] != str(today):
            cursor.execute("UPDATE tasks SET status='Todo', date_reset=? WHERE status='Completed'", (str(today),))
            conn.commit()

# Function to add a task with notes
def add_task():
    task_text = task_entry.get()
    notes_text = notes_entry.get("1.0", tk.END).strip()
    
    if task_text:
        cursor.execute("INSERT INTO tasks (task, status, notes) VALUES (?, 'Todo', ?)", (task_text, notes_text))
        conn.commit()
        refresh_todo_list()
        task_entry.delete(0, tk.END)
        notes_entry.delete("1.0", tk.END)

# Function to refresh the 'To Do' list
def refresh_todo_list():
    todo_list.delete(*todo_list.get_children())
    cursor.execute("SELECT * FROM tasks WHERE status='Todo'")
    for idx, row in enumerate(cursor.fetchall(), start=1):
        task_text = row[1]
        notes_text = row[3]
        todo_list.insert('', 'end', values=(f"{idx}. {task_text}", notes_text))

# Function to refresh the 'Completed Tasks' list
def refresh_completed_list():
    completed_list.delete(*completed_list.get_children())
    cursor.execute("SELECT * FROM tasks WHERE status='Completed'")
    for idx, row in enumerate(cursor.fetchall(), start=1):
        task_text = row[1]
        notes_text = row[3]
        completed_list.insert('', 'end', values=(f"{idx}. {task_text}", notes_text))

# Function to mark a task as finished
def mark_as_finished():
    selected_item = todo_list.selection()
    if selected_item:
        task = todo_list.item(selected_item, 'values')[0].split(".")[1].strip()  # Extract task name
        cursor.execute("UPDATE tasks SET status='Completed' WHERE task=?", (task,))
        conn.commit()
        refresh_todo_list()
        refresh_completed_list()

# Function to mark a task as unfinished
def mark_as_unfinished():
    selected_item = completed_list.selection()
    if selected_item:
        task = completed_list.item(selected_item, 'values')[0].split(".")[1].strip()  # Extract task name
        cursor.execute("UPDATE tasks SET status='Todo' WHERE task=?", (task,))
        conn.commit()
        refresh_completed_list()
        refresh_todo_list()

# Function to delete a task
def delete_task():
    selected_item = todo_list.selection() or completed_list.selection()
    if selected_item:
        task = todo_list.item(selected_item, 'values')[0].split(".")[1].strip() if todo_list.selection() else completed_list.item(selected_item, 'values')[0].split(".")[1].strip()  # Extract task name
        cursor.execute("DELETE FROM tasks WHERE task=?", (task,))
        conn.commit()
        refresh_todo_list()
        refresh_completed_list()

# Function to edit task notes
def edit_notes():
    selected_item = todo_list.selection() or completed_list.selection()
    if selected_item:
        task = todo_list.item(selected_item, 'values')[0].split(".")[1].strip() if todo_list.selection() else completed_list.item(selected_item, 'values')[0].split(".")[1].strip()  # Extract task name
        cursor.execute("SELECT notes FROM tasks WHERE task=?", (task,))
        result = cursor.fetchone()
        notes = result[0] if result is not None else ""
        edited_notes = simpledialog.askstring("Edit Notes", f"Edit notes for {task}: ", initialvalue=notes)
        if edited_notes is not None:
            cursor.execute("UPDATE tasks SET notes=? WHERE task=?", (edited_notes, task))
            conn.commit()
            refresh_todo_list()
            refresh_completed_list()

# Function to edit task name
def edit_task_name():
    selected_item = todo_list.selection()
    if selected_item:
        old_task = todo_list.item(selected_item, 'values')[0].split(".")[1].strip()  # Extract task name
        edited_task = simpledialog.askstring("Edit Task", f"Edit task name for {old_task}: ", initialvalue=old_task)
        if edited_task is not None:
            cursor.execute("UPDATE tasks SET task=? WHERE task=?", (edited_task, old_task))
            conn.commit()
            refresh_todo_list()
            refresh_completed_list()

# Create the main window
root = tk.Tk()
root.title("Task Manager")

# Create and configure the notebook
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# Create 'To Do' tab
todo_tab = ttk.Frame(notebook)
notebook.add(todo_tab, text="To Do")

# Create 'Completed Tasks' tab
completed_tab = ttk.Frame(notebook)
notebook.add(completed_tab, text="Completed Tasks")

# Create and configure the task listviews with a scrollbar
columns = ("Task", "Notes")
todo_frame = ttk.Frame(todo_tab)
todo_frame.pack(fill=tk.BOTH, expand=True)

completed_frame = ttk.Frame(completed_tab)
completed_frame.pack(fill=tk.BOTH, expand=True)

todo_list = ttk.Treeview(todo_frame, columns=columns, show="headings")
completed_list = ttk.Treeview(completed_frame, columns=columns, show="headings")

scrollbar_todo = ttk.Scrollbar(todo_frame, orient=tk.VERTICAL, command=todo_list.yview)
scrollbar_completed = ttk.Scrollbar(completed_frame, orient=tk.VERTICAL, command=completed_list.yview)

todo_list.configure(yscrollcommand=scrollbar_todo.set)
completed_list.configure(yscrollcommand=scrollbar_completed.set)

for column in columns:
    todo_list.heading(column, text=column)
    completed_list.heading(column, text=column)

todo_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
completed_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

scrollbar_todo.pack(fill=tk.Y, side=tk.RIGHT)
scrollbar_completed.pack(fill=tk.Y, side=tk.RIGHT)

# Create task entry field and notes entry field

task_label = tk.Label(root, text="Task:")
task_label.pack(fill=tk.BOTH, expand=True)

task_entry = tk.Entry(root)
task_entry.pack(fill=tk.BOTH, expand=True)

notes_label = tk.Label(root, text="Notes:")
notes_label.pack(fill=tk.BOTH, expand=True)

notes_entry = tk.Text(root, height=4)
notes_entry.pack(fill=tk.BOTH, expand=True)

# Create buttons
add_button = tk.Button(root, text="Add Task", command=add_task)
mark_finished_button = tk.Button(root, text="Mark as Finished", command=mark_as_finished)
mark_unfinished_button = tk.Button(root, text="Mark as Unfinished", command=mark_as_unfinished)
delete_button = tk.Button(root, text="Delete Task", command=delete_task)
edit_notes_button = tk.Button(root, text="Edit Notes", command=edit_notes)
edit_task_name_button = tk.Button(root, text="Edit Task Name", command=edit_task_name)

add_button.pack(fill=tk.BOTH, expand=True)
mark_finished_button.pack(fill=tk.BOTH, expand=True)
mark_unfinished_button.pack(fill=tk.BOTH, expand=True)
delete_button.pack(fill=tk.BOTH, expand=True)
edit_notes_button.pack(fill=tk.BOTH, expand=True)
edit_task_name_button.pack(fill=tk.BOTH, expand=True)

# Refresh task lists
refresh_todo_list()
refresh_completed_list()

# Reset tasks to 'Unfinished' on Mondays
reset_tasks()

# Start the GUI event loop
root.mainloop()