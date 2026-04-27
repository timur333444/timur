import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
from functools import partial

DATA_FILE = "expenses.json"


class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("800x500")
        self.root.resizable(True, True)

        self.expenses = []
        self.load_data()

        # Переменные для полей ввода
        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.filter_category_var = tk.StringVar()
        self.filter_date_var = tk.StringVar()

        self.categories = ["Еда", "Транспорт", "Развлечения", "Здоровье", "Коммунальные услуги", "Другое"]

        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        # === Фрейм ввода данных ===
        input_frame = ttk.LabelFrame(self.root, text="Добавить расход", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        # Сумма
        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(input_frame, textvariable=self.amount_var, width=15).grid(row=0, column=1, padx=5, pady=5)

        # Категория
        ttk.Label(input_frame, text="Категория:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        category_combo = ttk.Combobox(input_frame, textvariable=self.category_var, values=self.categories, width=15)
        category_combo.grid(row=0, column=3, padx=5, pady=5)
        category_combo.set(self.categories[0])

        # Дата
        ttk.Label(input_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(input_frame, textvariable=self.date_var, width=12).grid(row=0, column=5, padx=5, pady=5)

        # Кнопка добавления
        ttk.Button(input_frame, text="➕ Добавить", command=self.add_expense).grid(row=0, column=6, padx=10, pady=5)

        # === Фрейм фильтрации ===
        filter_frame = ttk.LabelFrame(self.root, text="Фильтрация", padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(filter_frame, text="Категория:").grid(row=0, column=0, padx=5, pady=5)
        filter_category = ttk.Combobox(filter_frame, textvariable=self.filter_category_var,
                                       values=["Все"] + self.categories, width=15)
        filter_category.grid(row=0, column=1, padx=5, pady=5)
        filter_category.set("Все")

        ttk.Label(filter_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(filter_frame, textvariable=self.filter_date_var, width=12).grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(filter_frame, text="🔍 Применить фильтр", command=self.refresh_table).grid(row=0, column=4, padx=10, pady=5)
        ttk.Button(filter_frame, text="❌ Сбросить фильтры", command=self.clear_filters).grid(row=0, column=5, padx=5, pady=5)

        # === Фрейм суммы за период ===
        period_frame = ttk.LabelFrame(self.root, text="Подсчёт за период", padding=10)
        period_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(period_frame, text="Начало (ГГГГ-ММ-ДД):").grid(row=0, column=0, padx=5, pady=5)
        self.start_date_var = tk.StringVar()
        ttk.Entry(period_frame, textvariable=self.start_date_var, width=12).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(period_frame, text="Конец (ГГГГ-ММ-ДД):").grid(row=0, column=2, padx=5, pady=5)
        self.end_date_var = tk.StringVar()
        ttk.Entry(period_frame, textvariable=self.end_date_var, width=12).grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(period_frame, text="💰 Рассчитать сумму", command=self.calculate_period_sum).grid(row=0, column=4, padx=10, pady=5)

        self.period_sum_label = ttk.Label(period_frame, text="Сумма за период: 0.00 ₽", font=("Arial", 10, "bold"))
        self.period_sum_label.grid(row=0, column=5, padx=10, pady=5)

        # === Таблица расходов ===
        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("id", "amount", "category", "date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        self.tree.heading("id", text="ID")
        self.tree.heading("amount", text="Сумма (₽)")
        self.tree.heading("category", text="Категория")
        self.tree.heading("date", text="Дата")

        self.tree.column("id", width=40)
        self.tree.column("amount", width=100)
        self.tree.column("category", width=150)
        self.tree.column("date", width=120)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # === Кнопки управления ===
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(control_frame, text="🗑 Удалить выбранное", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="💾 Сохранить в JSON", command=self.save_data).pack(side=tk.LEFT, padx=5)

    def validate_amount(self, amount_str):
        try:
            amount = float(amount_str)
            if amount <= 0:
                return False, "Сумма должна быть положительным числом"
            return True, amount
        except ValueError:
            return False, "Сумма должна быть числом"

    def validate_date(self, date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True, date_str
        except ValueError:
            return False, "Дата должна быть в формате ГГГГ-ММ-ДД"

    def add_expense(self):
        amount_str = self.amount_var.get().strip()
        category = self.category_var.get().strip()
        date_str = self.date_var.get().strip()

        # Валидация
        valid_amount, amount_or_error = self.validate_amount(amount_str)
        if not valid_amount:
            messagebox.showerror("Ошибка ввода", amount_or_error)
            return

        if not category:
            messagebox.showerror("Ошибка ввода", "Категория не может быть пустой")
            return

        valid_date, date_or_error = self.validate_date(date_str)
        if not valid_date:
            messagebox.showerror("Ошибка ввода", date_or_error)
            return

        # Добавление
        new_id = max([e["id"] for e in self.expenses], default=0) + 1
        self.expenses.append({
            "id": new_id,
            "amount": amount_or_error,
            "category": category,
            "date": date_or_error
        })

        self.save_data()
        self.refresh_table()
        self.clear_input_fields()
        messagebox.showinfo("Успех", "Расход добавлен")

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return

        for item in selected:
            expense_id = int(self.tree.item(item)["values"][0])
            self.expenses = [e for e in self.expenses if e["id"] != expense_id]

        self.save_data()
        self.refresh_table()
        messagebox.showinfo("Успех", "Запись(и) удалены")

    def get_filtered_expenses(self):
        filtered = self.expenses.copy()

        category = self.filter_category_var.get()
        if category and category != "Все":
            filtered = [e for e in filtered if e["category"] == category]

        date = self.filter_date_var.get().strip()
        if date:
            valid, _ = self.validate_date(date)
            if valid:
                filtered = [e for e in filtered if e["date"] == date]

        return filtered

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        filtered = self.get_filtered_expenses()
        for expense in filtered:
            self.tree.insert("", tk.END, values=(
                expense["id"],
                f"{expense['amount']:.2f}",
                expense["category"],
                expense["date"]
            ))

    def calculate_period_sum(self):
        start_str = self.start_date_var.get().strip()
        end_str = self.end_date_var.get().strip()

        if not start_str or not end_str:
            messagebox.showwarning("Предупреждение", "Введите начальную и конечную дату")
            return

        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_str, "%Y-%m-%d")

            if start_date > end_date:
                messagebox.showerror("Ошибка", "Начальная дата не может быть позже конечной")
                return

            total = 0
            for expense in self.expenses:
                expense_date = datetime.strptime(expense["date"], "%Y-%m-%d")
                if start_date <= expense_date <= end_date:
                    total += expense["amount"]

            self.period_sum_label.config(text=f"Сумма за период: {total:.2f} ₽")

        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")

    def clear_filters(self):
        self.filter_category_var.set("Все")
        self.filter_date_var.set("")
        self.refresh_table()

    def clear_input_fields(self):
        self.amount_var.set("")
        self.date_var.set("")

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.expenses = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.expenses = []

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.expenses, f, ensure_ascii=False, indent=2)
        except IOError as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить данные: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()