import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os

# --- 1. Конфигурация и работа с данными (JSON) ---
DATA_FILE = "data/favorites.json"
GITHUB_API_URL = "https://api.github.com/search/users"

def load_favorites():
    """Загружает избранных пользователей из JSON-файла."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_favorites(favorites):
    """Сохраняет список избранных пользователей в JSON-файл."""
    with open(DATA_FILE, "w") as f:
        json.dump(favorites, f, indent=4)


# --- 2. Логика работы с API ---
def search_github_users(query):
    """
    Выполняет поиск пользователей через GitHub API.
    Возвращает список словарей с данными о пользователях.
    """
    try:
        params = {'q': query}
        headers = {'Accept': 'application/vnd.github.v3+json'}
        response = requests.get(GITHUB_API_URL, params=params, headers=headers)
        response.raise_for_status() # Проверка на ошибки HTTP (например, 404, 500)
        
        data = response.json()
        # Извлекаем только нужную информацию из каждого результата
        return [
            {
                'login': item['login'],
                'id': item['id'],
                'html_url': item['html_url'],
                'avatar_url': item['avatar_url']
            } for item in data.get('items', [])
        ]
        
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Ошибка сети", f"Не удалось подключиться к GitHub:\n{e}")
        return []


# --- 3. Логика GUI ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GitHub User Finder")
        self.geometry("900x600")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        
        # Загружаем избранное при запуске
        self.favorites = load_favorites()
        
        self.create_widgets()
        
    def create_widgets(self):
        # --- Верхний фрейм: Поиск ---
        frame_search = tk.Frame(self, bg="#f0f0f0")
        frame_search.pack(pady=15, fill="x", padx=20)
        
        tk.Label(frame_search, text="Поиск:", font=("Arial", 12), bg="#f0f0f0").pack(side="left")
        self.entry_search = tk.Entry(frame_search, font=("Arial", 12), width=30)
        self.entry_search.pack(side="left", ipadx=5, ipady=3)
        
        btn_search = tk.Button(frame_search, text="Найти", command=self.on_search)
        btn_search.pack(side="left", padx=10)
        
        # --- Фрейм для результатов и избранного ---
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#e0e0e0", sashwidth=5)
        main_pane.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Левая часть: Результаты поиска (Treeview)
        frame_results = tk.Frame(main_pane, bg="white")
        
        # Treeview для красивого отображения списка с аватарами и кнопками
        self.tree = ttk.Treeview(frame_results, columns=("login", "url"), show="headings")
        self.tree.heading("login", text="Логин")
        self.tree.heading("url", text="Профиль")
        self.tree.column("login", width=200)
        self.tree.column("url", width=0) # Скрываем колонку с URL, используем её для ссылки
        
        self.tree.pack(fill="both", expand=True)
        
        # Правая часть: Избранное (Listbox)
        frame_favs = tk.Frame(main_pane, bg="white")
        
        tk.Label(frame_favs, text="Избранное:", font=("Arial", 12)).pack(pady=5)
        
        self.listbox_favs = tk.Listbox(frame_favs, font=("Arial", 11), height=25)
        self.listbox_favs.pack(fill="both", expand=True)
        
        main_pane.add(frame_results)
        main_pane.add(frame_favs)
        
        # Обновляем список избранного при запуске окна
        self.update_favs_list()
    
    def on_search(self):
        """Обработчик нажатия кнопки 'Найти'."""
        query = self.entry_search.get().strip()
        
        # --- Проверка корректности ввода (Критерий 5) ---
        if not query:
            messagebox.showwarning("Ошибка", "Поле поиска не должно быть пустым!")
            return
            
        users = search_github_users(query)
        
        # Очищаем дерево перед вставкой новых данных
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        if not users:
            messagebox.showinfo("Результат", "Пользователи не найдены.")
            return
            
        for user in users:
            # Добавляем строку с логином и ссылкой.
            # Кнопку "В избранное" создаем динамически в колонке 'url'
            self.tree.insert("", "end", values=(user['login'], user['html_url']),
                             tags=(user['id'],))
        
        # Настраиваем отображение кнопок в колонке 'url'
        self.tree.tag_configure("addable", background="white")
        for child in self.tree.get_children():
            item_id = self.tree.item(child)["tags"][0]
            login = self.tree.item(child)["values"][0]
            
            # Создаем кнопку для каждой строки
            btn_fav = tk.Button
