import tkinter as tk
import tkinter.ttk as ttk
import sqlite3
import datetime
from tkinter import simpledialog

# Constants for table columns
ID_COLUMN = 'id'
TASK_COLUMN = 'task'
STATUS_COLUMN = 'status'
NOTES_COLUMN = 'notes'
DATE_RESET_COLUMN = 'date_reset'

class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("TaskMasterX")

        # Create and configure the notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create 'To Do' tab
        self.todo_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.todo_tab, text="To Do")

        # Create 'Completed Tasks' tab
        self.completed_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.completed_tab, text="Completed Tasks")

        # Create and configure the task listviews with a scrollbar
        self.columns = ("Task", "Notes")
        self.todo_frame = ttk.Frame(self.todo_tab)
        self.todo_frame.pack(fill=tk.BOTH, expand=True)

        self.completed_frame = ttk.Frame(self.completed_tab)
        self.completed_frame.pack(fill=tk.BOTH, expand=True)

        self.todo_list = ttk.Treeview(self.todo_frame, columns=self.columns, show="headings")
        self.completed_list = ttk.Treeview(self.completed_frame, columns=self.columns, show="headings")

        self.scrollbar_todo = ttk.Scrollbar(self.todo_frame, orient=tk.VERTICAL, command=self.todo_list.yview)
        self.scrollbar_completed = ttk.Scrollbar(self.completed_frame, orient=tk.VERTICAL, command=self.completed_list.yview)

        self.todo_list.configure(yscrollcommand=self.scrollbar_todo.set)
        self.completed_list.configure(yscrollcommand=self.scrollbar_completed.set)

        for column in self.columns:
            self.todo_list.heading(column, text=column)
            self.completed_list.heading(column, text=column)

        self.todo_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.completed_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.scrollbar_todo.pack(fill=tk.Y, side=tk.RIGHT)
        self.scrollbar_completed.pack(fill=tk.Y, side=tk.RIGHT)

        # Create task entry field and notes entry field
        self.task_label = tk.Label(self.root, text="Task:")
        self.task_label.pack(fill=tk.BOTH, expand=True)

        self.task_entry = tk.Entry(self.root)
        self.task_entry.pack(fill=tk.BOTH, expand=True)

        self.notes_label = tk.Label(self.root, text="Notes:")
        self.notes_label.pack(fill=tk.BOTH, expand=True)

        self.notes_entry = tk.Text(self.root, height=4)
        self.notes_entry.pack(fill=tk.BOTH, expand=True)

        # Create buttons
        self.add_button = tk.Button(self.root, text="Add Task", command=self.add_task)
        self.mark_finished_button = tk.Button(self.root, text="Mark as Finished", command=self.mark_as_finished)
        self.mark_unfinished_button = tk.Button(self.root, text="Mark as Unfinished", command=self.mark_as_unfinished)
        self.delete_button = tk.Button(self.root, text="Delete Task", command=self.delete_task)
        self.edit_notes_button = tk.Button(self.root, text="Edit Notes", command=self.edit_notes)
        self.edit_task_name_button = tk.Button(self.root, text="Edit Task Name", command=self.edit_task_name)

        self.add_button.pack(fill=tk.BOTH, expand=True)
        self.mark_finished_button.pack(fill=tk.BOTH, expand=True)
        self.mark_unfinished_button.pack(fill=tk.BOTH, expand=True)
        self.delete_button.pack(fill=tk.BOTH, expand=True)
        self.edit_notes_button.pack(fill=tk.BOTH, expand=True)
        self.edit_task_name_button.pack(fill=tk.BOTH, expand=True)

        # Create context menus for editing notes and task name
        self.context_menu_task = tk.Menu(self.root, tearoff=0)
        self.context_menu_task.add_command(label="Edit Task Name", command=self.edit_task_name)

        self.context_menu_notes = tk.Menu(self.root, tearoff=0)
        self.context_menu_notes.add_command(label="Edit Notes", command=self.edit_notes)

        # Bind the context menus to the task and notes columns separately
        self.todo_list.bind("<Button-3>", self.show_context_menu_task)
        self.todo_list.bind("<Button-3>", self.show_context_menu_notes, add=True)

        # Initialize database
        self.conn = sqlite3.connect('tasks.db')
        self.db_cursor = self.conn.cursor()
        self.create_table_if_not_exists()

        # Refresh task lists
        self.refresh_todo_list()
        self.refresh_completed_list()

        # Reset tasks to 'Unfinished' on Mondays and refresh the lists
        self.reset_tasks()

        # Start the GUI event loop
        self.root.mainloop()

    def create_table_if_not_exists(self):
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                {} INTEGER PRIMARY KEY AUTOINCREMENT,
                {} TEXT,
                {} TEXT,
                {} TEXT,
                {} TEXT
            )
        '''.format(ID_COLUMN, TASK_COLUMN, STATUS_COLUMN, NOTES_COLUMN, DATE_RESET_COLUMN))
        self.conn.commit()

    def reset_tasks(self):
        today = datetime.date.today()
        if today.weekday() == 0:  # Monday corresponds to 0 in the weekday() function
            self.db_cursor.execute("SELECT {} FROM tasks LIMIT 1".format(DATE_RESET_COLUMN))
            last_reset_date = self.db_cursor.fetchone()
            if not last_reset_date or last_reset_date[0] != str(today):
                self.db_cursor.execute("UPDATE tasks SET {}='Todo', {}=? WHERE {}='Completed'".format(STATUS_COLUMN, DATE_RESET_COLUMN, STATUS_COLUMN),
                                       (str(today),))
                self.conn.commit()
                self.refresh_todo_list()
                self.refresh_completed_list()

    def add_task(self):
        task_text = self.task_entry.get()
        notes_text = self.notes_entry.get("1.0", tk.END).strip()

        if task_text:
            self.db_cursor.execute("INSERT INTO tasks ({}, {}, {}) VALUES (?, 'Todo', ?)".format(TASK_COLUMN, STATUS_COLUMN, NOTES_COLUMN),
                                   (task_text, notes_text))
            self.conn.commit()
            self.refresh_todo_list()
            self.task_entry.delete(0, tk.END)
            self.notes_entry.delete("1.0", tk.END)

    def refresh_todo_list(self):
        self.todo_list.delete(*self.todo_list.get_children())
        self.db_cursor.execute("SELECT * FROM tasks WHERE {}='Todo'".format(STATUS_COLUMN))
        for idx, row in enumerate(self.db_cursor.fetchall(), start=1):
            task_text = row[1]
            notes_text = row[3]
            self.todo_list.insert('', 'end', values=("{}. {}".format(idx, task_text), notes_text))

    def refresh_completed_list(self):
        self.completed_list.delete(*self.completed_list.get_children())
        self.db_cursor.execute("SELECT * FROM tasks WHERE {}='Completed'".format(STATUS_COLUMN))
        for idx, row in enumerate(self.db_cursor.fetchall(), start=1):
            task_text = row[1]
            notes_text = row[3]
            self.completed_list.insert('', 'end', values=("{}. {}".format(idx, task_text), notes_text))

    def mark_as_finished(self):
        selected_item = self.todo_list.selection()
        if selected_item:
            task = self.todo_list.item(selected_item, 'values')[0].split(".")[1].strip()
            self.db_cursor.execute("UPDATE tasks SET {}='Completed' WHERE {}=?".format(STATUS_COLUMN, TASK_COLUMN), (task,))
            self.conn.commit()
            self.refresh_todo_list()
            self.refresh_completed_list()

    def mark_as_unfinished(self):
        selected_item = self.completed_list.selection()
        if selected_item:
            task = self.completed_list.item(selected_item, 'values')[0].split(".")[1].strip()
            self.db_cursor.execute("UPDATE tasks SET {}='Todo' WHERE {}=?".format(STATUS_COLUMN, TASK_COLUMN), (task,))
            self.conn.commit()
            self.refresh_completed_list()
            self.refresh_todo_list()

    def delete_task(self):
        selected_item = self.todo_list.selection() or self.completed_list.selection()
        if selected_item:
            task = self.todo_list.item(selected_item, 'values')[0].split(".")[1].strip() if self.todo_list.selection() else self.completed_list.item(selected_item, 'values')[0].split(".")[1].strip()
            self.db_cursor.execute("DELETE FROM tasks WHERE {}=?".format(TASK_COLUMN), (task,))
            self.conn.commit()
            self.refresh_todo_list()
            self.refresh_completed_list()

    def edit_task_name(self):
        selected_item = self.todo_list.selection()
        if selected_item:
            old_task = self.todo_list.item(selected_item, 'values')[0].split(".")[1].strip()
            edited_task = simpledialog.askstring("Edit Task", "Edit task name for {}: ".format(old_task), initialvalue=old_task)
            if edited_task is not None:
                self.db_cursor.execute("UPDATE tasks SET {}=? WHERE {}=?".format(TASK_COLUMN, TASK_COLUMN), (edited_task, old_task))
                self.conn.commit()
                self.refresh_todo_list()
                self.refresh_completed_list()

    def edit_notes(self):
        selected_item = self.todo_list.selection()
        if selected_item:
            task = self.todo_list.item(selected_item, 'values')[0].split(".")[1].strip()
            self.db_cursor.execute("SELECT {} FROM tasks WHERE {}=?".format(NOTES_COLUMN, TASK_COLUMN), (task,))
            result = self.db_cursor.fetchone()
            notes = result[0] if result is not None else ""
            edited_notes = simpledialog.askstring("Edit Notes", "Edit notes for {}: ".format(task), initialvalue=notes)
            if edited_notes is not None:
                self.db_cursor.execute("UPDATE tasks SET {}=? WHERE {}=?".format(NOTES_COLUMN, TASK_COLUMN), (edited_notes, task))
                self.conn.commit()
                self.refresh_todo_list()
                self.refresh_completed_list()
                
    def show_context_menu_task(self, event):
        task_item = self.todo_list.identify_column(event.x)
        if task_item == "#1":  # Check if the clicked column is the "Task" column
            selected_item = self.todo_list.selection()
            if selected_item:
                self.context_menu_task.post(event.x_root, event.y_root)

    def show_context_menu_notes(self, event):
        notes_item = self.todo_list.identify_column(event.x)
        if notes_item == "#2":  # Check if the clicked column is the "Notes" column
            selected_item = self.todo_list.selection()
            if selected_item:
                self.context_menu_notes.post(event.x_root, event.y_root)

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManager(root)
