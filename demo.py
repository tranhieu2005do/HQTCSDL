"""
Giao diện demo dự đoán tỷ số bóng đá
Sử dụng tkinter - chạy bằng: python app_demo.py
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading

# Thêm thư mục gốc vào sys.path 
# Đặt file này cùng cấp với thư mục models/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


BG_MAIN      = "#1a1a2e"
BG_PANEL     = "#16213e"
BG_CARD      = "#0f3460"
BG_INPUT     = "#1e2a4a"
ACCENT       = "#e94560"
ACCENT2      = "#00b4d8"
TEXT_MAIN    = "#eaeaea"
TEXT_SUB     = "#a0aec0"
TEXT_WIN     = "#48bb78"
TEXT_LOSE    = "#fc8181"
TEXT_DRAW    = "#f6e05e"
BORDER       = "#2d3748"

FONT_TITLE   = ("Segoe UI", 18, "bold")
FONT_HEAD    = ("Segoe UI", 12, "bold")
FONT_BODY    = ("Segoe UI", 10)
FONT_SMALL   = ("Segoe UI", 9)
FONT_SCORE   = ("Segoe UI", 32, "bold")
FONT_BTN     = ("Segoe UI", 11, "bold")
FONT_MONO    = ("Consolas", 10)


class FootballPredictorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("⚽  Football Match Predictor")
        self.root.geometry("920x780")
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(True, True)
        self.root.minsize(820, 700)

        self.engine = None
        self.team_list: list[str] = []

        self._build_ui()
        self._load_engine_async()

    # UI 
    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG_PANEL, pady=12)
        header.pack(fill="x")

        tk.Label(
            header, text="⚽  FOOTBALL MATCH PREDICTOR",
            font=FONT_TITLE, fg=ACCENT, bg=BG_PANEL
        ).pack()
        tk.Label(
            header, text="Dự đoán tỷ số dựa trên mô hình Machine Learning",
            font=FONT_SMALL, fg=TEXT_SUB, bg=BG_PANEL
        ).pack()

        self.status_var = tk.StringVar(value="⏳  Đang khởi động mô hình...")
        status_bar = tk.Frame(self.root, bg=BG_PANEL, padx=16, pady=4)
        status_bar.pack(fill="x")
        self.status_lbl = tk.Label(
            status_bar, textvariable=self.status_var,
            font=FONT_SMALL, fg=ACCENT2, bg=BG_PANEL, anchor="w"
        )
        self.status_lbl.pack(fill="x")

        main = tk.Frame(self.root, bg=BG_MAIN)
        main.pack(fill="both", expand=True, padx=20, pady=(8, 20))
        main.columnconfigure(0, weight=1)

        self._build_input_card(main)

        self._build_result_area(main)

    def _build_input_card(self, parent):
        card = tk.Frame(parent, bg=BG_PANEL, bd=0, relief="flat")
        card.pack(fill="x", pady=(0, 12))

        tk.Label(
            card, text="🏟  Thông tin trận đấu",
            font=FONT_HEAD, fg=ACCENT2, bg=BG_PANEL
        ).pack(anchor="w", padx=16, pady=(12, 4))

        sep = tk.Frame(card, bg=BORDER, height=1)
        sep.pack(fill="x", padx=16)

        row = tk.Frame(card, bg=BG_PANEL)
        row.pack(fill="x", padx=16, pady=12)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=0)
        row.columnconfigure(2, weight=1)
        row.columnconfigure(3, weight=0)
        row.columnconfigure(4, weight=1)

        home_col = tk.Frame(row, bg=BG_PANEL)
        home_col.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        tk.Label(home_col, text="ĐỘI NHÀ", font=FONT_SMALL, fg=TEXT_SUB, bg=BG_PANEL).pack(anchor="w")
        self.home_var = tk.StringVar()
        self.home_cb = ttk.Combobox(
            home_col, textvariable=self.home_var,
            font=FONT_BODY, state="disabled", height=12
        )
        self.home_cb.pack(fill="x", pady=(2, 0))
        self.home_cb.bind("<KeyRelease>", lambda e: self._filter_teams(self.home_cb, self.home_var))

        tk.Label(row, text="VS", font=("Segoe UI", 14, "bold"),
                 fg=ACCENT, bg=BG_PANEL).grid(row=0, column=1, padx=8)

        away_col = tk.Frame(row, bg=BG_PANEL)
        away_col.grid(row=0, column=2, sticky="ew", padx=(8, 8))
        tk.Label(away_col, text="ĐỘI KHÁCH", font=FONT_SMALL, fg=TEXT_SUB, bg=BG_PANEL).pack(anchor="w")
        self.away_var = tk.StringVar()
        self.away_cb = ttk.Combobox(
            away_col, textvariable=self.away_var,
            font=FONT_BODY, state="disabled", height=12
        )
        self.away_cb.pack(fill="x", pady=(2, 0))
        self.away_cb.bind("<KeyRelease>", lambda e: self._filter_teams(self.away_cb, self.away_var))

        date_col = tk.Frame(row, bg=BG_PANEL)
        date_col.grid(row=0, column=4, sticky="ew", padx=(8, 0))
        tk.Label(date_col, text="NGÀY THI ĐẤU", font=FONT_SMALL, fg=TEXT_SUB, bg=BG_PANEL).pack(anchor="w")
        self.date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        self.date_entry = tk.Entry(
            date_col, textvariable=self.date_var,
            font=FONT_BODY, bg=BG_INPUT, fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN, relief="flat", bd=4
        )
        self.date_entry.pack(fill="x", pady=(2, 0))

        btn_row = tk.Frame(card, bg=BG_PANEL)
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        self.predict_btn = tk.Button(
            btn_row, text="🔮  DỰ ĐOÁN NGAY",
            font=FONT_BTN, bg=ACCENT, fg="white",
            activebackground="#c0392b", activeforeground="white",
            relief="flat", bd=0, padx=24, pady=8, cursor="hand2",
            state="disabled", command=self._on_predict
        )
        self.predict_btn.pack(side="right")

        self.clear_btn = tk.Button(
            btn_row, text="🗑  Xóa kết quả",
            font=FONT_BODY, bg=BORDER, fg=TEXT_SUB,
            activebackground=BG_INPUT, activeforeground=TEXT_MAIN,
            relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
            command=self._clear_result
        )
        self.clear_btn.pack(side="right", padx=(0, 8))

    def _build_result_area(self, parent):
        self.result_frame = tk.Frame(parent, bg=BG_MAIN)
        self.result_frame.pack(fill="both", expand=True)

        self.placeholder = tk.Label(
            self.result_frame,
            text="Chọn hai đội và nhấn Dự Đoán để xem kết quả",
            font=FONT_BODY, fg=TEXT_SUB, bg=BG_MAIN
        )
        self.placeholder.pack(expand=True)


    def _load_engine_async(self):
        threading.Thread(target=self._load_engine, daemon=True).start()

    def _load_engine(self):
        try:
            from models.v2.predict_match import PredictionEngine
            import logging
            logging.disable(logging.CRITICAL)
            self.engine = PredictionEngine()
            self.team_list = sorted(self.engine.data_loader.get_team_id_mapping().keys())
            self.root.after(0, self._on_engine_ready)
        except Exception as exc:
            error_msg = str(exc)
            self.root.after(0, lambda: self._on_engine_error(error_msg))

    def _on_engine_ready(self):
        teams = self.team_list
        self.home_cb.configure(values=teams, state="normal")
        self.away_cb.configure(values=teams, state="normal")
        self.predict_btn.configure(state="normal")
        self.status_var.set(f"✅  Mô hình sẵn sàng  —  {len(teams)} đội được tải")
        self.status_lbl.configure(fg=TEXT_WIN)

    def _on_engine_error(self, msg):
        self.status_var.set(f"❌  Lỗi: {msg}")
        self.status_lbl.configure(fg=ACCENT)


    def _filter_teams(self, cb: ttk.Combobox, var: tk.StringVar):
        typed = var.get().lower()
        filtered = [t for t in self.team_list if typed in t.lower()]
        cb.configure(values=filtered)
        cb.event_generate("<Down>")

    def _on_predict(self):
        home = self.home_var.get().strip()
        away = self.away_var.get().strip()
        date = self.date_var.get().strip()

        if not home or not away:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn đội nhà và đội khách!")
            return
        if home == away:
            messagebox.showwarning("Lỗi", "Đội nhà và đội khách không thể giống nhau!")
            return
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Ngày không hợp lệ", "Định dạng ngày: YYYY-MM-DD  (ví dụ: 2024-03-15)")
            return

        self.predict_btn.configure(state="disabled", text="⏳  Đang dự đoán...")
        self._clear_result(keep_placeholder=False)
        self.status_var.set("🔄  Đang xử lý dự đoán...")
        self.status_lbl.configure(fg=ACCENT2)

        threading.Thread(
            target=self._run_prediction, args=(home, away, date), daemon=True
        ).start()

    def _run_prediction(self, home, away, date):
        try:
            result = self.engine.predict_match(home, away, date)
            self.root.after(0, lambda: self._show_result(result))
        except Exception as exc:
            error_msg = str(exc)
            self.root.after(0, lambda: self._show_error(error_msg))

    def _clear_result(self, keep_placeholder=True):
        for w in self.result_frame.winfo_children():
            w.destroy()
        if keep_placeholder:
            self.placeholder = tk.Label(
                self.result_frame,
                text="Chọn hai đội và nhấn Dự Đoán để xem kết quả",
                font=FONT_BODY, fg=TEXT_SUB, bg=BG_MAIN
            )
            self.placeholder.pack(expand=True)

    def _show_result(self, result: dict):
        self.predict_btn.configure(state="normal", text="🔮  DỰ ĐOÁN NGAY")
        self.status_var.set("✅  Dự đoán thành công!")
        self.status_lbl.configure(fg=TEXT_WIN)

        for w in self.result_frame.winfo_children():
            w.destroy()

        canvas = tk.Canvas(self.result_frame, bg=BG_MAIN, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG_MAIN)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        self._build_score_card(scroll_frame, result)
        self._build_h2h_card(scroll_frame, result)

    def _build_score_card(self, parent, result):
        """Card hiển thị kết quả dự đoán tỷ số."""
        card = tk.Frame(parent, bg=BG_PANEL, padx=20, pady=16)
        card.pack(fill="x", pady=(0, 12))

        winner = result["winner_prediction"]
        conf   = result["confidence"]
        conf_label = self.engine.get_confidence_interpretation(conf)

        conf_color = TEXT_WIN if conf_label == "HIGH" else ACCENT2 if conf_label == "MEDIUM" else TEXT_LOSE
        winner_map = {"HOME_WIN": "ĐỘI NHÀ THẮNG", "AWAY_WIN": "ĐỘI KHÁCH THẮNG", "DRAW": "HÒA"}
        winner_text = winner_map.get(winner, winner)
        winner_color = TEXT_WIN if winner == "HOME_WIN" else TEXT_LOSE if winner == "AWAY_WIN" else TEXT_DRAW

        tk.Label(card, text="🏆  KẾT QUẢ DỰ ĐOÁN",
                 font=FONT_HEAD, fg=ACCENT2, bg=BG_PANEL).pack(anchor="w")
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=(4, 12))

        score_row = tk.Frame(card, bg=BG_PANEL)
        score_row.pack(fill="x")

        tk.Label(score_row, text=result["home_team"],
                 font=FONT_HEAD, fg=TEXT_MAIN, bg=BG_PANEL, wraplength=200, justify="center"
                 ).grid(row=0, column=0, sticky="ew", padx=10)

        score_frame = tk.Frame(score_row, bg=BG_CARD, padx=20, pady=8)
        score_frame.grid(row=0, column=1, padx=20)
        tk.Label(
            score_frame,
            text=f"{result['predicted_home_goals']}  –  {result['predicted_away_goals']}",
            font=FONT_SCORE, fg=TEXT_MAIN, bg=BG_CARD
        ).pack()

        tk.Label(score_row, text=result["away_team"],
                 font=FONT_HEAD, fg=TEXT_MAIN, bg=BG_PANEL, wraplength=200, justify="center"
                 ).grid(row=0, column=2, sticky="ew", padx=10)

        for i in [0, 2]:
            score_row.columnconfigure(i, weight=1)
        score_row.columnconfigure(1, weight=0)

        tk.Label(card, text=f"📅  {result['match_date']}",
                 font=FONT_SMALL, fg=TEXT_SUB, bg=BG_PANEL).pack(pady=(10, 0))

        info_row = tk.Frame(card, bg=BG_PANEL)
        info_row.pack(pady=10)

        tk.Label(info_row, text=winner_text, font=("Segoe UI", 13, "bold"),
                 fg=winner_color, bg=BG_PANEL).pack(side="left", padx=(0, 20))

        tk.Label(info_row,
                 text=f"Độ tin cậy: {conf*100:.1f}%  ({conf_label})",
                 font=FONT_BODY, fg=conf_color, bg=BG_PANEL).pack(side="left")

    def _build_h2h_card(self, parent, result):
        """Card hiển thị 5 trận đối đầu gần nhất."""
        card = tk.Frame(parent, bg=BG_PANEL, padx=20, pady=16)
        card.pack(fill="x", pady=(0, 12))

        tk.Label(card, text="📊  5 TRẬN ĐỐI ĐẦU GẦN NHẤT",
                 font=FONT_HEAD, fg=ACCENT2, bg=BG_PANEL).pack(anchor="w")
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=(4, 12))

        h2h_matches = result.get("h2h_last5_matches", [])
        h2h_summary = result.get("h2h_summary", {})

        if not h2h_matches:
            tk.Label(card, text="Không có dữ liệu đối đầu trước đây.",
                     font=FONT_BODY, fg=TEXT_SUB, bg=BG_PANEL).pack()
            return

        summary_row = tk.Frame(card, bg=BG_CARD, padx=12, pady=10)
        summary_row.pack(fill="x", pady=(0, 12))

        stats = [
            ("⚽ Tổng trận",      str(h2h_summary.get("total_matches", 0))),
            ("🏠 ĐN thắng",       str(h2h_summary.get("home_team_wins", 0))),
            ("✈ ĐK thắng",       str(h2h_summary.get("away_team_wins", 0))),
            ("🤝 Hòa",            str(h2h_summary.get("draws", 0))),
            ("⚡ TB bàn (nhà)",   str(h2h_summary.get("home_team_avg_goals", 0))),
            ("⚡ TB bàn (khách)", str(h2h_summary.get("away_team_avg_goals", 0))),
            ("📈 Cả 2 ghi bàn",  f"{h2h_summary.get('btts_rate', 0)*100:.0f}%"),
            ("📈 Trên 2.5 bàn",  f"{h2h_summary.get('over_2_5_rate', 0)*100:.0f}%"),
        ]

        cols = 4
        for i, (label, value) in enumerate(stats):
            col = i % cols
            row_idx = i // cols
            cell = tk.Frame(summary_row, bg=BG_CARD, padx=12)
            cell.grid(row=row_idx, column=col, sticky="ew", pady=2)
            summary_row.columnconfigure(col, weight=1)
            tk.Label(cell, text=label, font=FONT_SMALL, fg=TEXT_SUB, bg=BG_CARD).pack()
            tk.Label(cell, text=value, font=FONT_HEAD, fg=ACCENT2, bg=BG_CARD).pack()

        header = tk.Frame(card, bg=BG_INPUT)
        header.pack(fill="x")
        for col_text, col_width in [("NGÀY", 100), ("ĐỘI NHÀ", 180), ("TỶ SỐ", 80), ("ĐỘI KHÁCH", 180), ("KQ", 100)]:
            tk.Label(
                header, text=col_text, font=FONT_SMALL, fg=TEXT_SUB,
                bg=BG_INPUT, width=col_width // 8, anchor="center", padx=6, pady=5
            ).pack(side="left", expand=True, fill="x")

        result_map = {
            "HOME_WIN": ("ĐN Thắng", TEXT_WIN),
            "AWAY_WIN": ("ĐK Thắng", TEXT_LOSE),
            "DRAW":     ("Hòa",      TEXT_DRAW),
        }

        home_id = self.engine.data_loader.get_team_id_mapping().get(result["home_team"])

        for idx, match in enumerate(h2h_matches):
            row_bg = BG_CARD if idx % 2 == 0 else BG_PANEL
            row = tk.Frame(card, bg=row_bg)
            row.pack(fill="x")

            kq_text, kq_color = result_map.get(match["result"], (match["result"], TEXT_MAIN))

            home_name_in_match = match["home_team"]
            away_name_in_match = match["away_team"]

            tk.Label(row, text=match["date"], font=FONT_MONO, fg=TEXT_SUB,
                     bg=row_bg, padx=6, pady=4).pack(side="left", expand=True, fill="x")
            tk.Label(row, text=home_name_in_match, font=FONT_BODY, fg=TEXT_MAIN,
                     bg=row_bg, anchor="e", padx=6).pack(side="left", expand=True, fill="x")
            tk.Label(row, text=f"{match['home_goals']}  –  {match['away_goals']}",
                     font=("Segoe UI", 10, "bold"), fg=ACCENT2,
                     bg=row_bg, anchor="center", padx=4).pack(side="left", expand=True, fill="x")
            tk.Label(row, text=away_name_in_match, font=FONT_BODY, fg=TEXT_MAIN,
                     bg=row_bg, anchor="w", padx=6).pack(side="left", expand=True, fill="x")
            tk.Label(row, text=kq_text, font=FONT_SMALL, fg=kq_color,
                     bg=row_bg, anchor="center", padx=6).pack(side="left", expand=True, fill="x")

    def _show_error(self, msg: str):
        self.predict_btn.configure(state="normal", text="🔮  DỰ ĐOÁN NGAY")
        self.status_var.set(f"❌  Lỗi: {msg[:80]}")
        self.status_lbl.configure(fg=ACCENT)

        for w in self.result_frame.winfo_children():
            w.destroy()

        error_card = tk.Frame(self.result_frame, bg=BG_PANEL, padx=20, pady=20)
        error_card.pack(fill="x", pady=10)
        tk.Label(error_card, text="❌  Có lỗi xảy ra", font=FONT_HEAD, fg=ACCENT, bg=BG_PANEL).pack()
        tk.Label(error_card, text=msg, font=FONT_BODY, fg=TEXT_SUB, bg=BG_PANEL, wraplength=700).pack(pady=8)


def apply_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "TCombobox",
        fieldbackground=BG_INPUT,
        background=BG_INPUT,
        foreground=TEXT_MAIN,
        selectbackground=BG_CARD,
        selectforeground=TEXT_MAIN,
        bordercolor=BORDER,
        arrowcolor=ACCENT2,
        relief="flat",
    )
    style.configure("TScrollbar", background=BORDER, troughcolor=BG_PANEL, bordercolor=BG_PANEL)
    style.map("TCombobox", fieldbackground=[("readonly", BG_INPUT)])


def main():
    root = tk.Tk()
    apply_style()

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = FootballPredictorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()