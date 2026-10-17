import plotly.express as px
import streamlit as st

from engineering import simulate_motion, summarize

st.set_page_config(page_title="Motion Lab | Engineering Demo", page_icon="⚙️", layout="wide")
st.title("Motion Lab")
st.caption("A small engineering sandbox for exploring constant-force motion.")
st.info("SIMULATED EXAMPLE · Deterministic local calculation; no sensor or vehicle data is used.", icon="ℹ️")

with st.sidebar:
    st.header("Simulation inputs")
    mass_kg = st.number_input("Mass (kg)", min_value=0.1, max_value=5000.0, value=1200.0, step=50.0)
    force_n = st.number_input("Applied force (N)", min_value=0.0, max_value=50000.0, value=2400.0, step=100.0)
    duration_s = st.number_input("Duration (s)", min_value=0.1, max_value=60.0, value=12.0, step=0.5)

try:
    result = simulate_motion(mass_kg, force_n, duration_s)
    metrics = summarize(mass_kg, force_n, result)
except (ValueError, ZeroDivisionError) as exc:
    st.error(f"Check the simulation inputs: {exc}")
else:
    first, second, third = st.columns(3)
    first.metric("Acceleration", f"{metrics['acceleration_m_s2']:.2f} m/s²")
    second.metric("Final velocity", f"{metrics['final_velocity_m_s']:.1f} m/s")
    third.metric("Distance traveled", f"{metrics['distance_m']:.1f} m")

    st.subheader("Motion over time")
    chart = px.line(
        result,
        x="time_s",
        y=["velocity_m_s", "distance_m"],
        labels={"time_s": "Time (s)", "value": "Value", "variable": "Measure"},
        color_discrete_sequence=["#176B87", "#E07A42"],
    )
    chart.update_layout(legend_title_text="", margin=dict(l=10, r=10, t=20, b=10), hovermode="x unified")
    st.plotly_chart(chart, use_container_width=True)
    st.caption("Model assumptions: starts from rest, constant force, no drag or grade. Distance is numerically integrated.")
