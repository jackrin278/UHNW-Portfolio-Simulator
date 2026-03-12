import streamlit as st
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# --- 1. Website Design & Sidebar ---
st.set_page_config(page_title="UHNW Simulator", layout="wide")
st.title("UHNW Portfolio Simulator: The Endowment Model")
st.write("Stress-testing a $50M portfolio using J.P. Morgan 2026 Assumptions, Tax Drag, Advisory Fees, and Dynamic De-Risking.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("1. Client Profile & Goals")
initial_withdrawal = st.sidebar.slider("Initial Annual Spending ($)", 1000000, 10000000, 2000000, 500000)
legacy_target = st.sidebar.slider("Legacy Goal (Minimum Inheritance)", 0, 50000000, 10000000, 1000000)
inflation_rate = st.sidebar.number_input("Annual Inflation (%)", value=2.5, step=0.1) / 100
tax_rate = st.sidebar.slider("Effective Tax Rate (%)", 0, 50, 35, 1) / 100

st.sidebar.header("2. Asset Allocation (%)")
weight_pub_eq = st.sidebar.number_input("U.S. Large Cap Equities", value=35)
weight_muni = st.sidebar.number_input("Municipal Bonds (Tax-Free)", value=20)
weight_pe = st.sidebar.number_input("Private Equity", value=20)
weight_pcredit = st.sidebar.number_input("Private Credit", value=15)
weight_hedge = st.sidebar.number_input("Hedge Funds", value=10)

st.sidebar.header("3. Advanced Advisory Strategy")
aum_fee = st.sidebar.slider("Bank Advisory Fee (AUM %)", 0.0, 2.0, 0.75, 0.05) / 100
crash_year_1 = st.sidebar.checkbox("Black Swan: -25% Crash in Year 1")
glide_path = st.sidebar.checkbox("Glide Path: Shift 1% Equity to Munis Annually")

# Normalize initial weights
total_weight = weight_pub_eq + weight_muni + weight_pe + weight_pcredit + weight_hedge
w_eq = weight_pub_eq / total_weight
w_muni = weight_muni / total_weight
w_pe = weight_pe / total_weight
w_pcredit = weight_pcredit / total_weight
w_hedge = weight_hedge / total_weight

# --- 2. The Engine ---
starting_money = 50000000
simulations = 500
success_count = 0
terminal_values = []

fig, ax = plt.subplots(figsize=(10, 5))

for life in range(simulations):
    current_money = starting_money
    current_withdrawal = initial_withdrawal
    portfolio_history = [starting_money]
    
    for year in range(30):
        # Dynamic Glide Path Logic
        current_w_eq = w_eq
        current_w_muni = w_muni
        if glide_path:
            shift = min(current_w_eq, year * 0.01) # Shift max 1% per year
            current_w_eq -= shift
            current_w_muni += shift

        # JPM 2026 Projections
        ret_pub_eq = random.gauss(0.067, 0.15)     
        ret_muni = random.gauss(0.040, 0.05)       
        ret_pe = random.gauss(0.103, 0.19)         
        ret_pcredit = random.gauss(0.076, 0.07)    
        ret_hedge = random.gauss(0.041, 0.06)      
        
        # Calculate Taxable vs. Tax-Free Returns
        taxable_return = (current_w_eq * ret_pub_eq) + (w_pe * ret_pe) + (w_pcredit * ret_pcredit) + (w_hedge * ret_hedge)
        after_tax_return = taxable_return * (1 - tax_rate)
        
        # Add the Tax-Free Muni return back in
        total_return = after_tax_return + (current_w_muni * ret_muni)
        
        # Sequence Risk Black Swan Event Override
        if year == 0 and crash_year_1:
            total_return = -0.25
        
        # Apply math: Market Growth -> Withdrawals -> AUM Fee
        current_money = current_money + (current_money * total_return)
        current_money = current_money - current_withdrawal
        current_money = current_money * (1 - aum_fee) # The bank takes its cut
        
        # Adjust next year's spending for inflation
        current_withdrawal = current_withdrawal * (1 + inflation_rate)
        
        if current_money < 0:
            current_money = 0
            
        portfolio_history.append(current_money)
        if current_money <= 0:
            break 

    # New Success Metric: Did they hit the legacy target?
    if current_money >= legacy_target:
        success_count += 1
        
    terminal_values.append(current_money)
        
    if life < 100:
        ax.plot(portfolio_history, color='purple', alpha=0.1)

# --- 3. Displaying the Results ---
success_rate = (success_count / simulations) * 100
sorted_terminals = sorted(terminal_values)

# Calculate Institutional Percentiles
p10_terminal = sorted_terminals[int(0.10 * len(sorted_terminals))] # Worst 10%
p50_terminal = sorted_terminals[int(0.50 * len(sorted_terminals))] # Median
p90_terminal = sorted_terminals[int(0.90 * len(sorted_terminals))] # Best 10%

st.markdown(f"### Likelihood of Securing ${legacy_target*1e-6:,.1f}M Legacy: **{success_rate:.1f}%**")

# Massive metrics display
col1, col2, col3 = st.columns(3)
col1.metric("Worst Case (10th %ile)", f"${p10_terminal*1e-6:,.1f}M")
col2.metric("Base Case (50th %ile)", f"${p50_terminal*1e-6:,.1f}M")
col3.metric("Best Case (90th %ile)", f"${p90_terminal*1e-6:,.1f}M")

# Chart formatting
ax.set_ylabel("Account Balance")
ax.set_xlabel("Years in Retirement")
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'${x*1e-6:,.0f}M'))
# Draw a horizontal line to show the legacy target on the chart!
ax.axhline(y=legacy_target, color='red', linestyle='--', alpha=0.5, label="Legacy Target")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

st.info("Success is defined as surviving 30 years AND leaving behind the minimum requested legacy amount, net of inflation, taxes, and advisory fees.")
