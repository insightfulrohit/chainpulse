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
BG_DARK       = "#0a0e1a"
BG_CARD       = "#111827"
BG_CARD_HOVER = "#1a2236"
BG_HEADER     = "#060b14"
BG_SIDEBAR    = "#07101c"
ACCENT        = "#00d4ff"
ACCENT2       = "#0088cc"
GOLD          = "#f59e0b"
TEXT_PRIMARY  = "#e2e8f0"
TEXT_MUTED    = "#64748b"
TEXT_WHITE    = "#ffffff"
SUCCESS       = "#10b981"
BORDER        = "#1e2d45"

# ── Per-Section Accent Colors ──────────────────────────────────
SECTION_COLORS = {
    "blockchain": {"accent": "#00d4ff", "dim": "#0088cc", "badge_bg": "#003a52", "icon": "⛓"},
    "ai":         {"accent": "#a855f7", "dim": "#7c3aed", "badge_bg": "#2e1a4a", "icon": "🤖"},
    "hacking":    {"accent": "#ef4444", "dim": "#b91c1c", "badge_bg": "#3b0f0f", "icon": "💀"},
    "tech":       {"accent": "#22c55e", "dim": "#15803d", "badge_bg": "#0f2d1a", "icon": "🔬"},
}

# ── RSS Feeds Per Section ──────────────────────────────────────
SECTION_FEEDS = {
    "blockchain": [
        "https://cointelegraph.com/rss",
        "https://decrypt.co/feed",
        "https://cryptonews.com/news/feed/",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
    ],
    "ai": [
        "https://feeds.feedburner.com/venturebeat/SZYF",
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.wired.com/feed/rss",
    ],
    "hacking": [
        "https://feeds.feedburner.com/TheHackersNews",
        "https://www.bleepingcomputer.com/feed/",
        "https://krebsonsecurity.com/feed/",
        "https://threatpost.com/feed/",
        "https://www.darkreading.com/rss.xml",
    ],
    "tech": [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.wired.com/feed/rss",
        "https://feeds.feedburner.com/venturebeat/SZYF",
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    ],
}

# ── Keywords Per Section ───────────────────────────────────────
SECTION_KEYWORDS = {
    "blockchain": [
        "blockchain", "bitcoin", "ethereum", "crypto", "defi", "nft", "web3",
        "smart contract", "altcoin", "token", "wallet", "mining", "hash", "ledger",
        "dao", "dex", "stablecoin", "layer2", "polygon", "solana", "binance", "cardano",
    ],
    "ai": [
        "artificial intelligence", "ai ", "openai", "chatgpt", "gemini", "claude", "llm",
        "machine learning", "deep learning", "neural network", "gpt", "large language",
        "generative ai", "ai model", "ai safety", "ai regulation", "ai hacking",
        "ai attack", "ai vulnerability", "ai cybersecurity", "ai breach",
        "copilot", "midjourney", "stable diffusion", "ai tool", "ai chip",
        "nvidia ai", "google ai", "meta ai", "microsoft ai", "anthropic",
    ],
    "hacking": [
        "hack", "breach", "cyberattack", "ransomware", "malware", "phishing", "exploit",
        "vulnerability", "zero-day", "data leak", "stolen", "cybercrime", "ddos",
        "intrusion", "dark web", "spyware", "backdoor", "credential", "compromised",
        "security flaw", "cve", "threat actor", "apt", "nation-state", "cyber espionage",
        "data theft", "password", "encryption crack", "botnet", "trojan", "worm",
    ],
    "tech": [
        "technology", "invention", "innovation", "launch", "release", "new device",
        "smartphone", "chip", "processor", "quantum", "robotics", "5g", "6g", "satellite",
        "electric vehicle", "ev", "battery", "space", "nasa", "spacex", "apple", "google",
        "microsoft", "meta", "amazon", "samsung", "gadget", "software update",
        "breakthrough", "research", "scientist", "laboratory", "patent", "startup",
    ],
}

# ── Section Labels ─────────────────────────────────────────────
SECTION_LABELS = {
    "blockchain": "⛓  Blockchain",
    "ai":         "🤖  AI News",
    "hacking":    "💀  Hacking",
    "tech":       "🔬  Tech News",
}

# ── Sidebar Sub-Categories ─────────────────────────────────────
SECTION_SUBCATS = {
    "blockchain": [
        ("₿  Bitcoin",    "bitcoin"),
        ("Ξ  Ethereum",   "ethereum"),
        ("📊  DeFi",      "defi"),
        ("🖼  NFT",       "nft"),
        ("🌐  Web3",      "web3"),
        ("⛏  Mining",    "mining"),
        ("🔐  Security",  "security"),
    ],
    "ai": [
        ("🧠  LLM",        "llm"),
        ("🔓  AI Hacks",   "ai hacking"),
        ("🛡  AI Safety",  "ai safety"),
        ("🎨  GenAI",      "generative"),
        ("⚡  OpenAI",     "openai"),
        ("🔮  Google AI",  "google ai"),
    ],
    "hacking": [
        ("💣  Ransomware", "ransomware"),
        ("🎣  Phishing",   "phishing"),
        ("🕳  Zero-Day",   "zero-day"),
        ("🌊  DDoS",       "ddos"),
        ("🕵  Espionage",  "espionage"),
        ("🔐  Breach",     "breach"),
    ],
    "tech": [
        ("📱  Devices",    "smartphone"),
        ("🚀  Space",      "space"),
        ("🤖  Robotics",   "robotics"),
        ("⚡  EV",         "electric vehicle"),
        ("💻  Software",   "software"),
        ("🔬  Science",    "research"),
    ],
}


# ── Helpers ────────────────────────────────────────────────────

def strip_html(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def matches_section(title, desc, section):
    combined = (title + " " + desc).lower()
    return any(kw in combined for kw in SECTION_KEYWORDS[section])


def fetch_section(section):
    articles = []
    for url in SECTION_FEEDS[section]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                raw = resp.read()
            root = ET.fromstring(raw)
            items = root.findall(".//item")
            for item in items[:40]:
                title = strip_html((item.findtext("title") or "").strip())
                link  = (item.findtext("link") or "").strip()
                desc  = strip_html((item.findtext("description") or "").strip())
                pub   = (item.findtext("pubDate") or "").strip()
                if title and link and matches_section(title, desc, section):
                    articles.append({
                        "title":     title,
                        "link":      link,
                        "desc":      desc[:300] + ("..." if len(desc) > 300 else ""),
                        "full_desc": desc,
                        "pub":       pub,
                        "source":    urllib.parse.urlparse(url).netloc.replace("www.", ""),
                        "section":   section,
                    })
        except Exception:
            continue

    seen, unique = set(), []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return unique[:60]


def translate_to_hindi(text):
    """Use MyMemory free translation API — no key needed."""
    try:
        chunks = [text[i:i+450] for i in range(0, len(text), 450)]
        translated_chunks = []
        for chunk in chunks:
            encoded = urllib.parse.quote(chunk)
            url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=en|hi"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read())
            translated_chunks.append(data["responseData"]["translatedText"])
        return " ".join(translated_chunks)
    except Exception as e:
        return f"[Translation failed: {e}]"


# ══════════════════════════════════════════════════════════════
#  Main Application
# ══════════════════════════════════════════════════════════════
class ChainPulseApp:

    def __init__(self, root):
        self.root = root
        self.root.title("ChainPulse  •  Live Intelligence Dashboard")
        self.root.geometry("1280x860")
        self.root.minsize(960, 640)
        self.root.configure(bg=BG_DARK)

        # Per-section data stores
        self.data    = {s: [] for s in SECTION_FEEDS}
        self.filtered = {s: [] for s in SECTION_FEEDS}
        self.loading  = {s: False for s in SECTION_FEEDS}

        self.active_section = "blockchain"
        self.current_view   = "dashboard"
        self.current_art    = None
        self.search_var     = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)

        self._build_ui()
        self._load_all_async()

    # ── UI Construction ────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_nav_tabs()
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
        tk.Label(logo_frame, text="   LIVE INTELLIGENCE DASHBOARD",
                 font=("Courier", 9), bg=BG_HEADER, fg=TEXT_MUTED
                 ).pack(side="left", pady=(8, 0))

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

        # Refresh All
        tk.Button(ctrl, text="↻  Refresh All", font=("Segoe UI", 10),
                  bg=ACCENT2, fg=TEXT_WHITE, activebackground=ACCENT,
                  activeforeground=TEXT_WHITE, relief="flat", cursor="hand2",
                  padx=12, pady=4, command=self._load_all_async
                  ).pack(side="right", padx=(8, 0))

        # Search
        search_frame = tk.Frame(ctrl, bg="#1a2236", bd=0)
        search_frame.pack(side="right")
        tk.Label(search_frame, text="🔍", font=("Segoe UI Emoji", 11),
                 bg="#1a2236", fg=TEXT_MUTED).pack(side="left", padx=(8, 2))
        tk.Entry(search_frame, textvariable=self.search_var,
                 font=("Segoe UI", 10), bg="#1a2236", fg=TEXT_PRIMARY,
                 insertbackground=ACCENT, relief="flat", width=22,
                 ).pack(side="left", pady=4, padx=(0, 8))

    def _build_nav_tabs(self):
        tab_bar = tk.Frame(self.root, bg=BG_HEADER, height=46)
        tab_bar.pack(fill="x", side="top")
        tab_bar.pack_propagate(False)

        self.tab_btns = {}
        for sec, label in SECTION_LABELS.items():
            col = SECTION_COLORS[sec]
            btn = tk.Button(
                tab_bar, text=label,
                font=("Segoe UI", 10, "bold"),
                bg=BG_HEADER, fg=TEXT_MUTED,
                activebackground=BG_CARD,
                activeforeground=col["accent"],
                relief="flat", cursor="hand2",
                padx=22, pady=10,
                command=lambda s=sec: self._switch_section(s))
            btn.pack(side="left")
            self.tab_btns[sec] = btn

        self._highlight_tab(self.active_section)

        # Ticker strip
        ticker_frame = tk.Frame(self.root, bg=ACCENT2, height=28)
        ticker_frame.pack(fill="x", side="top")
        ticker_frame.pack_propagate(False)
        self.ticker_lbl = tk.Label(
            ticker_frame,
            text="  ⚡ LIVE  •  Loading all feeds…",
            font=("Courier", 9, "bold"), bg=ACCENT2, fg=TEXT_WHITE, anchor="w")
        self.ticker_lbl.pack(fill="x", padx=8, pady=4)

    def _highlight_tab(self, section):
        for sec, btn in self.tab_btns.items():
            col = SECTION_COLORS[sec]
            if sec == section:
                btn.configure(bg=BG_CARD, fg=col["accent"])
            else:
                btn.configure(bg=BG_HEADER, fg=TEXT_MUTED)

    def _build_body(self):
        self.body = tk.Frame(self.root, bg=BG_DARK)
        self.body.pack(fill="both", expand=True, pady=(4, 0))

        # Sidebar
        self.sidebar = tk.Frame(self.body, bg=BG_SIDEBAR, width=200)
        self.sidebar.pack(fill="y", side="left")
        self.sidebar.pack_propagate(False)

        # Main content area
        self.content = tk.Frame(self.body, bg=BG_DARK)
        self.content.pack(fill="both", expand=True, padx=6)

        self._build_dashboard_frame()
        self._build_article_frame()
        self._rebuild_sidebar(self.active_section)
        self._show_dashboard()

    def _rebuild_sidebar(self, section):
        for w in self.sidebar.winfo_children():
            w.destroy()

        col = SECTION_COLORS[section]

        # Colored section header
        sh = tk.Frame(self.sidebar, bg=col["badge_bg"])
        sh.pack(fill="x")
        tk.Label(sh, text=f"{col['icon']}  {section.upper()}",
                 font=("Courier", 9, "bold"), bg=col["badge_bg"], fg=col["accent"]
                 ).pack(padx=14, pady=10, anchor="w")

        tk.Label(self.sidebar, text="CATEGORIES", font=("Courier", 9, "bold"),
                 bg=BG_SIDEBAR, fg=TEXT_MUTED).pack(pady=(16, 6), padx=16, anchor="w")

        # All Articles button
        self._sidebar_btn("🏠  All Articles", lambda: self._apply_filter(None), section)

        # Sub-category buttons
        for label, kw in SECTION_SUBCATS[section]:
            self._sidebar_btn(label, lambda k=kw: self._apply_filter(k), section)

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", pady=12, padx=12)
        tk.Label(self.sidebar, text="LIVE SOURCES", font=("Courier", 9, "bold"),
                 bg=BG_SIDEBAR, fg=TEXT_MUTED).pack(padx=16, anchor="w")

        for url in SECTION_FEEDS[section]:
            src = urllib.parse.urlparse(url).netloc.replace("www.", "")
            tk.Label(self.sidebar, text=f"  • {src}",
                     font=("Segoe UI", 8), bg=BG_SIDEBAR, fg=TEXT_MUTED
                     ).pack(anchor="w", padx=12, pady=2)

    def _sidebar_btn(self, label, cmd, section):
        col = SECTION_COLORS[section]
        btn = tk.Button(
            self.sidebar, text=f"  {label}", font=("Segoe UI", 10),
            bg=BG_SIDEBAR, fg=TEXT_PRIMARY,
            activebackground=BG_CARD, activeforeground=col["accent"],
            relief="flat", anchor="w", cursor="hand2",
            padx=14, pady=7, command=cmd)
        btn.pack(fill="x")
        btn.bind("<Enter>", lambda e, b=btn: b.configure(fg=col["accent"]))
        btn.bind("<Leave>", lambda e, b=btn: b.configure(fg=TEXT_PRIMARY))

    def _build_dashboard_frame(self):
        self.dash_frame = tk.Frame(self.content, bg=BG_DARK)

        # Canvas + Scrollbar
        self.canvas = tk.Canvas(self.dash_frame, bg=BG_DARK, highlightthickness=0)
        vsb = ttk.Scrollbar(self.dash_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.cards_frame = tk.Frame(self.canvas, bg=BG_DARK)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")

        self.cards_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>",      self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>",  self._on_mousewheel)

    def _build_article_frame(self):
        self.art_frame = tk.Frame(self.content, bg=BG_DARK)

        # Back bar
        back_bar = tk.Frame(self.art_frame, bg=BG_HEADER, height=46)
        back_bar.pack(fill="x")
        back_bar.pack_propagate(False)

        tk.Button(back_bar, text="← Back to Dashboard",
                  font=("Segoe UI", 10), bg=BG_HEADER, fg=ACCENT,
                  activebackground=BG_CARD, activeforeground=ACCENT,
                  relief="flat", cursor="hand2", padx=14,
                  command=self._show_dashboard).pack(side="left", pady=8)

        self.art_hindi_btn = tk.Button(
            back_bar, text="🇮🇳  Translate to हिंदी",
            font=("Segoe UI", 10, "bold"), bg="#1a2236", fg=GOLD,
            activebackground="#253050", activeforeground=GOLD,
            relief="flat", cursor="hand2", padx=12,
            command=self._translate_article)
        self.art_hindi_btn.pack(side="right", padx=10, pady=8)

        tk.Button(back_bar, text="🌐  Open in Browser",
                  font=("Segoe UI", 10), bg=ACCENT2, fg=TEXT_WHITE,
                  activebackground=ACCENT, activeforeground=TEXT_WHITE,
                  relief="flat", cursor="hand2", padx=12,
                  command=self._open_in_browser
                  ).pack(side="right", padx=4, pady=8)

        # Article scroll area
        art_canvas = tk.Canvas(self.art_frame, bg=BG_DARK, highlightthickness=0)
        art_vsb    = ttk.Scrollbar(self.art_frame, orient="vertical", command=art_canvas.yview)
        art_canvas.configure(yscrollcommand=art_vsb.set)
        art_vsb.pack(side="right", fill="y")
        art_canvas.pack(side="left", fill="both", expand=True)

        self.art_inner = tk.Frame(art_canvas, bg=BG_DARK)
        self._art_win  = art_canvas.create_window((0, 0), window=self.art_inner, anchor="nw")

        self.art_inner.bind("<Configure>", lambda e: art_canvas.configure(
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
        tk.Label(sb, text="ChainPulse v2.0  •  Blockchain · AI · Hacking · Tech",
                 font=("Courier", 8), bg=BG_HEADER, fg=TEXT_MUTED
                 ).pack(side="right", padx=12)

    # ── Section Switching ──────────────────────────────────────

    def _switch_section(self, section):
        self.active_section = section
        self._highlight_tab(section)
        self._rebuild_sidebar(section)

        col  = SECTION_COLORS[section]
        arts = self.filtered.get(section) or self.data.get(section, [])
        self.current_view = "dashboard"
        self.art_frame.pack_forget()
        self.dash_frame.pack(fill="both", expand=True)
        self._render_cards(arts, section)

        if arts:
            ticker = f"  {col['icon']} {section.upper()}  •  " + \
                     "   ●   ".join(a["title"] for a in arts[:6])
            self._update_ticker(ticker)

    # ── Views ──────────────────────────────────────────────────

    def _show_dashboard(self):
        self.art_frame.pack_forget()
        self.dash_frame.pack(fill="both", expand=True)
        self.current_view = "dashboard"
        sec  = self.active_section
        arts = self.filtered.get(sec) or self.data.get(sec, [])
        self._render_cards(arts, sec)

    def _show_article(self, article):
        self.current_art  = article
        self.current_view = "article"
        self.dash_frame.pack_forget()
        self.art_frame.pack(fill="both", expand=True)
        self._render_article(article, hindi=False)

    # ── Card Rendering ─────────────────────────────────────────

    def _render_cards(self, arts, section):
        col = SECTION_COLORS[section]
        for w in self.cards_frame.winfo_children():
            w.destroy()

        if not arts:
            msg = "⏳ Loading…" if self.loading.get(section) else "No articles found."
            tk.Label(self.cards_frame, text=msg,
                     font=("Segoe UI", 14), bg=BG_DARK, fg=TEXT_MUTED
                     ).pack(pady=80)
            return

        # Section banner
        banner = tk.Frame(self.cards_frame, bg=col["badge_bg"])
        banner.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(banner,
                 text=f" {col['icon']}  {SECTION_LABELS[section].split('  ')[1].upper()}  ·  {len(arts)} articles ",
                 font=("Courier", 9, "bold"), bg=col["badge_bg"], fg=col["accent"]
                 ).pack(side="left", padx=10, pady=6)
        tk.Label(banner, text=f"Updated {datetime.now().strftime('%H:%M:%S')}",
                 font=("Courier", 8), bg=col["badge_bg"], fg=TEXT_MUTED
                 ).pack(side="right", padx=10)

        # Hero card
        self._make_hero_card(arts[0], col)

        # Grid for remaining articles
        grid = tk.Frame(self.cards_frame, bg=BG_DARK)
        grid.pack(fill="x", padx=10, pady=6)

        for i, art in enumerate(arts[1:], 1):
            col_idx = (i - 1) % 3
            row_idx = (i - 1) // 3
            self._make_grid_card(grid, art, row_idx, col_idx, col)

        for c in range(3):
            grid.columnconfigure(c, weight=1)

    def _make_hero_card(self, art, col):
        card = tk.Frame(self.cards_frame, bg=BG_CARD, cursor="hand2")
        card.pack(fill="x", padx=10, pady=(4, 6))

        # Accent left bar
        bar = tk.Frame(card, bg=col["accent"], width=4)
        bar.pack(side="left", fill="y")

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="x", padx=20, pady=16, side="left", expand=True)

        # Badge
        badge_f = tk.Frame(inner, bg=col["badge_bg"])
        badge_f.pack(anchor="w", pady=(0, 8))
        tk.Label(badge_f,
                 text=f" {col['icon']} FEATURED  •  {art['source'].upper()} ",
                 font=("Courier", 8, "bold"), bg=col["badge_bg"], fg=col["accent"]
                 ).pack(padx=4, pady=2)

        title = tk.Label(inner, text=art["title"],
                         font=("Georgia", 16, "bold"), bg=BG_CARD, fg=TEXT_WHITE,
                         wraplength=900, justify="left", cursor="hand2")
        title.pack(anchor="w", pady=(0, 6))

        desc = tk.Label(inner, text=art["desc"],
                        font=("Segoe UI", 10), bg=BG_CARD, fg=TEXT_MUTED,
                        wraplength=900, justify="left")
        desc.pack(anchor="w")

        meta = tk.Frame(inner, bg=BG_CARD)
        meta.pack(anchor="w", pady=(10, 0))
        tk.Label(meta, text=f"📡 {art['source']}",
                 font=("Courier", 8), bg=BG_CARD, fg=col["accent"]).pack(side="left")
        tk.Label(meta,
                 text=f"   🕐 {art['pub'][:25] if art['pub'] else 'Recent'}",
                 font=("Courier", 8), bg=BG_CARD, fg=TEXT_MUTED).pack(side="left")

        all_w = [card, inner, title, desc, meta]
        for w in all_w:
            w.bind("<Button-1>", lambda e, a=art: self._show_article(a))
        self._hover_effect(card, all_w)

    def _make_grid_card(self, parent, art, row, col_idx, col):
        card = tk.Frame(parent, bg=BG_CARD, cursor="hand2", relief="flat")
        card.grid(row=row, column=col_idx, padx=5, pady=5, sticky="nsew")

        # Top accent line
        tk.Frame(card, bg=col["accent"], height=2).pack(fill="x")

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="both", padx=14, pady=12)

        src_bar = tk.Frame(inner, bg=BG_CARD)
        src_bar.pack(fill="x", pady=(0, 6))
        tk.Label(src_bar, text=f"● {art['source'].upper()}",
                 font=("Courier", 7, "bold"), bg=BG_CARD, fg=col["dim"]
                 ).pack(side="left")

        title = tk.Label(inner, text=art["title"],
                         font=("Georgia", 11, "bold"), bg=BG_CARD, fg=TEXT_WHITE,
                         wraplength=280, justify="left", cursor="hand2")
        title.pack(anchor="w", pady=(0, 6))

        short = art["desc"][:120] + "…" if len(art["desc"]) > 120 else art["desc"]
        desc = tk.Label(inner, text=short,
                        font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_MUTED,
                        wraplength=280, justify="left")
        desc.pack(anchor="w")

        tk.Label(inner, text=art["pub"][:16] if art["pub"] else "",
                 font=("Courier", 7), bg=BG_CARD, fg=TEXT_MUTED
                 ).pack(anchor="e", pady=(8, 0))

        all_w = [card, inner, title, desc]
        for w in all_w:
            w.bind("<Button-1>", lambda e, a=art: self._show_article(a))
        self._hover_effect(card, all_w)

    def _hover_effect(self, card, widgets):
        def on_enter(e):
            card.configure(bg=BG_CARD_HOVER)
            for w in widgets:
                try:    w.configure(bg=BG_CARD_HOVER)
                except: pass
        def on_leave(e):
            card.configure(bg=BG_CARD)
            for w in widgets:
                try:    w.configure(bg=BG_CARD)
                except: pass
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

    # ── Article Rendering ──────────────────────────────────────

    def _render_article(self, article, hindi=False):
        for w in self.art_inner.winfo_children():
            w.destroy()

        sec = article.get("section", self.active_section)
        col = SECTION_COLORS[sec]

        pad = tk.Frame(self.art_inner, bg=BG_DARK)
        pad.pack(fill="x", padx=60, pady=30)

        # Section tag + source + date
        top = tk.Frame(pad, bg=BG_DARK)
        top.pack(anchor="w", pady=(0, 12))
        tk.Label(top, text=f" {col['icon']} {sec.upper()} ",
                 font=("Courier", 9, "bold"), bg=col["badge_bg"], fg=col["accent"]
                 ).pack(side="left", ipadx=4, ipady=2)
        tk.Label(top, text=f"  {article['source'].upper()}",
                 font=("Courier", 9, "bold"), bg=BG_DARK, fg=col["dim"]
                 ).pack(side="left")
        tk.Label(top, text=f"   {article['pub'][:30] if article['pub'] else 'Recent'}",
                 font=("Courier", 9), bg=BG_DARK, fg=TEXT_MUTED).pack(side="left")

        # Title
        title_text = article.get("title_hi", article["title"]) if hindi else article["title"]
        tk.Label(pad, text=title_text,
                 font=("Georgia", 20, "bold"), bg=BG_DARK, fg=TEXT_WHITE,
                 wraplength=900, justify="left").pack(anchor="w", pady=(0, 16))

        # Colored divider
        tk.Frame(pad, bg=col["accent"], height=3).pack(fill="x", pady=(0, 20))

        # Body
        body_text = article.get("body_hi", article["full_desc"]) if hindi else article["full_desc"]
        body_text = body_text or "No content available. Please open in browser for the full article."

        tk.Label(pad, text=body_text,
                 font=("Georgia", 12), bg=BG_DARK, fg=TEXT_PRIMARY,
                 wraplength=900, justify="left").pack(anchor="w", pady=(0, 20))

        # Footer note
        tk.Label(pad,
                 text="ℹ  This is the article preview from RSS feed. Click 'Open in Browser' for the full article.",
                 font=("Segoe UI", 9), bg=BG_DARK, fg=TEXT_MUTED,
                 wraplength=900, justify="left").pack(anchor="w")

        self._art_canvas.yview_moveto(0)

    # ── Actions ────────────────────────────────────────────────

    def _apply_filter(self, keyword):
        sec = self.active_section
        if keyword:
            self.filtered[sec] = [
                a for a in self.data[sec]
                if keyword in (a["title"] + a["desc"]).lower()
            ]
        else:
            self.filtered[sec] = list(self.data[sec])
        if self.current_view == "dashboard":
            self._render_cards(self.filtered[sec], sec)

    def _on_search(self, *_):
        q   = self.search_var.get().lower()
        sec = self.active_section
        if q:
            self.filtered[sec] = [
                a for a in self.data[sec]
                if q in (a["title"] + a["desc"]).lower()
            ]
        else:
            self.filtered[sec] = list(self.data[sec])
        if self.current_view == "dashboard":
            self._render_cards(self.filtered[sec], sec)

    def _toggle_hindi(self):
        if self.current_view == "article" and self.current_art:
            self._translate_article()

    def _translate_article(self):
        if not self.current_art:
            return
        art = self.current_art
        # Already translated — just show it
        if "body_hi" in art:
            self._render_article(art, hindi=True)
            self.art_hindi_btn.configure(
                text="🔤  Show English", command=self._show_english)
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

    # ── Data Loading ───────────────────────────────────────────

    def _load_all_async(self):
        self.status_lbl.configure(text="⏳ Fetching all feeds…")
        self._update_ticker("  ⚡ LIVE  •  Fetching Blockchain · AI · Hacking · Tech feeds…")
        for sec in SECTION_FEEDS:
            self.loading[sec] = True
            threading.Thread(target=self._load_one, args=(sec,), daemon=True).start()

    def _load_one(self, section):
        arts = fetch_section(section)
        self.root.after(0, lambda s=section, a=arts: self._on_loaded(s, a))

    def _on_loaded(self, section, arts):
        self.loading[section]  = False
        self.data[section]     = arts
        self.filtered[section] = list(arts)

        col          = SECTION_COLORS[section]
        count        = len(arts)
        total_loaded = sum(len(v) for v in self.data.values())
        still_loading = any(self.loading.values())

        if not still_loading:
            self.status_lbl.configure(
                text=f"✅ All feeds loaded  •  {total_loaded} articles  •  {datetime.now().strftime('%H:%M:%S')}")
        else:
            self.status_lbl.configure(
                text=f"⏳ Loading…  {section} done ({count} articles)")

        if section == self.active_section and self.current_view == "dashboard":
            self._render_cards(arts, section)
            ticker = f"  {col['icon']} {section.upper()}  •  " + \
                     "   ●   ".join(a["title"] for a in arts[:6])
            self._update_ticker(ticker)

    def _update_ticker(self, text):
        self.ticker_lbl.configure(text=text)

    # ── Canvas Helpers ─────────────────────────────────────────

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

    app = ChainPulseApp(root)
    root.mainloop()
