import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import html
import re
from datetime import datetime


# ── Color Palette ──────────────────────────────────────────────
BG_DARK      = "#0a0e1a"
BG_CARD      = "#111827"
BG_CARD_HOVER= "#1a2236"
BG_HEADER    = "#060b14"
ACCENT       = "#00d4ff"
ACCENT2      = "#0088cc"
GOLD         = "#f59e0b"
TEXT_PRIMARY = "#e2e8f0"
TEXT_MUTED   = "#64748b"
TEXT_WHITE   = "#ffffff"
SUCCESS      = "#10b981"
BORDER       = "#1e2d45"

# ── RSS Feeds ──────────────────────────────────────────────────
FEEDS = [
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://cryptonews.com/news/feed/",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
]

BLOCKCHAIN_KEYWORDS = [
    "blockchain","bitcoin","ethereum","crypto","defi","nft","web3",
    "smart contract","altcoin","token","wallet","mining","hash","ledger",
    "dao","dex","stablecoin","layer2","polygon","solana","binance","cardano",
]


def strip_html(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    return text.strip()


def is_blockchain(title, desc=""):
    combined = (title + " " + desc).lower()
    return any(kw in combined for kw in BLOCKCHAIN_KEYWORDS)


def fetch_articles():
    articles = []
    for url in FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read()
            root = ET.fromstring(raw)
            items = root.findall(".//item")
            for item in items[:30]:
                title = strip_html((item.findtext("title") or "").strip())
                link  = (item.findtext("link") or "").strip()
                desc  = strip_html((item.findtext("description") or "").strip())
                pub   = (item.findtext("pubDate") or "").strip()
                if title and link and is_blockchain(title, desc):
                    articles.append({
                        "title": title,
                        "link":  link,
                        "desc":  desc[:300] + ("..." if len(desc) > 300 else ""),
                        "full_desc": desc,
                        "pub":   pub,
                        "source": urllib.parse.urlparse(url).netloc.replace("www.", ""),
                    })
        except Exception:
            continue
    # deduplicate by title
    seen = set()
    unique = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return unique[:60]


def translate_to_hindi(text):
    """Use MyMemory free translation API."""
    try:
        # split into chunks ≤ 500 chars
        chunks = [text[i:i+450] for i in range(0, len(text), 450)]
        translated_chunks = []
        for chunk in chunks:
            encoded = urllib.parse.quote(chunk)
            url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=en|hi"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            translated_chunks.append(data["responseData"]["translatedText"])
        return " ".join(translated_chunks)
    except Exception as e:
        return f"[Translation failed: {e}]"


# ══════════════════════════════════════════════════════════════
#  Main Application
# ══════════════════════════════════════════════════════════════
class BlockchainNewsApp:

    def __init__(self, root):
        self.root = root
        self.root.title("ChainPulse  •  Blockchain News")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        self.root.configure(bg=BG_DARK)

        self.articles     = []
        self.filtered     = []
        self.current_view = "dashboard"   # "dashboard" | "article"
        self.current_art  = None
        self.hindi_mode   = tk.BooleanVar(value=False)
        self.search_var   = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)

        self._build_ui()
        self._load_articles_async()

    # ── UI Construction ────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_body()
        self._build_statusbar()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG_HEADER, height=72)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(hdr, bg=BG_HEADER)
        logo_frame.pack(side="left", padx=20, pady=10)
        tk.Label(logo_frame, text="⛓", font=("Segoe UI Emoji", 26),
                 bg=BG_HEADER, fg=ACCENT).pack(side="left")
        tk.Label(logo_frame, text=" Chain", font=("Georgia", 22, "bold"),
                 bg=BG_HEADER, fg=TEXT_WHITE).pack(side="left")
        tk.Label(logo_frame, text="Pulse", font=("Georgia", 22, "bold"),
                 bg=BG_HEADER, fg=ACCENT).pack(side="left")
        tk.Label(logo_frame, text="  BLOCKCHAIN NEWS", font=("Courier", 9),
                 bg=BG_HEADER, fg=TEXT_MUTED).pack(side="left", pady=(8,0))

        # Right controls
        ctrl = tk.Frame(hdr, bg=BG_HEADER)
        ctrl.pack(side="right", padx=20, pady=14)

        # Hindi toggle
        self.hindi_btn = tk.Button(
            ctrl, text="🇮🇳  हिंदी", font=("Segoe UI", 10, "bold"),
            bg="#1a2236", fg=GOLD, activebackground="#253050",
            activeforeground=GOLD, relief="flat", cursor="hand2",
            padx=12, pady=4, command=self._toggle_hindi)
        self.hindi_btn.pack(side="right", padx=(8, 0))

        # Refresh
        tk.Button(ctrl, text="↻  Refresh", font=("Segoe UI", 10),
                  bg=ACCENT2, fg=TEXT_WHITE, activebackground=ACCENT,
                  activeforeground=TEXT_WHITE, relief="flat", cursor="hand2",
                  padx=12, pady=4, command=self._load_articles_async
                  ).pack(side="right", padx=(8,0))

        # Search
        search_frame = tk.Frame(ctrl, bg="#1a2236", bd=0)
        search_frame.pack(side="right")
        tk.Label(search_frame, text="🔍", font=("Segoe UI Emoji", 11),
                 bg="#1a2236", fg=TEXT_MUTED).pack(side="left", padx=(8,2))
        tk.Entry(search_frame, textvariable=self.search_var,
                 font=("Segoe UI", 10), bg="#1a2236", fg=TEXT_PRIMARY,
                 insertbackground=ACCENT, relief="flat", width=22,
                 ).pack(side="left", pady=4, padx=(0,8))

        # Ticker strip
        ticker_frame = tk.Frame(self.root, bg=ACCENT2, height=28)
        ticker_frame.pack(fill="x", side="top")
        ticker_frame.pack_propagate(False)
        self.ticker_lbl = tk.Label(
            ticker_frame,
            text="  ⚡ LIVE  •  Loading blockchain news…",
            font=("Courier", 9, "bold"), bg=ACCENT2, fg=TEXT_WHITE, anchor="w")
        self.ticker_lbl.pack(fill="x", padx=8, pady=4)

    def _build_body(self):
        self.body = tk.Frame(self.root, bg=BG_DARK)
        self.body.pack(fill="both", expand=True, pady=(8,0))

        # Sidebar
        sidebar = tk.Frame(self.body, bg=BG_HEADER, width=200)
        sidebar.pack(fill="y", side="left")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="CATEGORIES", font=("Courier", 9, "bold"),
                 bg=BG_HEADER, fg=TEXT_MUTED).pack(pady=(20,8), padx=16, anchor="w")

        cats = [("🏠  Dashboard", self._show_dashboard),
                ("₿  Bitcoin",    lambda: self._filter_cat("bitcoin")),
                ("Ξ  Ethereum",   lambda: self._filter_cat("ethereum")),
                ("📊  DeFi",      lambda: self._filter_cat("defi")),
                ("🖼  NFT",       lambda: self._filter_cat("nft")),
                ("🌐  Web3",      lambda: self._filter_cat("web3")),
                ("⛏  Mining",    lambda: self._filter_cat("mining")),
                ("🔐  Security",  lambda: self._filter_cat("security")),]
        for label, cmd in cats:
            btn = tk.Button(sidebar, text=label, font=("Segoe UI", 10),
                            bg=BG_HEADER, fg=TEXT_PRIMARY, activebackground=BG_CARD,
                            activeforeground=ACCENT, relief="flat", anchor="w",
                            cursor="hand2", padx=16, pady=7, command=cmd)
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.configure(fg=ACCENT))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(fg=TEXT_PRIMARY))

        # Divider
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", pady=12, padx=12)
        tk.Label(sidebar, text="LIVE SOURCES", font=("Courier", 9, "bold"),
                 bg=BG_HEADER, fg=TEXT_MUTED).pack(padx=16, anchor="w")
        for src in ["cointelegraph.com","decrypt.co","cryptonews.com","coindesk.com"]:
            tk.Label(sidebar, text=f"  • {src}", font=("Segoe UI", 8),
                     bg=BG_HEADER, fg=TEXT_MUTED).pack(anchor="w", padx=12, pady=2)

        # Main content
        self.content = tk.Frame(self.body, bg=BG_DARK)
        self.content.pack(fill="both", expand=True, padx=10, pady=6)

        self._build_dashboard_frame()
        self._build_article_frame()
        self._show_dashboard()

    def _build_dashboard_frame(self):
        self.dash_frame = tk.Frame(self.content, bg=BG_DARK)

        # Canvas + Scrollbar
        self.canvas = tk.Canvas(self.dash_frame, bg=BG_DARK, highlightthickness=0)
        vsb = ttk.Scrollbar(self.dash_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.cards_frame = tk.Frame(self.canvas, bg=BG_DARK)
        self.canvas_window = self.canvas.create_window((0,0), window=self.cards_frame, anchor="nw")

        self.cards_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>",      self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>",  self._on_mousewheel)

    def _build_article_frame(self):
        self.art_frame = tk.Frame(self.content, bg=BG_DARK)

        # Back bar
        back_bar = tk.Frame(self.art_frame, bg=BG_HEADER, height=44)
        back_bar.pack(fill="x")
        back_bar.pack_propagate(False)

        tk.Button(back_bar, text="← Back to Dashboard",
                  font=("Segoe UI", 10), bg=BG_HEADER, fg=ACCENT,
                  activebackground=BG_CARD, activeforeground=ACCENT,
                  relief="flat", cursor="hand2", padx=14,
                  command=self._show_dashboard).pack(side="left", pady=6)

        self.art_hindi_btn = tk.Button(
            back_bar, text="🇮🇳  Translate to हिंदी",
            font=("Segoe UI", 10, "bold"), bg="#1a2236", fg=GOLD,
            activebackground="#253050", activeforeground=GOLD,
            relief="flat", cursor="hand2", padx=12,
            command=self._translate_article)
        self.art_hindi_btn.pack(side="right", padx=10, pady=6)

        self.art_open_btn = tk.Button(
            back_bar, text="🌐  Open in Browser",
            font=("Segoe UI", 10), bg=ACCENT2, fg=TEXT_WHITE,
            activebackground=ACCENT, activeforeground=TEXT_WHITE,
            relief="flat", cursor="hand2", padx=12,
            command=self._open_in_browser)
        self.art_open_btn.pack(side="right", padx=4, pady=6)

        # Article scroll area
        art_canvas = tk.Canvas(self.art_frame, bg=BG_DARK, highlightthickness=0)
        art_vsb    = ttk.Scrollbar(self.art_frame, orient="vertical", command=art_canvas.yview)
        art_canvas.configure(yscrollcommand=art_vsb.set)
        art_vsb.pack(side="right", fill="y")
        art_canvas.pack(side="left", fill="both", expand=True)

        self.art_inner = tk.Frame(art_canvas, bg=BG_DARK)
        self._art_win  = art_canvas.create_window((0,0), window=self.art_inner, anchor="nw")

        self.art_inner.bind("<Configure>",  lambda e: art_canvas.configure(
            scrollregion=art_canvas.bbox("all")))
        art_canvas.bind("<Configure>", lambda e: art_canvas.itemconfig(
            self._art_win, width=e.width))
        art_canvas.bind_all("<MouseWheel>", lambda e: art_canvas.yview_scroll(
            int(-1*(e.delta/120)), "units"))

        self._art_canvas = art_canvas

    def _build_statusbar(self):
        sb = tk.Frame(self.root, bg=BG_HEADER, height=26)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        self.status_lbl = tk.Label(
            sb, text="⚡ Initializing…", font=("Courier", 8),
            bg=BG_HEADER, fg=TEXT_MUTED, anchor="w")
        self.status_lbl.pack(side="left", padx=12)
        tk.Label(sb, text="ChainPulse v1.0  •  Live Blockchain Intelligence",
                 font=("Courier", 8), bg=BG_HEADER, fg=TEXT_MUTED
                 ).pack(side="right", padx=12)

    # ── Views ──────────────────────────────────────────────────

    def _show_dashboard(self):
        self.art_frame.pack_forget()
        self.dash_frame.pack(fill="both", expand=True)
        self.current_view = "dashboard"
        self._render_cards(self.filtered if self.filtered else self.articles)

    def _show_article(self, article):
        self.current_art = article
        self.dash_frame.pack_forget()
        self.art_frame.pack(fill="both", expand=True)
        self.current_view = "article"
        self._render_article(article, hindi=False)

    # ── Card Rendering ─────────────────────────────────────────

    def _render_cards(self, arts):
        for w in self.cards_frame.winfo_children():
            w.destroy()

        if not arts:
            tk.Label(self.cards_frame, text="No articles found.",
                     font=("Segoe UI", 14), bg=BG_DARK, fg=TEXT_MUTED
                     ).pack(pady=60)
            return

        # Hero card (first article)
        self._make_hero_card(arts[0])

        # Grid for the rest
        grid = tk.Frame(self.cards_frame, bg=BG_DARK)
        grid.pack(fill="x", padx=10, pady=6)

        for i, art in enumerate(arts[1:], 1):
            col = (i-1) % 3
            row = (i-1) // 3
            self._make_grid_card(grid, art, row, col)

        for c in range(3):
            grid.columnconfigure(c, weight=1)

    def _make_hero_card(self, art):
        card = tk.Frame(self.cards_frame, bg=BG_CARD, cursor="hand2")
        card.pack(fill="x", padx=10, pady=(8,6))

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="x", padx=20, pady=16)

        # Badge
        badge = tk.Frame(inner, bg=ACCENT)
        badge.pack(anchor="w", pady=(0,8))
        tk.Label(badge, text=" ● FEATURED ", font=("Courier", 8, "bold"),
                 bg=ACCENT, fg=BG_DARK).pack(padx=4, pady=2)

        title = tk.Label(inner, text=art["title"],
                         font=("Georgia", 16, "bold"), bg=BG_CARD, fg=TEXT_WHITE,
                         wraplength=900, justify="left", cursor="hand2")
        title.pack(anchor="w", pady=(0,6))

        desc = tk.Label(inner, text=art["desc"],
                        font=("Segoe UI", 10), bg=BG_CARD, fg=TEXT_MUTED,
                        wraplength=900, justify="left")
        desc.pack(anchor="w")

        meta = tk.Frame(inner, bg=BG_CARD)
        meta.pack(anchor="w", pady=(10,0))
        tk.Label(meta, text=f"📡 {art['source']}", font=("Courier", 8),
                 bg=BG_CARD, fg=ACCENT).pack(side="left")
        tk.Label(meta, text=f"   🕐 {art['pub'][:25] if art['pub'] else 'Recent'}",
                 font=("Courier", 8), bg=BG_CARD, fg=TEXT_MUTED).pack(side="left")

        for w in [card, inner, title, desc, meta]:
            w.bind("<Button-1>", lambda e, a=art: self._show_article(a))
        self._hover_effect(card, [card, inner, title, desc, meta])

    def _make_grid_card(self, parent, art, row, col):
        card = tk.Frame(parent, bg=BG_CARD, cursor="hand2", relief="flat")
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="both", padx=14, pady=12)

        src_bar = tk.Frame(inner, bg=BG_CARD)
        src_bar.pack(fill="x", pady=(0,6))
        tk.Label(src_bar, text=f"● {art['source'].upper()}",
                 font=("Courier", 7, "bold"), bg=BG_CARD, fg=ACCENT2
                 ).pack(side="left")

        title = tk.Label(inner, text=art["title"],
                         font=("Georgia", 11, "bold"), bg=BG_CARD, fg=TEXT_WHITE,
                         wraplength=280, justify="left", cursor="hand2")
        title.pack(anchor="w", pady=(0,6))

        desc = tk.Label(inner, text=art["desc"][:120]+"…" if len(art["desc"])>120 else art["desc"],
                        font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_MUTED,
                        wraplength=280, justify="left")
        desc.pack(anchor="w")

        tk.Label(inner, text=art["pub"][:16] if art["pub"] else "",
                 font=("Courier", 7), bg=BG_CARD, fg=TEXT_MUTED
                 ).pack(anchor="e", pady=(8,0))

        for w in [card, inner, title, desc]:
            w.bind("<Button-1>", lambda e, a=art: self._show_article(a))
        self._hover_effect(card, [card, inner, title, desc])

    def _hover_effect(self, card, widgets):
        def on_enter(e):
            card.configure(bg=BG_CARD_HOVER)
            for w in widgets:
                try:
                    w.configure(bg=BG_CARD_HOVER)
                except Exception:
                    pass
        def on_leave(e):
            card.configure(bg=BG_CARD)
            for w in widgets:
                try:
                    w.configure(bg=BG_CARD)
                except Exception:
                    pass
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

    # ── Article Rendering ──────────────────────────────────────

    def _render_article(self, article, hindi=False):
        for w in self.art_inner.winfo_children():
            w.destroy()

        pad = tk.Frame(self.art_inner, bg=BG_DARK)
        pad.pack(fill="x", padx=60, pady=30)

        # Source badge
        src_f = tk.Frame(pad, bg=BG_DARK)
        src_f.pack(anchor="w", pady=(0,12))
        tk.Label(src_f, text=f" {article['source'].upper()} ",
                 font=("Courier", 9, "bold"), bg=ACCENT2, fg=TEXT_WHITE
                 ).pack(side="left", ipadx=4, ipady=2)
        tk.Label(src_f, text=f"   {article['pub'][:30] if article['pub'] else 'Recent'}",
                 font=("Courier", 9), bg=BG_DARK, fg=TEXT_MUTED).pack(side="left")

        # Title
        title_text = article.get("title_hi", article["title"]) if hindi else article["title"]
        tk.Label(pad, text=title_text,
                 font=("Georgia", 20, "bold"), bg=BG_DARK, fg=TEXT_WHITE,
                 wraplength=900, justify="left").pack(anchor="w", pady=(0,16))

        # Divider
        tk.Frame(pad, bg=ACCENT, height=3).pack(fill="x", pady=(0,20))

        # Body
        body_text = article.get("body_hi", article["full_desc"]) if hindi else article["full_desc"]
        body_text = body_text or "No content available. Please open in browser for the full article."

        tk.Label(pad, text=body_text,
                 font=("Georgia", 12), bg=BG_DARK, fg=TEXT_PRIMARY,
                 wraplength=900, justify="left").pack(anchor="w", pady=(0,20))

        # Note
        tk.Label(pad,
                 text="ℹ  This is the article preview from RSS feed. Click 'Open in Browser' for the full article.",
                 font=("Segoe UI", 9), bg=BG_DARK, fg=TEXT_MUTED,
                 wraplength=900, justify="left").pack(anchor="w")

        self._art_canvas.yview_moveto(0)

    # ── Actions ────────────────────────────────────────────────

    def _toggle_hindi(self):
        if self.current_view == "article" and self.current_art:
            self._translate_article()

    def _translate_article(self):
        if not self.current_art:
            return
        art = self.current_art
        # already translated?
        if "body_hi" in art:
            self._render_article(art, hindi=True)
            return

        self.status_lbl.configure(text="⏳ Translating to Hindi…")
        self.art_hindi_btn.configure(state="disabled", text="⏳ Translating…")

        def do_translate():
            art["title_hi"] = translate_to_hindi(art["title"])
            art["body_hi"]  = translate_to_hindi(art["full_desc"] or art["desc"])
            self.root.after(0, lambda: [
                self._render_article(art, hindi=True),
                self.status_lbl.configure(text="✅ Translation complete"),
                self.art_hindi_btn.configure(
                    state="normal", text="🔤  Show English",
                    command=self._show_english),
            ])

        threading.Thread(target=do_translate, daemon=True).start()

    def _show_english(self):
        if self.current_art:
            self._render_article(self.current_art, hindi=False)
            self.art_hindi_btn.configure(
                text="🇮🇳  Translate to हिंदी",
                command=self._translate_article)

    def _open_in_browser(self):
        if self.current_art:
            webbrowser.open(self.current_art["link"])

    def _filter_cat(self, keyword):
        self.filtered = [a for a in self.articles if keyword in
                         (a["title"] + a["desc"]).lower()]
        self._show_dashboard()

    def _on_search(self, *_):
        q = self.search_var.get().lower()
        if q:
            self.filtered = [a for a in self.articles if q in
                             (a["title"] + a["desc"]).lower()]
        else:
            self.filtered = list(self.articles)
        if self.current_view == "dashboard":
            self._render_cards(self.filtered)

    # ── Data Loading ───────────────────────────────────────────

    def _load_articles_async(self):
        self.status_lbl.configure(text="⏳ Fetching latest blockchain news…")
        self._update_ticker("  ⚡ LIVE  •  Fetching blockchain news from multiple sources…")
        threading.Thread(target=self._load_thread, daemon=True).start()

    def _load_thread(self):
        arts = fetch_articles()
        self.root.after(0, lambda: self._on_articles_loaded(arts))

    def _on_articles_loaded(self, arts):
        self.articles = arts
        self.filtered = list(arts)
        count = len(arts)
        self.status_lbl.configure(text=f"✅ {count} blockchain articles loaded  •  {datetime.now().strftime('%H:%M:%S')}")
        ticker = "  ⚡ LIVE  •  " + "   ●   ".join(a["title"] for a in arts[:8])
        self._update_ticker(ticker)
        if self.current_view == "dashboard":
            self._render_cards(arts)

    def _update_ticker(self, text):
        self.ticker_lbl.configure(text=text)

    # ── Canvas helpers ─────────────────────────────────────────

    def _on_frame_configure(self, e):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self.canvas.itemconfig(self.canvas_window, width=e.width)

    def _on_mousewheel(self, e):
        if self.current_view == "dashboard":
            self.canvas.yview_scroll(int(-1*(e.delta/120)), "units")


# ── Entry Point ────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Vertical.TScrollbar",
                    background=BG_CARD, troughcolor=BG_DARK,
                    bordercolor=BG_DARK, arrowcolor=TEXT_MUTED,
                    darkcolor=BG_CARD, lightcolor=BG_CARD)

    app = BlockchainNewsApp(root)
    root.mainloop()
