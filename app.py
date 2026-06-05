import csv
from difflib import SequenceMatcher
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


APP_TITLE = "歌曲名单查询工具"
DEFAULT_CSV = Path(__file__).with_name("data") / "nocopyright_list.csv"
MAIN_COLUMNS = ["歌曲名", "演唱", "专辑"]


def normalize(value):
    return str(value or "").strip().casefold()


def compact(value):
    return "".join(normalize(value).split())


def fuzzy_score(query, text):
    query = compact(query)
    text = compact(text)
    if not query or not text:
        return 0
    if query in text:
        return 100

    score = int(SequenceMatcher(None, query, text).ratio() * 100)
    if len(query) >= 2:
        window_scores = [
            int(SequenceMatcher(None, query, text[index : index + len(query)]).ratio() * 100)
            for index in range(max(1, len(text) - len(query) + 1))
        ]
        score = max(score, max(window_scores, default=0))
    return score


class SongCsvStore:
    def __init__(self, path):
        self.path = Path(path)
        self.preamble = []
        self.headers = MAIN_COLUMNS[:]
        self.extra_width = 0
        self.rows = []
        self.load()

    def load(self):
        if not self.path.exists():
            self.preamble = []
            self.headers = MAIN_COLUMNS[:]
            self.extra_width = 0
            self.rows = []
            return

        with self.path.open("r", encoding="utf-8-sig", newline="") as file:
            raw_rows = list(csv.reader(file))

        header_index = self._find_header_row(raw_rows)
        if header_index is None:
            self.preamble = []
            self.headers = MAIN_COLUMNS[:]
            data_rows = raw_rows
        else:
            self.preamble = raw_rows[:header_index]
            self.headers = raw_rows[header_index]
            data_rows = raw_rows[header_index + 1 :]

        width = max(len(self.headers), *(len(row) for row in data_rows), len(MAIN_COLUMNS))
        self.extra_width = max(0, width - len(MAIN_COLUMNS))
        self.headers = self._fit_width(self.headers, width)
        self.rows = [self._fit_width(row, width) for row in data_rows if any(cell.strip() for cell in row)]

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(self.preamble)
            writer.writerow(self.headers)
            writer.writerows(self.rows)

    def add(self, title, artist, album):
        width = len(self.headers)
        row = self._fit_width([title.strip(), artist.strip(), album.strip()], width)
        self.rows.append(row)
        self.save()

    def delete(self, row_indexes):
        for index in sorted(row_indexes, reverse=True):
            if 0 <= index < len(self.rows):
                del self.rows[index]
        self.save()

    def search(self, text):
        query = normalize(text)
        if not query:
            return list(enumerate(self.rows))

        matched = []
        threshold = 58 if len(compact(query)) <= 3 else 64
        for index, row in enumerate(self.rows):
            fields = row[:3]
            combined = " ".join(fields)
            score = max(
                fuzzy_score(query, combined),
                fuzzy_score(query, fields[0]),
                fuzzy_score(query, fields[1]),
                fuzzy_score(query, fields[2]),
            )
            if score >= threshold:
                matched.append((score, index, row))

        matched.sort(key=lambda item: (-item[0], item[1]))
        return [(index, row) for _, index, row in matched]

    @staticmethod
    def _fit_width(row, width):
        return list(row[:width]) + [""] * max(0, width - len(row))

    @staticmethod
    def _find_header_row(rows):
        for index, row in enumerate(rows):
            normalized = [cell.strip() for cell in row]
            if "歌曲名" in normalized:
                return index
        return None


class SongApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x640")
        self.minsize(760, 480)

        self.store = SongCsvStore(DEFAULT_CSV)
        self.visible_items = []

        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        toolbar = ttk.Frame(self, padding=(12, 10, 12, 6))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(1, weight=1)

        ttk.Label(toolbar, text="CSV 文件").grid(row=0, column=0, sticky="w")
        self.file_label = ttk.Label(toolbar, text=str(self.store.path), foreground="#555")
        self.file_label.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        ttk.Button(toolbar, text="选择 CSV", command=self.choose_file).grid(row=0, column=2)

        search_bar = ttk.Frame(self, padding=(12, 4, 12, 6))
        search_bar.grid(row=1, column=0, sticky="ew")
        search_bar.columnconfigure(1, weight=1)

        ttk.Label(search_bar, text="查询歌曲").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_table())
        search_entry = ttk.Entry(search_bar, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        ttk.Button(search_bar, text="清空", command=lambda: self.search_var.set("")).grid(row=0, column=2)

        table_frame = ttk.Frame(self, padding=(12, 0, 12, 6))
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.table = ttk.Treeview(table_frame, columns=MAIN_COLUMNS, show="headings", selectmode="extended")
        for column in MAIN_COLUMNS:
            self.table.heading(column, text=column)
            self.table.column(column, width=240, minwidth=120, anchor="w")
        self.table.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.table.configure(yscrollcommand=scrollbar.set)

        editor = ttk.Frame(self, padding=(12, 6, 12, 12))
        editor.grid(row=3, column=0, sticky="ew")
        for index in range(3):
            editor.columnconfigure(index * 2 + 1, weight=1)

        self.title_var = tk.StringVar()
        self.artist_var = tk.StringVar()
        self.album_var = tk.StringVar()

        ttk.Label(editor, text="歌曲名").grid(row=0, column=0, sticky="w")
        ttk.Entry(editor, textvariable=self.title_var).grid(row=0, column=1, sticky="ew", padx=(6, 12))
        ttk.Label(editor, text="演唱").grid(row=0, column=2, sticky="w")
        ttk.Entry(editor, textvariable=self.artist_var).grid(row=0, column=3, sticky="ew", padx=(6, 12))
        ttk.Label(editor, text="专辑").grid(row=0, column=4, sticky="w")
        ttk.Entry(editor, textvariable=self.album_var).grid(row=0, column=5, sticky="ew", padx=(6, 12))

        actions = ttk.Frame(editor)
        actions.grid(row=0, column=6, sticky="e")
        ttk.Button(actions, text="添加", command=self.add_song).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(actions, text="删除选中", command=self.delete_selected).grid(row=0, column=1)

        self.status_var = tk.StringVar()
        status = ttk.Label(self, textvariable=self.status_var, anchor="w", padding=(12, 0, 12, 10))
        status.grid(row=4, column=0, sticky="ew")

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="选择歌曲名单 CSV",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
        )
        if not path:
            return
        self.store = SongCsvStore(path)
        self.file_label.configure(text=str(self.store.path))
        self.refresh_table()

    def refresh_table(self):
        for item in self.table.get_children():
            self.table.delete(item)

        self.visible_items = self.store.search(self.search_var.get())
        for visible_index, (row_index, row) in enumerate(self.visible_items):
            self.table.insert("", "end", iid=str(visible_index), values=row[:3])

        total = len(self.store.rows)
        shown = len(self.visible_items)
        self.status_var.set(f"显示 {shown} / {total} 首歌")

    def add_song(self):
        title = self.title_var.get().strip()
        artist = self.artist_var.get().strip()
        album = self.album_var.get().strip()

        if not title:
            messagebox.showwarning(APP_TITLE, "请至少填写歌曲名。")
            return

        exists = any(
            normalize(row[0]) == normalize(title) and normalize(row[1]) == normalize(artist)
            for row in self.store.rows
        )
        if exists and not messagebox.askyesno(APP_TITLE, "列表里已有同名同歌手歌曲，仍然添加吗？"):
            return

        self.store.add(title, artist, album)
        self.title_var.set("")
        self.artist_var.set("")
        self.album_var.set("")
        self.refresh_table()

    def delete_selected(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showinfo(APP_TITLE, "请先在表格里选中要删除的歌曲。")
            return

        if not messagebox.askyesno(APP_TITLE, f"确定删除选中的 {len(selected)} 条记录吗？"):
            return

        row_indexes = [self.visible_items[int(item)][0] for item in selected]
        self.store.delete(row_indexes)
        self.refresh_table()


if __name__ == "__main__":
    app = SongApp()
    app.mainloop()
