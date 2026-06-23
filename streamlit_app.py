import streamlit as st
import pandas as pd
import plotly.express as px
from pulp import *

st.set_page_config(page_title="Prescriptive Analytics Distribusi Barang", page_icon="📦", layout="wide")

st.markdown("""
<style>

.main {
    background-color: #0F172A;
}

.block-container {
    padding-top: 1rem;
}

h1, h2, h3 {
    color: white;
}

div[data-testid="metric-container"] {
    background: linear-gradient(135deg,#1e3a8a,#2563eb);
    border: 1px solid rgba(255,255,255,0.1);
    padding: 20px;
    border-radius: 18px;
    box-shadow: 0 8px 20px rgba(37,99,235,.25);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
# 📦 Prescriptive Analytics Dashboard

### Optimasi Distribusi Barang Menggunakan Linear Programming

Dashboard ini membantu menentukan distribusi barang optimal dari warehouse ke customer dengan biaya minimum menggunakan metode Transportation Problem dan PuLP.
""")

supply_df = pd.read_csv("supply.csv")
demand_df = pd.read_csv("demand.csv")
cost_df = pd.read_csv("cost_matrix.csv")

scenario = st.sidebar.selectbox(
    "Pilih Skenario",
    ["Demand Normal","Demand +10%","Demand +20%","Demand +30%"]
)

st.sidebar.markdown("---")

st.sidebar.info("""
📚 Mata Kuliah:
Analisis Data dan Informasi

🎓 Program Studi:
Teknik Informatika

📦 Tema:
Optimasi Distribusi Barang

⚙ Metode:
Linear Programming (PuLP)
""")

multiplier = 1.0
if scenario == "Demand +10%":
    multiplier = 1.10
elif scenario == "Demand +20%":
    multiplier = 1.20
elif scenario == "Demand +30%":
    multiplier = 1.30

demand_sim = demand_df.copy()
demand_sim["Demand"] = (demand_sim["Demand"] * multiplier).round().astype(int)

warehouses = supply_df["Warehouse"].tolist()
customers = demand_sim["Customer"].tolist()

supply = dict(zip(supply_df["Warehouse"], supply_df["Supply"]))
demand = dict(zip(demand_sim["Customer"], demand_sim["Demand"]))

cost = {}
for _, row in cost_df.iterrows():
    cost[(row["Warehouse"], row["Customer"])] = row["Cost"]

total_supply = supply_df["Supply"].sum()
total_demand = demand_sim["Demand"].sum()

feasible = total_supply >= total_demand

optimal_cost = None
result_df = pd.DataFrame()

if feasible:
    model = LpProblem("Transportation", LpMinimize)

    x = LpVariable.dicts("Ship", (warehouses, customers), lowBound=0)

    model += lpSum(cost[(i,j)] * x[i][j] for i in warehouses for j in customers)

    for i in warehouses:
        model += lpSum(x[i][j] for j in customers) <= supply[i]

    for j in customers:
        model += lpSum(x[i][j] for i in warehouses) == demand[j]

    with st.spinner(
        "🔄 Menjalankan optimasi distribusi..."
    ):
        model.solve()

    optimal_cost = value(model.objective)

    st.info(
    f"📦 Sistem berhasil menghasilkan rekomendasi distribusi "
    f"optimal dengan total biaya minimum sebesar "
    f"{optimal_cost:,.2f}."
    )

    results = []
    for i in warehouses:
        for j in customers:
            qty = value(x[i][j])
            if qty and qty > 0:
                results.append([i,j,qty])

    result_df = pd.DataFrame(results, columns=["Warehouse","Customer","Quantity"])

solver_status = (
    LpStatus[model.status]
    if feasible
    else "Not Feasible"
)

st.metric(
    "⚙ Solver Status",
    solver_status
)

ratio = (
    total_supply / total_demand
    if total_demand > 0
    else 0
)

if feasible and len(result_df) > 0:
    
    best_route = result_df.loc[
        result_df["Quantity"].idxmax()
    ]

    st.success(
        f"Rekomendasi utama: "
        f"{best_route['Warehouse']} → "
        f"{best_route['Customer']} "
        f"dengan volume distribusi "
        f"{best_route['Quantity']:.0f} unit."
    )

st.header("📊 Key Performance Indicators")

col1, col2, col3, col4, col5 = st.columns(5)


col1.metric(
    "📦 Total Supply",
    f"{total_supply:,.0f}"
)

col2.metric(
    "🏪 Total Demand",
    f"{total_demand:,.0f}"
)

if feasible:
    col3.metric(
        "💰 Minimum Cost",
        f"{optimal_cost:,.2f}"
    )
else:
    col3.metric(
        "💰 Minimum Cost",
        "N/A"
    )

if feasible:
    col4.metric(
        "⚙ Solver",
        LpStatus[model.status]
    )

if feasible:
    st.success(
        "✅ Model feasible dan berhasil dioptimasi."
    )
else:
    st.error(
        "❌ Total demand melebihi total supply."
    )

col5.metric(
    "📈 Supply/Demand",
    f"{ratio:.2f}"
)

st.subheader("📈 Feasibility Ratio")

progress = min(
    ratio,
    1.0
)

st.progress(progress)

st.caption(
    f"Supply memenuhi {progress*100:.1f}% dari demand."
)

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "🏭 Supply & Demand",
    "🚚 Hasil Optimasi",
    "📈 Analisis"
])

with tab1:

    st.subheader("Ringkasan Sistem")

    if feasible:
        st.success(
            "Model berhasil menemukan solusi optimal."
        )

    st.markdown(f"""
### Skenario Aktif

**{scenario}**

Total Supply : **{total_supply:,.0f}**

Total Demand : **{total_demand:,.0f}**
""")

    if feasible and len(result_df) > 0:

        best_route = result_df.loc[
            result_df["Quantity"].idxmax()
        ]

        st.info(
            f"Rute distribusi terbesar adalah "
            f"{best_route['Warehouse']} → "
            f"{best_route['Customer']} "
            f"dengan jumlah {best_route['Quantity']:.0f} unit."
        )

with tab2:

    fig_supply = px.bar(
        supply_df,
        x="Warehouse",
        y="Supply",
        title="Supply per Warehouse",
        text="Supply"
    )

    st.plotly_chart(
        fig_supply,
        use_container_width=True
    )

    fig_demand = px.bar(
        demand_sim,
        x="Customer",
        y="Demand",
        title="Demand per Customer",
        text="Demand"
    )

    st.plotly_chart(
        fig_demand,
        use_container_width=True
    )

    fig_cost = px.histogram(
        cost_df,
        x="Cost",
        title="Distribusi Biaya Distribusi"
    )

    st.plotly_chart(
        fig_cost,
        use_container_width=True
    )

with tab3:

    st.subheader(
        "🚚 Distribusi Optimal"
    )

    if feasible:

        fig_result = px.bar(
            result_df,
            x="Warehouse",
            y="Quantity",
            color="Customer",
            title="Distribusi Warehouse ke Customer"
        )

        st.plotly_chart(
            fig_result,
            use_container_width=True
        )

        st.dataframe(
            result_df,
            use_container_width=True
        )

        st.download_button(
            "📥 Download Hasil Optimasi",
            result_df.to_csv(index=False),
            "hasil_optimasi.csv",
            "text/csv"
        )

with tab4:

    st.subheader(
        "📈 Analisis Prescriptive Analytics"
    )

    if feasible:

        st.success(
            f"Biaya distribusi minimum = {optimal_cost:,.2f}"
        )

        st.markdown(f"""
### Interpretasi Hasil

Model berhasil menemukan solusi optimal dengan biaya distribusi minimum sebesar **{optimal_cost:,.2f}**.

Rekomendasi distribusi ini membantu perusahaan menentukan alokasi pengiriman barang dari warehouse ke customer dengan biaya paling efisien berdasarkan kapasitas supply dan kebutuhan demand.

Dengan pendekatan Linear Programming, perusahaan dapat meminimalkan biaya distribusi sekaligus memenuhi seluruh permintaan customer sesuai kapasitas warehouse yang tersedia.


### Skenario

**{scenario}**

### Input

- Warehouse : {len(warehouses)}
- Customer : {len(customers)}
- Supply : {total_supply:,.0f}
- Demand : {total_demand:,.0f}

### Output

- Distribusi Optimal
- Total Biaya Minimum

### Metode

Transportation Problem menggunakan Linear Programming (PuLP).
""")


st.caption("""
Proyek Mata Kuliah Analisis Data dan Informasi

Tema: Sistem Prescriptive Analytics untuk Optimasi Distribusi Barang

Metode: Linear Programming (PuLP)
""")