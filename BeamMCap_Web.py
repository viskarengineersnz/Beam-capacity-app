import streamlit as st
import math
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

st.title("NZS 3101 Beam Moment Capacity Calculator")

# --- Input fields ---
b = st.number_input("Width b (mm)", value=300)
h = st.number_input("Overall depth h (mm)", value=450)
cover = st.number_input("Clear cover (mm)", value=40)
fc = st.number_input("Concrete strength f'c (MPa)", value=25)
fy = st.number_input("Reinforcement yield strength fy (MPa)", value=500)
Es = st.number_input("Steel modulus Es (MPa)", value=200000)
alpha1 = st.number_input("α₁ (stress block factor)", value=0.85)
beta1 = st.number_input("β₁ (stress block factor)", value=0.85)
nt = st.number_input("Number of tension bars", value=3, step=1)
dt = st.number_input("Tension bar diameter (mm)", value=16)
nc = st.number_input("Number of compression bars", value=3, step=1)
dc = st.number_input("Compression bar diameter (mm)", value=10)

phi = 0.85
eps_cu = 0.003

# --- Calculations ---
As_t = nt * math.pi * dt**2 / 4
As_c = nc * math.pi * dc**2 / 4
d = h - cover - dt/2
d_prime = cover + dc/2 if nc > 0 else 0
T = As_t * fy

def equilibrium(a):
    c = a / beta1
    eps_sc = eps_cu * (c - d_prime) / c if nc > 0 else 0
    fs_c = min(Es * eps_sc, fy) if nc > 0 else 0
    Cc = alpha1 * fc * b * a
    Cs = As_c * fs_c
    return Cc + Cs - T

# Bisection method
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

a = a_mid
c = a / beta1
eps_sc = eps_cu * (c - d_prime) / c if nc > 0 else 0
fs_c = min(Es * eps_sc, fy) if nc > 0 else 0
Cc = alpha1 * fc * b * a
Cs = As_c * fs_c
Mn = (Cc * (d - a/2) + Cs * (d - d_prime)) / 1e6
phiMn = phi * Mn

# --- Display results ---
st.subheader("Results")
st.write(f"Equivalent stress-block depth a = {a:.2f} mm")
st.write(f"Neutral axis depth c = {c:.2f} mm")
st.write(f"Compression steel stress = {fs_c:.2f} MPa")
st.write(f"Nominal moment Mn = {Mn:.2f} kN·m")
st.write(f"Design moment φMn = {phiMn:.2f} kN·m")

# --- PDF Export (optional) ---
if st.button("Save PDF Report"):
    filename = st.text_input("Enter PDF filename", "Beam_Report.pdf")
    if filename:
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        report_text = f"""
        NZS 3101 Beam Calculation Report

        Inputs:
        b = {b} mm, h = {h} mm, cover = {cover} mm
        f'c = {fc} MPa, fy = {fy} MPa, Es = {Es} MPa
        Tension bars: {nt} Ø{dt} mm
        Compression bars: {nc} Ø{dc} mm
        α₁ = {alpha1}, β₁ = {beta1}, φ = {phi}

        Results:
        a = {a:.2f} mm
        c = {c:.2f} mm
        Compression steel stress = {fs_c:.2f} MPa
        Mn = {Mn:.2f} kN·m
        φMn = {phiMn:.2f} kN·m
        """
        story = [Paragraph(p.strip(), styles["Normal"]) for p in report_text.split("\n") if p.strip()]
        doc.build(story)
        st.success(f"PDF report saved as {filename}")
