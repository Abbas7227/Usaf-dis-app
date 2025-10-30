import customtkinter as c
import tkinter as tk
from PIL import Image, ImageDraw

# Load map image
map_image = Image.open("map.png").resize((635, 491)).copy()

# Persistent map state
map_state = {
    "image": map_image,
    "draw": ImageDraw.Draw(map_image),
    "ctk_image": c.CTkImage(light_image=map_image, size=(635, 491))
}

# Create main window
window = c.CTk()
window.geometry("700x600+1200+0")
window.title("USAF mission planner")
window.resizable(False, False)

# ✅ Set PNG icon after window is created
icon_tk = tk.PhotoImage(file="icon.png")
window.iconphoto(False, icon_tk)

# --- Drawing Tab ---
def flight_plan_visualizer():
    draw_colors = {
        "red": "#dd3754",
        "blue": "#3156dd",
        "green": "#23ca38",
        "yellow": "#e3e32d",
        "black": "#000000",
        "white": "#ffffff",
    }
    current_draw_color = draw_colors["black"]
    draw_mode = {"mode": "straight"}  # "straight" or "freehand"

    # Background frame
    bg = c.CTkFrame(window, width=700, height=600, fg_color="#323290", corner_radius=0)
    bg.place(x=0, y=0)

    # Map label
    map_label = c.CTkLabel(bg, image=map_state["ctk_image"], text="", fg_color="transparent", width=635, height=491)
    map_label.place(x=30, y=90)

    start_point = {"x": None, "y": None}

    def update_preview(x0, y0, x1, y1):
        preview_image = map_state["image"].copy()
        preview_draw = ImageDraw.Draw(preview_image)
        preview_draw.line((x0, y0, x1, y1), fill=current_draw_color, width=2)
        preview_ctk = c.CTkImage(light_image=preview_image, size=(635, 491))
        map_label.configure(image=preview_ctk)
        map_label.image = preview_ctk

    def on_mouse_down(event):
        start_point["x"] = event.x
        start_point["y"] = event.y
        if draw_mode["mode"] == "freehand":
            map_state["draw"].point((event.x, event.y), fill=current_draw_color)

    def on_mouse_drag(event):
        x0, y0 = start_point["x"], start_point["y"]
        x1, y1 = event.x, event.y
        if None not in (x0, y0, x1, y1):
            if draw_mode["mode"] == "straight":
                update_preview(x0, y0, x1, y1)
            else:
                map_state["draw"].line((x0, y0, x1, y1), fill=current_draw_color, width=2)
                start_point["x"], start_point["y"] = x1, y1
                map_state["ctk_image"] = c.CTkImage(light_image=map_state["image"], size=(635, 491))
                map_label.configure(image=map_state["ctk_image"])
                map_label.image = map_state["ctk_image"]

    def on_mouse_up(event):
        x0, y0 = start_point["x"], start_point["y"]
        x1, y1 = event.x, event.y
        if draw_mode["mode"] == "straight" and None not in (x0, y0, x1, y1):
            map_state["draw"].line((x0, y0, x1, y1), fill=current_draw_color, width=2)
            map_state["ctk_image"] = c.CTkImage(light_image=map_state["image"], size=(635, 491))
            map_label.configure(image=map_state["ctk_image"])
            map_label.image = map_state["ctk_image"]

    map_label.bind("<ButtonPress-1>", on_mouse_down)
    map_label.bind("<B1-Motion>", on_mouse_drag)
    map_label.bind("<ButtonRelease-1>", on_mouse_up)

    # --- Mode Buttons ---
    def set_straight_mode():
        draw_mode["mode"] = "straight"

    def set_freehand_mode():
        draw_mode["mode"] = "freehand"

    straight_btn = c.CTkButton(bg, text="Straight Line", command=set_straight_mode, width=100)
    straight_btn.place(x=30, y=40)

    freehand_btn = c.CTkButton(bg, text="Freehand", command=set_freehand_mode, width=100)
    freehand_btn.place(x=140, y=40)

# --- Initialize ---
flight_plan_visualizer()
tabs_holder = c.CTkScrollbar(window, fg_color="#323290", corner_radius=20, height=40, width=680, bg_color="#416690")
tabs_holder.place(x=10, y=5)

window.mainloop()