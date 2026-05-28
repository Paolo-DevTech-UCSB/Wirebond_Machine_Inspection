import tkinter as tk
import random

root = tk.Tk()
root.geometry("800x100")

# --- Canvas + Scrollbar container ---
container = tk.Frame(root)
container.pack(fill="both", expand=True)

canvas = tk.Canvas(container, height=200)
canvas.pack(side="top", fill="both", expand=True)

h_scroll = tk.Scrollbar(container, orient="horizontal", command=canvas.xview)
h_scroll.pack(side="bottom", fill="x")

canvas.configure(xscrollcommand=h_scroll.set)

# --- Frame inside canvas ---
outer_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=outer_frame, anchor="nw")

for i in range(300):

    # cell wrapper with zero padding
    cell = tk.Frame(outer_frame, padx=0, pady=0)
    cell.grid(row=0, column=i, padx=1, pady=0)

    # --- plot ON TOP ---
    plot = tk.Canvas(
        cell,
        width=40,
        height=50,
        bg="white",
        highlightthickness=0
    )
    plot.pack(padx=0, pady=0)

    h = random.randint(5, 45)
    plot.create_rectangle(5, 50-h, 35, 50, fill="blue")

    # --- button BELOW (tightest possible) ---
    btn = tk.Button(
        cell,
        text=str(i),
        width=4,
        height=2,     # reduced height to remove bottom space
        padx=0,
        pady=0,
        borderwidth=1
    )
    btn.pack(padx=0, pady=0)

# --- Update scroll region ---
def update_scroll_region(event=None):
    canvas.configure(scrollregion=canvas.bbox("all"))

outer_frame.bind("<Configure>", update_scroll_region)

root.mainloop()
