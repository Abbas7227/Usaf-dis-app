import customtkinter as c
import tkinter as tk
from PIL import Image, ImageDraw

# --- Base Colors ---
BG_DARK = "#0f1a3c"
BG_MID = "#16275f"
BG_LIGHT = "#1c2a5e"
ACCENT = "#2a3b6e"
TEXT = "#ffffff"

#/--Logo--\#
logo_i = Image.open("logo.png").resize((317, 281))
logo = c.CTkImage(light_image=logo_i, size=logo_i.size)
#\--Logo--/#

# --- Load Map Image ---
map_image = Image.open("map.png").resize((635, 491)).copy()
map_state = {
    "image": map_image,
    "draw": ImageDraw.Draw(map_image),
    "ctk_image": c.CTkImage(light_image=map_image, size=(635, 491))
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

# --- Flight Plan Tab ---
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

    c.CTkLabel(header, text="Flight Plan Editor", text_color=TEXT,
               font=("Segoe UI", 16, "bold")).place(x=15, y=10)

    # --- Drawing Controls ---
    c.CTkButton(header, text="Straight Line",
                command=lambda: draw_mode.update(mode="straight"),
                width=100, height=30, fg_color=BG_LIGHT, hover_color=ACCENT).place(x=180, y=10)

    c.CTkButton(header, text="Freehand",
                command=lambda: draw_mode.update(mode="freehand"),
                width=100, height=30, fg_color=BG_LIGHT, hover_color=ACCENT).place(x=290, y=10)

    # --- Eraser Button ---
    c.CTkButton(header, text="Eraser",
                command=lambda: draw_mode.update(mode="eraser"),
                width=100, height=30, fg_color="#bb2a2a", hover_color="#dd4444").place(x=400, y=10)

    # --- Eraser Size Slider ---
    eraser_slider = c.CTkSlider(header, from_=5, to=40, number_of_steps=7, width=100,
                                command=lambda v: eraser_size.update(size=int(v)))
    eraser_slider.place(x=510, y=18)
    eraser_slider.set(10)

    # --- Color Picker ---
    def change_color(choice):
        current_draw_color["color"] = draw_colors[choice]

    color_picker = c.CTkOptionMenu(bg, values=list(draw_colors.keys()), command=change_color, width=120, fg_color=BG_LIGHT, button_color=ACCENT, text_color=TEXT, dropdown_fg_color=ACCENT,)
    color_picker.set("Black")
    color_picker.place(x=30, y=70)

    # --- Map Area ---
    map_frame = c.CTkFrame(bg, fg_color=BG_MID, corner_radius=20, width=640, height=470)
    map_frame.place(x=30, y=110)

    map_label = c.CTkLabel(map_frame, image=map_state["ctk_image"], text="", fg_color="transparent", width=635, height=460)
    map_label.place(x=2, y=2)

    # --- Drawing Logic ---
    start_point = {"x": None, "y": None}

    def refresh_map():
        map_state["ctk_image"] = c.CTkImage(light_image=map_state["image"], size=(635, 491))
        map_label.configure(image=map_state["ctk_image"])
        map_label.image = map_state["ctk_image"]

    def update_preview(x0, y0, x1, y1):
        preview_image = map_state["image"].copy()
        preview_draw = ImageDraw.Draw(preview_image)
        preview_draw.line((x0, y0, x1, y1), fill=current_draw_color["color"], width=2)
        preview_ctk = c.CTkImage(light_image=preview_image, size=(635, 491))
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
        """Draw a small circle of map background color (like eraser)."""
        r = eraser_size["size"]
        # Sample from original map to restore background under brush
        base = Image.open("map.png").resize((635, 491))
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
                map_state["draw"].line((x0, y0, x1, y1),
                                       fill=current_draw_color["color"], width=2)
                start_point["x"], start_point["y"] = x1, y1
                refresh_map()
            elif draw_mode["mode"] == "eraser":
                erase(x1, y1)
                start_point["x"], start_point["y"] = x1, y1

    def on_mouse_up(event):
        x0, y0 = start_point["x"], start_point["y"]
        x1, y1 = event.x, event.y
        if draw_mode["mode"] == "straight" and None not in (x0, y0, x1, y1):
            map_state["draw"].line((x0, y0, x1, y1),
                                   fill=current_draw_color["color"], width=2)
            refresh_map()

    map_label.bind("<ButtonPress-1>", on_mouse_down)
    map_label.bind("<B1-Motion>", on_mouse_drag)
    map_label.bind("<ButtonRelease-1>", on_mouse_up)


# --- Flight Planner Tab ---
def flight_planner_tab():
    planner = c.CTkFrame(window, width=700, height=550, fg_color=BG_DARK, corner_radius=0)
    tab_frames["Flight Planner"] = planner

    font_small = ("Segoe UI", 13)
    font_label = ("Segoe UI", 12, "bold")
    entry_h = 35

    # --- Section 1: Flight Info Box ---
    info_box = c.CTkFrame(planner, width=640, height=190, fg_color=BG_MID,corner_radius=15, border_width=1, border_color=ACCENT)
    info_box.place(x=30, y=20)

    c.CTkLabel(info_box, text="Flight Information", text_color="#9aa0b3",font=font_label).place(x=25, y=5)

    call_sign = c.CTkEntry(info_box, placeholder_text="Call Sign", width=200, height=entry_h,fg_color=BG_LIGHT, border_color=ACCENT, border_width=1,text_color=TEXT, font=font_small)
    call_sign.place(x=20, y=35)

    update_btn = c.CTkButton(info_box, text="Update 🛠️", width=120, height=35,fg_color=ACCENT, hover_color="#364b87",border_color=ACCENT, border_width=1,text_color=TEXT, font=("Segoe UI", 14, "bold"))
    update_btn.place(x=240, y=35)

    # Row 1
    dep = c.CTkEntry(info_box, placeholder_text="Departure ICAO", width=150, height=entry_h,fg_color=BG_LIGHT, border_color=ACCENT, text_color=TEXT, font=font_small)
    dep.place(x=30, y=90)

    aircraft = c.CTkEntry(info_box, placeholder_text="Aircraft", width=150, height=entry_h,fg_color=BG_LIGHT, border_color=ACCENT, text_color=TEXT, font=font_small)
    aircraft.place(x=200, y=90)

    role = c.CTkEntry(info_box, placeholder_text="Role", width=150, height=entry_h,fg_color=BG_LIGHT, border_color=ACCENT, text_color=TEXT, font=font_small)
    role.place(x=370, y=90)

    # Row 2
    arr = c.CTkEntry(info_box, placeholder_text="Arrival ICAO", width=150, height=entry_h,fg_color=BG_LIGHT, border_color=ACCENT, text_color=TEXT, font=font_small)
    arr.place(x=30, y=135)

    cruising = c.CTkEntry(info_box, placeholder_text="Cruising Alt", width=150, height=entry_h,fg_color=BG_LIGHT, border_color=ACCENT, text_color=TEXT, font=font_small)
    cruising.place(x=200, y=135)

    initial = c.CTkEntry(info_box, placeholder_text="Initial Alt", width=150, height=entry_h,fg_color=BG_LIGHT, border_color=ACCENT, text_color=TEXT, font=font_small)
    initial.place(x=370, y=135)

    # --- Section 2: Mission Data Box ---
    bottom_box = c.CTkFrame(planner, width=640, height=300, fg_color=BG_MID,corner_radius=15, border_width=1, border_color=ACCENT)
    bottom_box.place(x=30, y=230)

    c.CTkLabel(bottom_box, text="Mission Data", text_color="#9aa0b3",font=font_label).place(x=25, y=5)

    mission_box = c.CTkTextbox(bottom_box, width=280, height=100,fg_color=BG_LIGHT, border_color=ACCENT,border_width=1, text_color=TEXT, font=font_small)
    mission_box.place(x=25, y=30)

    your_objective = c.CTkTextbox(bottom_box, width=280, height=100,fg_color=BG_LIGHT, border_color=ACCENT,border_width=1, text_color=TEXT, font=font_small)
    your_objective.place(x=25, y=150)

    notams = c.CTkTextbox(bottom_box, width=280, height=220,fg_color=BG_LIGHT, border_color=ACCENT,border_width=1, text_color=TEXT, font=font_small)
    notams.place(x=330, y=30)

    placeholders = {
        mission_box: "mission objective",
        your_objective: "your objective",
        notams: "notams / notes"
    }

    for text_box, placeholder in placeholders.items():
        text_box.insert("1.0", placeholder)
        text_box.configure(text_color="#9aa0b3")

        def on_focus_in(event, tb=text_box, ph=placeholder):
            if tb.get("1.0", "end-1c") == ph:
                tb.delete("1.0", "end")
                tb.configure(text_color=TEXT)

        def on_focus_out(event, tb=text_box, ph=placeholder):
            if tb.get("1.0", "end-1c").strip() == "":
                tb.insert("1.0", ph)
                tb.configure(text_color="#9aa0b3")

        text_box.bind("<FocusIn>", on_focus_in)
        text_box.bind("<FocusOut>", on_focus_out)



# --- Initialize ---
flight_plan_visualizer()
flight_planner_tab()
show_tab("Flight Plan")

window.mainloop()
