import customtkinter as c
import tkinter
import tkinter.simpledialog as sd
from tkinter import messagebox
from PIL import Image, ImageDraw
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import traceback

# -------------------------
# Firebase init (expects firebase_config.json in same folder)
# -------------------------
FIREBASE_ENABLED = False
try:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    FIREBASE_ENABLED = True
    print("Firebase initialized.")
except Exception as e:
    print("Firebase init failed (continuing in offline mode):", e)
    traceback.print_exc()

# --- Base Colors ---
BG_DARK = "#0f1a3c"
BG_MID = "#16275f"
BG_LIGHT = "#1c2a5e"
ACCENT = "#2a3b6e"
TEXT = "#ffffff"

# --- Load Map Image ---
map_image = Image.open("map.png").resize((595, 451)).copy()
map_state = {
    "image": map_image,
    "draw": ImageDraw.Draw(map_image),
    "ctk_image": c.CTkImage(light_image=map_image, size=(595, 451))
}

# --- Window ---
window = c.CTk()
window.geometry("700x600+1200+0")
window.title("USAF Mission Planner")
window.resizable(False, False)

# --- Tab Manager ---
active_tab = {"name": "Flight Plan"}
tab_frames = {}


def show_tab(name):
    active_tab["name"] = name
    for t_name, frame in tab_frames.items():
        frame.place_forget()
    tab_frames[name].place(x=0, y=50)
    update_tab_styles()
    # If announcements tab shown, refresh
    if name == "Announcements":
        try:
            display_announcements()
        except Exception as e:
            print("Error refreshing announcements:", e)


tabs_holder = c.CTkFrame(window, height=50, width=700, fg_color=BG_MID, corner_radius=0)
tabs_holder.place(x=0, y=0)

tab_buttons = {}


def create_tab_button(name, x):
    btn = c.CTkButton(
        tabs_holder, text=name, width=120, height=30,
        corner_radius=15, fg_color=BG_LIGHT, hover_color=ACCENT,
        text_color=TEXT, font=("Segoe UI", 14, "bold"),
        command=lambda: show_tab(name)
    )
    btn.place(x=x, y=10)
    tab_buttons[name] = btn


def update_tab_styles():
    for name, btn in tab_buttons.items():
        btn.configure(fg_color=ACCENT if name == active_tab["name"] else BG_LIGHT)


create_tab_button("Flight Plan", 20)
create_tab_button("Flight Planner", 160)
create_tab_button("Announcements", 300)


# -------------------------
# Flight Plan Tab
# -------------------------
def flight_plan_visualizer():
    draw_colors = {
        "Red": "#dd3754",
        "Blue": "#3156dd",
        "Green": "#23ca38",
        "Yellow": "#e3e32d",
        "Black": "#000000",
        "White": "#ffffff",
    }
    current_draw_color = {"color": draw_colors["Black"]}
    draw_mode = {"mode": "straight"}

    # --- Eraser ---
    eraser_size = {"size": 10}

    bg = c.CTkFrame(window, width=700, height=550, fg_color=BG_DARK, corner_radius=0)
    tab_frames["Flight Plan"] = bg

    # --- Header Bar ---
    header = c.CTkFrame(bg, fg_color=BG_MID, corner_radius=15, width=640, height=50)
    header.place(x=30, y=10)

    c.CTkLabel(header, text="Flight Plan Editor", text_color=TEXT, font=("Segoe UI", 16, "bold")).place(x=15, y=10)
    c.CTkButton(header, text="Straight Line", command=lambda: draw_mode.update(mode="straight"), width=100, height=30,
                fg_color=BG_LIGHT, hover_color=ACCENT).place(x=180, y=10)
    c.CTkButton(header, text="Freehand", command=lambda: draw_mode.update(mode="freehand"), width=100, height=30,
                fg_color=BG_LIGHT, hover_color=ACCENT).place(x=290, y=10)
    c.CTkButton(header, text="Eraser", command=lambda: draw_mode.update(mode="eraser"), width=100, height=30,
                fg_color="#bb2a2a", hover_color="#dd4444").place(x=400, y=10)
    eraser_slider = c.CTkSlider(header, from_=5, to=40, number_of_steps=7, width=100,
                                command=lambda v: eraser_size.update(size=int(v)))
    eraser_slider.place(x=510, y=18);
    eraser_slider.set(10)

    def change_color(choice):
        current_draw_color["color"] = draw_colors[choice]

    color_picker = c.CTkOptionMenu(bg, values=list(draw_colors.keys()), command=change_color, width=120,
                                   fg_color=BG_LIGHT, button_color=ACCENT, text_color=TEXT, dropdown_fg_color=ACCENT, )
    color_picker.set("Black");
    color_picker.place(x=30, y=70)

    # --- Map Area ---
    map_frame = c.CTkFrame(bg, fg_color=BG_MID, corner_radius=20, width=595, height=451)
    map_frame.place(x=52, y=110)

    map_label = c.CTkLabel(map_frame, image=map_state["ctk_image"], text="", fg_color="transparent", width=595,
                           height=451)
    map_label.place(x=0, y=0)

    # --- Drawing Logic ---
    start_point = {"x": None, "y": None}

    def refresh_map():
        map_state["ctk_image"] = c.CTkImage(light_image=map_state["image"], size=(595, 451))
        map_label.configure(image=map_state["ctk_image"])
        map_label.image = map_state["ctk_image"]

    def update_preview(x0, y0, x1, y1):
        preview_image = map_state["image"].copy()
        preview_draw = ImageDraw.Draw(preview_image)
        preview_draw.line((x0, y0, x1, y1), fill=current_draw_color["color"], width=2)
        preview_ctk = c.CTkImage(light_image=preview_image, size=(595, 451))
        map_label.configure(image=preview_ctk)
        map_label.image = preview_ctk

    def on_mouse_down(event):
        start_point["x"], start_point["y"] = event.x, event.y
        if draw_mode["mode"] == "freehand":
            map_state["draw"].point((event.x, event.y), fill=current_draw_color["color"])
            refresh_map()
        elif draw_mode["mode"] == "eraser":
            erase(event.x, event.y)

    def erase(x, y):
        r = eraser_size["size"]
        base = Image.open("map.png").resize((595, 451))
        region = base.crop((x - r, y - r, x + r, y + r))
        map_state["image"].paste(region, (x - r, y - r))
        map_state["draw"] = ImageDraw.Draw(map_state["image"])
        refresh_map()

    def on_mouse_drag(event):
        x0, y0 = start_point["x"], start_point["y"]
        x1, y1 = event.x, event.y
        if None not in (x0, y0, x1, y1):
            if draw_mode["mode"] == "straight":
                update_preview(x0, y0, x1, y1)
            elif draw_mode["mode"] == "freehand":
                map_state["draw"].line((x0, y0, x1, y1), fill=current_draw_color["color"], width=2)
                start_point["x"], start_point["y"] = x1, y1
                refresh_map()
            elif draw_mode["mode"] == "eraser":
                erase(x1, y1);
                start_point["x"], start_point["y"] = x1, y1

    def on_mouse_up(event):
        x0, y0 = start_point["x"], start_point["y"]
        x1, y1 = event.x, event.y
        if draw_mode["mode"] == "straight" and None not in (x0, y0, x1, y1):
            map_state["draw"].line((x0, y0, x1, y1), fill=current_draw_color["color"], width=2)
            refresh_map()

    map_label.bind("<ButtonPress-1>", on_mouse_down)
    map_label.bind("<B1-Motion>", on_mouse_drag)
    map_label.bind("<ButtonRelease-1>", on_mouse_up)


# -------------------------
# Flight Planner Tab
# -------------------------
def flight_planner_tab():
    planner = c.CTkFrame(window, width=700, height=550, fg_color=BG_DARK, corner_radius=0)
    tab_frames["Flight Planner"] = planner

    font_small = ("Segoe UI", 13)
    font_label = ("Segoe UI", 12, "bold")
    entry_h = 35

    info_box = c.CTkFrame(planner, width=640, height=190, fg_color=BG_MID, corner_radius=15, border_width=1,
                          border_color=ACCENT)
    info_box.place(x=30, y=20)
    c.CTkLabel(info_box, text="Flight Information", text_color="#9aa0b3", font=font_label).place(x=25, y=5)

    call_sign = c.CTkEntry(info_box, placeholder_text="Call Sign", width=200, height=entry_h, fg_color=BG_LIGHT,
                           border_color=ACCENT, border_width=1, text_color=TEXT, font=font_small)
    call_sign.place(x=20, y=35)

    update_btn = c.CTkButton(info_box, text="Update 🛠️", width=120, height=35, fg_color=ACCENT, hover_color="#364b87",
                             border_color=ACCENT, border_width=1, text_color=TEXT, font=("Segoe UI", 14, "bold"))
    update_btn.place(x=240, y=35)

    dep = c.CTkEntry(info_box, placeholder_text="Departure ICAO", width=150, height=entry_h, fg_color=BG_LIGHT,
                     border_color=ACCENT, text_color=TEXT, font=font_small)
    dep.place(x=30, y=90)
    aircraft = c.CTkEntry(info_box, placeholder_text="Aircraft", width=150, height=entry_h, fg_color=BG_LIGHT,
                          border_color=ACCENT, text_color=TEXT, font=font_small)
    aircraft.place(x=200, y=90)
    role = c.CTkEntry(info_box, placeholder_text="Role", width=150, height=entry_h, fg_color=BG_LIGHT,
                      border_color=ACCENT, text_color=TEXT, font=font_small)
    role.place(x=370, y=90)

    arr = c.CTkEntry(info_box, placeholder_text="Arrival ICAO", width=150, height=entry_h, fg_color=BG_LIGHT,
                     border_color=ACCENT, text_color=TEXT, font=font_small)
    arr.place(x=30, y=135)
    cruising = c.CTkEntry(info_box, placeholder_text="Cruising Alt", width=150, height=entry_h, fg_color=BG_LIGHT,
                          border_color=ACCENT, text_color=TEXT, font=font_small)
    cruising.place(x=200, y=135)
    initial = c.CTkEntry(info_box, placeholder_text="Initial Alt", width=150, height=entry_h, fg_color=BG_LIGHT,
                         border_color=ACCENT, text_color=TEXT, font=font_small)
    initial.place(x=370, y=135)

    bottom_box = c.CTkFrame(planner, width=640, height=300, fg_color=BG_MID, corner_radius=15, border_width=1,
                            border_color=ACCENT)
    bottom_box.place(x=30, y=230)
    c.CTkLabel(bottom_box, text="Mission Data", text_color="#9aa0b3", font=font_label).place(x=25, y=5)

    mission_box = c.CTkTextbox(bottom_box, width=280, height=100, fg_color=BG_LIGHT, border_color=ACCENT,
                               border_width=1, text_color=TEXT, font=font_small)
    mission_box.place(x=25, y=30)
    your_objective = c.CTkTextbox(bottom_box, width=280, height=100, fg_color=BG_LIGHT, border_color=ACCENT,
                                  border_width=1, text_color=TEXT, font=font_small)
    your_objective.place(x=25, y=150)
    notams = c.CTkTextbox(bottom_box, width=280, height=220, fg_color=BG_LIGHT, border_color=ACCENT, border_width=1,
                          text_color=TEXT, font=font_small)
    notams.place(x=330, y=30)

    placeholders = {mission_box: "mission objective", your_objective: "your objective", notams: "notams / notes"}
    for text_box, placeholder in placeholders.items():
        text_box.insert("1.0", placeholder);
        text_box.configure(text_color="#9aa0b3")

        def on_focus_in(event, tb=text_box, ph=placeholder):
            if tb.get("1.0", "end-1c") == ph: tb.delete("1.0", "end"); tb.configure(text_color=TEXT)

        def on_focus_out(event, tb=text_box, ph=placeholder):
            if tb.get("1.0", "end-1c").strip() == "": tb.insert("1.0", ph); tb.configure(text_color="#9aa0b3")

        text_box.bind("<FocusIn>", on_focus_in);
        text_box.bind("<FocusOut>", on_focus_out)


# -------------------------
# Warning helper
# -------------------------
def warn(message):
    warn_win = c.CTkToplevel(window)
    warn_win.title("⚠ Warning")
    warn_win.geometry("300x150+1250+400")
    warn_win.resizable(False, False)
    warn_win.configure(fg_color=BG_MID)
    c.CTkLabel(warn_win, text="Warning", text_color="#ffcc00", font=("Segoe UI", 20, "bold"),
               fg_color="transparent").place(x=20, y=15)
    c.CTkLabel(warn_win, text=message, text_color=TEXT, font=("Segoe UI", 14), fg_color="transparent", wraplength=260,
               justify="left").place(x=20, y=55)
    c.CTkButton(warn_win, text="OK", width=80, height=28, fg_color=ACCENT, hover_color="#364b87",
                command=warn_win.destroy).place(x=110, y=110)


# -------------------------
# Announcements Tab - Fixed Delete Functionality
# -------------------------
ANN_ADMIN_CODE = "BLUEFALCON"


def announcements_tab():
    ann = c.CTkFrame(window, width=700, height=550, fg_color=BG_DARK, corner_radius=0)
    tab_frames["Announcements"] = ann

    # Main announcements area with 3 fixed bars
    main_panel = c.CTkFrame(ann, width=607, height=500, fg_color=BG_DARK,
                            border_color=ACCENT, border_width=2, corner_radius=20)
    main_panel.place(x=73, y=31)

    # Title
    c.CTkLabel(main_panel, text="ANNOUNCEMENTS", text_color=TEXT,
               font=("Segoe UI", 20, "bold")).place(x=30, y=20)

    # Create 3 announcement bars
    ann_bars = []
    bar_y_positions = [70, 190, 310]

    for i in range(3):
        bar = create_announcement_bar(main_panel, 30, bar_y_positions[i])
        ann_bars.append(bar)

    # Store references for updating
    ann.ann_bars = ann_bars

    # Settings column on the right
    setting_box = c.CTkFrame(ann, width=56, height=500, fg_color=BG_DARK,
                             border_color=ACCENT, border_width=2, corner_radius=20)
    setting_box.place(x=10, y=31)

    # Pin logic
    pinned = {"state": False}

    def pin():
        pinned["state"] = not pinned["state"]
        window.attributes("-topmost", pinned["state"])
        pin_log.configure(text="📍" if pinned["state"] else "📌")

    pin_btn = c.CTkButton(setting_box, width=40, height=40, corner_radius=10,
                          text="", fg_color=BG_LIGHT, border_color=ACCENT,
                          hover_color=ACCENT, command=pin)
    pin_btn.place(x=8, y=15)

    pin_log = c.CTkLabel(setting_box, text="📌", fg_color=BG_LIGHT,
                         bg_color="transparent", corner_radius=4, text_color=TEXT,
                         font=("Segoe UI", 14, "bold"), width=30, height=30)
    pin_log.place(x=13, y=20)

    # New announcement button
    def on_ann_btn():
        code = sd.askstring("Admin Code", "Enter announcement code:")
        if code is None:
            return
        if code != ANN_ADMIN_CODE:
            messagebox.showerror("Access Denied", "Invalid code.")
            return
        open_announcement_form()

    ann_btn = c.CTkButton(setting_box, width=40, height=40, corner_radius=10,
                          text="", fg_color=BG_LIGHT, border_color=ACCENT,
                          hover_color=ACCENT, command=on_ann_btn)
    ann_btn.place(x=8, y=65)

    ann_log = c.CTkLabel(setting_box, text="📣", fg_color=BG_LIGHT,
                         bg_color="transparent", corner_radius=4, text_color=TEXT,
                         font=("Segoe UI", 14, "bold"), width=30, height=30)
    ann_log.place(x=13, y=70)

    # Delete announcement button
    def on_delete_btn():
        code = sd.askstring("Admin Code", "Enter admin code to delete announcements:")
        if code is None:
            return
        if code != ANN_ADMIN_CODE:
            messagebox.showerror("Access Denied", "Invalid code.")
            return
        open_delete_announcements()

    delete_btn = c.CTkButton(setting_box, width=40, height=40, corner_radius=10,
                             text="", fg_color="#bb2a2a", border_color=ACCENT,
                             hover_color="#dd4444", command=on_delete_btn)
    delete_btn.place(x=8, y=115)

    delete_log = c.CTkLabel(setting_box, text="🗑️", fg_color="#bb2a2a",
                            bg_color="transparent", corner_radius=4, text_color=TEXT,
                            font=("Segoe UI", 14, "bold"), width=30, height=30)
    delete_log.place(x=13, y=120)


def create_announcement_bar(parent, x, y):
    """Create a single announcement bar with default 'waiting' content"""
    width, height = 540, 100

    # Create the main bar frame
    bar_frame = c.CTkFrame(parent, width=width, height=height,
                           fg_color=BG_LIGHT, border_color=ACCENT,
                           border_width=1, corner_radius=15)
    bar_frame.place(x=x, y=y)

    # Status indicator (left colored strip)
    status_indicator = c.CTkFrame(bar_frame, width=8, height=height - 20,
                                  fg_color="#666666", corner_radius=4)
    status_indicator.place(x=10, y=10)

    # Subject
    subject_label = c.CTkLabel(bar_frame, text="Waiting for announcement...",
                               font=("Segoe UI", 16, "bold"), text_color=TEXT,
                               fg_color="transparent", anchor="w")
    subject_label.place(x=30, y=15)

    # Details
    details_label = c.CTkLabel(bar_frame, text="No announcements available",
                               font=("Segoe UI", 12), text_color=TEXT,
                               fg_color="transparent", anchor="w", justify="left")
    details_label.place(x=30, y=45)

    # Metadata area (right side)
    meta_frame = c.CTkFrame(bar_frame, width=120, height=70,
                            fg_color=BG_DARK, corner_radius=10)
    meta_frame.place(x=width - 140, y=15)

    # Status tag
    status_tag = c.CTkLabel(meta_frame, text="---", width=100, height=25,
                            fg_color=BG_MID, text_color=TEXT,
                            font=("Segoe UI", 11, "bold"), corner_radius=8)
    status_tag.place(x=10, y=10)

    # Author/sender
    author_tag = c.CTkLabel(meta_frame, text="---", width=100, height=25,
                            fg_color=BG_MID, text_color=TEXT,
                            font=("Segoe UI", 11), corner_radius=8)
    author_tag.place(x=10, y=40)

    # Return all the updatable elements
    return {
        'frame': bar_frame,
        'status_indicator': status_indicator,
        'subject': subject_label,
        'details': details_label,
        'status_tag': status_tag,
        'author_tag': author_tag,
        'doc_id': None
    }


def update_announcement_bars(announcements_data):
    """Update the 3 announcement bars with latest data"""
    ann_frame = tab_frames.get("Announcements")
    if not ann_frame or not hasattr(ann_frame, 'ann_bars'):
        return

    ann_bars = ann_frame.ann_bars

    # Color mapping for status
    status_colors = {
        "INFO": "#3156dd",
        "ALERT": "#e3e32d",
        "WARNING": "#dd3754",
        "URGENT": "#ff00ff",
        "CRITICAL": "#ff0000",
        "MAINTENANCE": "#00ffff",
        "EXERCISE": "#00ff00",
        "WEATHER": "#ffa500",
        "SECURITY": "#800080",
        "ROUTINE": "#666666",
        "UPDATE": "#ffff00",
        "COMPLETED": "#008000"
    }

    # Update each bar
    for i, bar in enumerate(ann_bars):
        if i < len(announcements_data):
            # Has announcement data
            data = announcements_data[i]
            bar['subject'].configure(text=data.get('subject', 'No subject'))
            bar['details'].configure(text=data.get('details', 'No details'))
            bar['status_tag'].configure(text=data.get('status', 'INFO'))
            bar['author_tag'].configure(text=data.get('by_who', 'Unknown'))

            # Store document ID for deletion
            bar['doc_id'] = data.get('doc_id')

            # Update status color
            status_color = status_colors.get(data.get('status', 'INFO'), "#666666")
            bar['status_indicator'].configure(fg_color=status_color)
        else:
            # No announcement for this slot
            bar['subject'].configure(text="Waiting for announcement...")
            bar['details'].configure(text="No announcements available")
            bar['status_tag'].configure(text="---")
            bar['author_tag'].configure(text="---")
            bar['status_indicator'].configure(fg_color="#666666")
            bar['doc_id'] = None


def display_announcements():
    """Fetch announcements and update the 3 bars"""
    if not FIREBASE_ENABLED:
        # Show offline/waiting state
        update_announcement_bars([])
        return

    try:
        docs = db.collection("announcements").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
        items = []
        for d in docs:
            dat = d.to_dict()
            dat['doc_id'] = d.id  # Store document ID for deletion
            items.append(dat)

        # Take only the 3 most recent announcements
        recent_announcements = items[:3]
        update_announcement_bars(recent_announcements)

    except Exception as e:
        print("Failed to fetch announcements:", e)
        # On error, show waiting state
        update_announcement_bars([])


def open_announcement_form():
    """Popup where admin enters subject/details/status/by and then uploads to firestore."""
    form = c.CTkToplevel(window)
    form.title("New Announcement")
    form.geometry("520x400+980+300")
    form.configure(fg_color=BG_DARK)
    form.resizable(False, False)

    c.CTkLabel(form, text="Create Announcement", font=("Segoe UI", 18, "bold"), text_color=TEXT,
               fg_color="transparent").place(x=20, y=12)

    subj = c.CTkEntry(form, placeholder_text="Subject", width=460, height=40, fg_color=BG_LIGHT, border_color=ACCENT,
                      text_color=TEXT)
    subj.place(x=20, y=60)

    bywho = c.CTkEntry(form, placeholder_text="By (sender)", width=220, height=40, fg_color=BG_LIGHT,
                       border_color=ACCENT, text_color=TEXT)
    bywho.place(x=20, y=110)

    # Expanded status options
    status_options = [
        "INFO", "ALERT", "WARNING", "URGENT", "CRITICAL",
        "MAINTENANCE", "EXERCISE", "WEATHER", "SECURITY",
        "ROUTINE", "UPDATE", "COMPLETED"
    ]

    status = c.CTkOptionMenu(form, values=status_options, width=200, fg_color=BG_LIGHT, button_color=ACCENT,
                             text_color=TEXT)
    status.set("INFO")
    status.place(x=260, y=110)

    details = c.CTkTextbox(form, width=460, height=140, fg_color=BG_LIGHT, border_color=ACCENT, text_color=TEXT)
    details.place(x=20, y=160)
    details.insert("1.0", "")

    def submit():
        s = subj.get().strip()
        d = details.get("1.0", "end-1c").strip()
        st = status.get()
        b = bywho.get().strip()
        if not s:
            warn("Subject is required.")
            return
        if not d:
            warn("Details are required.")
            return
        if not b:
            warn("Sender (By) is required.")
            return

        # Upload to Firestore
        if not FIREBASE_ENABLED:
            messagebox.showerror("Firebase", "Firebase is not initialized. Put firebase_config.json in the app folder.")
            form.destroy()
            return

        try:
            doc = db.collection("announcements").document()
            doc.set({
                "subject": s,
                "details": d,
                "status": st,
                "by_who": b,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            messagebox.showinfo("Success", "Announcement posted to Firebase.")
            form.destroy()
            # Refresh the 3-bar display
            display_announcements()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to post announcement:\n{e}")

    c.CTkButton(form, text="Post Announcement", width=200, height=40, fg_color=ACCENT, hover_color="#364b87",
                command=submit).place(x=160, y=320)


def open_delete_announcements():
    """Popup to delete announcements - FIXED VERSION"""
    if not FIREBASE_ENABLED:
        messagebox.showerror("Firebase", "Firebase is not initialized.")
        return

    delete_form = c.CTkToplevel(window)
    delete_form.title("Delete Announcements")
    delete_form.geometry("500x400+1000+350")
    delete_form.configure(fg_color=BG_DARK)
    delete_form.resizable(False, False)

    c.CTkLabel(delete_form, text="Delete Announcements", font=("Segoe UI", 18, "bold"), text_color=TEXT).place(x=20,
                                                                                                               y=15)

    # Fetch current announcements
    try:
        docs = db.collection("announcements").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
        announcements_list = []
        for d in docs:
            data = d.to_dict()
            data['doc_id'] = d.id
            announcements_list.append(data)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch announcements: {e}")
        delete_form.destroy()
        return

    if not announcements_list:
        c.CTkLabel(delete_form, text="No announcements to delete", text_color=TEXT, font=("Segoe UI", 14)).place(x=20,
                                                                                                                 y=60)
        c.CTkButton(delete_form, text="Close", width=100, height=35, fg_color=ACCENT,
                    command=delete_form.destroy).place(x=200, y=350)
        return

    # Create scrollable frame for announcements
    scroll_frame = c.CTkScrollableFrame(delete_form, width=460, height=250, fg_color=BG_MID)
    scroll_frame.place(x=20, y=60)

    # Dictionary to track selected announcements
    selected_announcements = {}

    def create_announcement_item(parent, announcement, y_position):
        """Create a selectable announcement item with checkbox"""
        item_frame = c.CTkFrame(parent, width=440, height=40, fg_color=BG_LIGHT, corner_radius=8)
        item_frame.pack(pady=5, padx=10, fill="x")

        # Checkbox
        checkbox_var = c.BooleanVar()
        checkbox = c.CTkCheckBox(item_frame, text="", variable=checkbox_var,
                                 width=20, height=20, fg_color=ACCENT, hover_color=ACCENT,
                                 command=lambda: toggle_selection(announcement['doc_id'], checkbox_var.get()))
        checkbox.pack(side="left", padx=10)

        # Announcement info
        subject_text = announcement.get('subject', 'No Subject')
        if len(subject_text) > 35:
            subject_text = subject_text[:35] + "..."

        status_text = announcement.get('status', 'INFO')
        author_text = announcement.get('by_who', 'Unknown')

        info_text = f"{subject_text} | {status_text} | {author_text}"

        info_label = c.CTkLabel(item_frame, text=info_text, text_color=TEXT,
                                font=("Segoe UI", 12), anchor="w")
        info_label.pack(side="left", padx=10, fill="x", expand=True)

        # Store the checkbox variable
        selected_announcements[announcement['doc_id']] = checkbox_var

        return item_frame

    def toggle_selection(doc_id, is_selected):
        """Toggle selection state"""
        selected_announcements[doc_id].set(is_selected)

    # Create items for each announcement
    for announcement in announcements_list:
        create_announcement_item(scroll_frame, announcement, 0)

    def delete_selected():
        """Delete selected announcements"""
        selected_ids = [doc_id for doc_id, var in selected_announcements.items() if var.get()]

        if not selected_ids:
            messagebox.showwarning("Selection", "No announcements selected for deletion.")
            return

        confirm = messagebox.askyesno("Confirm Deletion",
                                      f"Are you sure you want to delete {len(selected_ids)} announcement(s)?")
        if not confirm:
            return

        try:
            for doc_id in selected_ids:
                db.collection("announcements").document(doc_id).delete()

            messagebox.showinfo("Success", f"Deleted {len(selected_ids)} announcement(s).")
            delete_form.destroy()
            display_announcements()  # Refresh the display
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete announcements: {e}")

    def delete_all():
        """Delete all announcements"""
        confirm = messagebox.askyesno("Confirm Deletion",
                                      "Are you sure you want to delete ALL announcements?")
        if not confirm:
            return

        try:
            docs = db.collection("announcements").stream()
            count = 0
            for doc in docs:
                doc.reference.delete()
                count += 1

            messagebox.showinfo("Success", f"Deleted all {count} announcements.")
            delete_form.destroy()
            display_announcements()  # Refresh the display
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete all announcements: {e}")

    # Buttons at the bottom
    button_frame = c.CTkFrame(delete_form, width=460, height=50, fg_color="transparent")
    button_frame.place(x=20, y=320)

    c.CTkButton(button_frame, text="Delete Selected", width=120, height=35,
                fg_color="#bb2a2a", hover_color="#dd4444", command=delete_selected).pack(side="left", padx=20)
    c.CTkButton(button_frame, text="Delete All", width=120, height=35,
                fg_color="#bb2a2a", hover_color="#dd4444", command=delete_all).pack(side="left", padx=20)
    c.CTkButton(button_frame, text="Close", width=120, height=35,
                fg_color=ACCENT, hover_color="#364b87", command=delete_form.destroy).pack(side="left", padx=20)


# -------------------------
# Initialize tabs and start
# -------------------------
flight_plan_visualizer()
flight_planner_tab()
announcements_tab()
show_tab("Flight Plan")

window.mainloop()
