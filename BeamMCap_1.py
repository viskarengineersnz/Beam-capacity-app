import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ---------------------------------------------------------
# NZS 3101 Beam Capacity Calculator with PDF Report Output
# ---------------------------------------------------------

def calculate_capacity():
    try:
        # --- Input values ---
        b = float(entry_b.get())
        h = float(entry_h.get())
        cover = float(entry_cover.get())
        fc = float(entry_fc.get())
        fy = float(entry_fy.get())
        Es = float(entry_Es.get())
        alpha1 = float(entry_alpha1.get())
        beta1 = float(entry_beta1.get())
        nt = int(entry_nt.get())
        dt = float(entry_dt.get())
        nc = int(entry_nc.get())
        dc = float(entry_dc.get())
        phi = 0.85
        eps_cu = 0.003

        # --- Derived values ---
        As_t = nt * math.pi * dt**2 / 4
        As_c = nc * math.pi * dc**2 / 4
        d = h - cover - dt/2
        d_prime = cover + dc/2 if nc > 0 else 0
        T = As_t * fy  # tension force (steel yields)

        def equilibrium(a):
            c = a / beta1
            eps_sc = eps_cu * (c - d_prime) / c if nc > 0 else 0
            fs_c = min(Es * eps_sc, fy) if nc > 0 else 0
            Cc = alpha1 * fc * b * a
            Cs = As_c * fs_c
            return Cc + Cs - T

        # --- Solve for a by bisection ---
        a_low, a_high = 1.0, h
        for _ in range(60):
            a_mid = 0.5 * (a_low + a_high)
            F_low = equilibrium(a_low)
            F_mid = equilibrium(a_mid)
            if F_low * F_mid < 0:
                a_high = a_mid
            else:
                a_low = a_mid
            if abs(F_mid) < 1e-2:
                break

        # --- Final results ---
        a = a_mid
        c = a / beta1
        eps_sc = eps_cu * (c - d_prime) / c if nc > 0 else 0
        fs_c = min(Es * eps_sc, fy) if nc > 0 else 0
        Cc = alpha1 * fc * b * a
        Cs = As_c * fs_c
        Mn = (Cc * (d - a / 2) + Cs * (d - d_prime)) / 1e6
        phiMn = phi * Mn

        result_text.set(
            f"Equivalent stress-block depth a = {a:.2f} mm\n"
            f"Neutral axis depth c = {c:.2f} mm\n"
            f"Compression steel stress = {fs_c:.2f} MPa\n"
            f"Nominal moment Mn = {Mn:.2f} kN·m\n"
            f"Design moment φMn = {phiMn:.2f} kN·m"
        )

        # Prepare a detailed text report with NZS references
        report = f"""
        NZS 3101 BEAM FLEXURAL CAPACITY CALCULATION REPORT
        --------------------------------------------------
        INPUT DATA
        Width (b) = {b:.1f} mm
        Depth (h) = {h:.1f} mm
        Cover = {cover:.1f} mm
        f'c = {fc:.1f} MPa, fy = {fy:.1f} MPa, Es = {Es:.0f} MPa
        Tension bars: {nt} Ø{dt} mm
        Compression bars: {nc} Ø{dc} mm
        α₁ = {alpha1:.2f}, β₁ = {beta1:.2f}, ϕ = {phi:.2f}

        REFERENCES
        • NZS 3101: Part 1 Clause 9.4.1.3 — α₁, β₁ values
        • NZS 3101: Part 1 Clause 9.4.1.2 — rectangular-stress-block
        • NZS 3101: Part 1 Clause 9.3.1 — ϕ factors for flexure
        • NZS 3101: Part 1 Clause 9.5.1 — steel strain ε_y = f_y / E_s = {fy/Es:.5f}

        CALCULATIONS
        1. Effective depths:
           d = h − cover − Øt/2 = {d:.1f} mm
           d′ = cover + Øc/2 = {d_prime:.1f} mm
        2. Reinforcement areas:
           As,t = {As_t:.2f} mm²
           As,c = {As_c:.2f} mm²
        3. Equilibrium of forces:
           T = As,t·f_y = {T/1000:.2f} kN
           Solving Cc + Cs = T by bisection → a = {a:.2f} mm
           ⇒ Neutral axis c = a/β₁ = {c:.2f} mm
        4. Compression steel strain ε_sc = {eps_sc:.6f} → f_sc = {fs_c:.2f} MPa
        5. Forces:
           Cc = α₁ f′c b a = {Cc/1000:.2f} kN
           Cs = As,c f_sc = {Cs/1000:.2f} kN
        6. Moment capacity:
           M_n = Cc (d − a/2) + Cs (d − d′)
               = {Mn:.2f} kN·m
           Design strength (ϕ = 0.85):
           ϕ M_n = {phiMn:.2f} kN·m

        CONCLUSION
        Design moment capacity = {phiMn:.2f} kN·m
        (Use in comparison with factored design moment M_u)
        """

        # Save the report string globally for PDF export
        global last_report
        last_report = report

    except Exception as e:
        result_text.set("Error: " + str(e))
        last_report = None


def export_pdf():
    if not last_report:
        messagebox.showerror("Error", "Please calculate first.")
        return
    filename = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Save PDF report as..."
    )
    if not filename:
        return

    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(p.strip(), styles["Normal"]) for p in last_report.split("\n") if p.strip()]
    doc.build(story)
    messagebox.showinfo("Saved", f"Report saved to:\n{filename}")

# --- GUI Setup ---
root = tk.Tk()
root.title("NZS 3101 Beam Capacity Calculator & PDF Report")

fields = [
    ("Width b (mm)", "300"),
    ("Depth h (mm)", "450"),
    ("Cover (mm)", "40"),
    ("f'c (MPa)", "25"),
    ("fy (MPa)", "500"),
    ("Es (MPa)", "200000"),
    ("α₁", "0.85"),
    ("β₁", "0.85"),
    ("# tension bars", "3"),
    ("Tension bar Ø (mm)", "16"),
    ("# compression bars", "3"),
    ("Compression bar Ø (mm)", "10")
]

entries = []
for label, default in fields:
    ttk.Label(root, text=label).pack()
    e = ttk.Entry(root)
    e.insert(0, default)
    e.pack()
    entries.append(e)

(entry_b, entry_h, entry_cover, entry_fc, entry_fy, entry_Es,
 entry_alpha1, entry_beta1, entry_nt, entry_dt, entry_nc, entry_dc) = entries

ttk.Button(root, text="Calculate", command=calculate_capacity).pack(pady=5)
result_text = tk.StringVar()
ttk.Label(root, textvariable=result_text, justify="left").pack(pady=5)
ttk.Button(root, text="Save Report as PDF", command=export_pdf).pack(pady=5)

last_report = None
root.mainloop()
