import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Page Configuration
st.set_page_config(
    page_title="O2O Client Insight Dashboard",
    page_icon="🥡",
    layout="wide"
)

# --- Data Generation ---
@st.cache_data
def generate_data():
    clients = [
        "Tasty Wok Express", "Burger Kingpin", "Sushi Zen", "Pizza Heaven", 
        "Taco Fiesta", "Curry House", "Noodle Bar 99", "Salad Greens", 
        "Wings & Things", "Breakfast Club", "Mama's Pasta", "BBQ Smokehouse",
        "Vegan Vibes", "Donut Delights", "Smoothie Station", "Grill Master",
        "Seafood Shack", "Kebab Corner", "Dim Sum Daily", "Falafel Factory"
    ]
    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    data = []
    
    for client in clients:
        base_gmv = np.random.uniform(15000, 80000)
        growth_trend = np.random.uniform(0.95, 1.2)
        cogs_rate = np.random.uniform(0.35, 0.45)
        comm_rate = 0.20
        agency_fee = 2500
        
        for i, month in enumerate(months):
            trend_factor = 1 + ((i / 11) * (growth_trend - 1))
            noise = np.random.uniform(0.9, 1.1)
            
            gmv = base_gmv * trend_factor * noise
            baseline_gmv = gmv * np.random.uniform(0.6, 0.8)
            ad_spend = gmv * np.random.uniform(0.08, 0.15)
            
            total_investment = ad_spend + agency_fee
            cogs = gmv * cogs_rate
            comm = gmv * comm_rate
            net_profit = gmv - cogs - comm - total_investment
            
            roi = (net_profit / total_investment) * 100 if total_investment > 0 else 0
            
            data.append({
                "Client_Name": client,
                "Month": month,
                "Month_Index": i, # For sorting
                "GMV": gmv,
                "Baseline_GMV": baseline_gmv,
                "Ad_Spend": ad_spend,
                "Agency_Fee": agency_fee,
                "COGS": cogs,
                "Platform_Comm": comm,
                "Total_Investment": total_investment,
                "Net_Profit": net_profit,
                "ROI": roi
            })
            
    return pd.DataFrame(data)

df = generate_data()

# --- Dashboard Structure ---

st.title("🥡 O2O Client Insight Dashboard")
st.markdown("Operational intelligence for food delivery optimization.")

tab1, tab2 = st.tabs(["Master Overview (Team View)", "Client Detail View"])

# --- TAB 1: Master Overview ---
with tab1:
    # 1. KPI Row
    total_gmv = df["GMV"].sum()
    total_profit = df["Net_Profit"].sum()
    total_invest = df["Total_Investment"].sum()
    weighted_roi = (total_profit / total_invest) * 100
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Managed GMV", f"${total_gmv:,.0f}")
    c2.metric("Total Net Profit", f"${total_profit:,.0f}")
    c3.metric("Agency Weighted ROI", f"{weighted_roi:.1f}%")
    
    st.divider()
    
    # 2. Client Health Matrix
    # Aggregate data by client
    client_agg = df.groupby("Client_Name").agg({
        "Total_Investment": "sum",
        "Net_Profit": "sum",
        "ROI": "mean", # Average monthly ROI
        "GMV": "sum"
    }).reset_index()
    
    # Recalculate overall ROI per client for accuracy
    client_agg["Overall_ROI"] = (client_agg["Net_Profit"] / client_agg["Total_Investment"]) * 100
    
    st.subheader("Client Health Matrix")
    fig_scatter = px.scatter(
        client_agg,
        x="Total_Investment",
        y="Overall_ROI",
        size="GMV",
        color="Net_Profit",
        hover_name="Client_Name",
        color_continuous_scale=["red", "yellow", "green"],
        labels={"Total_Investment": "Total Investment ($)", "Overall_ROI": "ROI (%)"},
        height=500
    )
    # Add quadrants or lines
    fig_scatter.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="Target ROI")
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # 3. Leaderboard
    st.subheader("Growth Leaderboard (Top 5)")
    # Calculate growth (Last Month vs First Month)
    growth_list = []
    for client in client_agg["Client_Name"].unique():
        client_df = df[df["Client_Name"] == client].sort_values("Month_Index")
        first_profit = client_df.iloc[0]["Net_Profit"]
        last_profit = client_df.iloc[-1]["Net_Profit"]
        # Handle division by zero or negative flip
        growth_abs = last_profit - first_profit
        growth_pct = (growth_abs / abs(first_profit)) * 100 if first_profit != 0 else 0
        growth_list.append({"Client_Name": client, "Profit_Growth_Pct": growth_pct, "Net_Profit_Total": client_df["Net_Profit"].sum()})
        
    growth_df = pd.DataFrame(growth_list).sort_values("Profit_Growth_Pct", ascending=False).head(5)
    
    st.dataframe(
        growth_df,
        column_config={
            "Profit_Growth_Pct": st.column_config.ProgressColumn(
                "Net Profit Growth (%)",
                format="%.1f%%",
                min_value=-50,
                max_value=100,
            ),
            "Net_Profit_Total": st.column_config.NumberColumn(
                "Total Profit ($)",
                format="$%d"
            )
        },
        hide_index=True,
        use_container_width=True
    )

# --- TAB 2: Client Detail View ---
with tab2:
    # 1. Sidebar Selector
    selected_client = st.sidebar.selectbox("Select Client", df["Client_Name"].unique())
    
    # Filter data
    c_data = df[df["Client_Name"] == selected_client].sort_values("Month_Index")
    c_totals = client_agg[client_agg["Client_Name"] == selected_client].iloc[0]
    last_month = c_data.iloc[-1]
    
    # 2. LTV Story Header
    st.markdown(f"## 📊 {selected_client} Performance Report")
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Investment (Last Month)", f"${last_month['Total_Investment']:,.0f}")
    k2.metric("Return GMV (Last Month)", f"${last_month['GMV']:,.0f}", delta=f"${last_month['GMV'] - last_month['Baseline_GMV']:,.0f} vs Baseline")
    k3.metric("Net Profit (Last Month)", f"${last_month['Net_Profit']:,.0f}")
    
    roi_mult = last_month['GMV'] / last_month['Total_Investment']
    st.info(f"💡 **LTV Insight:** For every **$1** invested this month, we generated **${roi_mult:.2f}** in sales.")
    
    # 3. Value Proof Chart (Area)
    st.subheader("Value Created by Operations")
    
    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(
        x=c_data["Month"], y=c_data["Baseline_GMV"],
        fill=None, mode='lines', line_color='gray', name='Baseline GMV'
    ))
    fig_area.add_trace(go.Scatter(
        x=c_data["Month"], y=c_data["GMV"],
        fill='tonexty', mode='lines', line_color='#10b981', name='Actual GMV (With Ops)'
    ))
    fig_area.update_layout(hovermode="x unified", title="Actual vs Baseline Sales")
    st.plotly_chart(fig_area, use_container_width=True)
    
    # 4. Cost Structure (Donut)
    st.subheader("Cost Structure Analysis")
    
    # Aggregate costs
    costs = {
        "COGS": c_data["COGS"].sum(),
        "Platform Comm": c_data["Platform_Comm"].sum(),
        "Ad Spend": c_data["Ad_Spend"].sum(),
        "Agency Fee": c_data["Agency_Fee"].sum(),
        "Net Profit": max(0, c_data["Net_Profit"].sum()) # Handle negative profit display
    }
    
    fig_donut = px.pie(
        values=list(costs.values()),
        names=list(costs.keys()),
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    fig_donut.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_donut, use_container_width=True)

    # Stub Download
    csv = c_data.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 Download Client Report",
        data=csv,
        file_name=f"{selected_client}_report.csv",
        mime="text/csv",
    )