import streamlit as st
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# --- 1. Website Design & Sidebar ---
st.set_page_config(page_title="UHNW Simulator", layout="wide")
st.title("UHNW Portfolio Simulator: The Endowment Model")
st.write("Stress-testing a $50M portfolio using J.P. Morgan 2026 Capital Market Assumptions, Tax Drag, and Sequence of Returns Risk.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("1. Client Profile")
initial_withdrawal = st.sidebar.slider("Initial Annual Spending ($)", 1000000, 10000000, 2000000, 500000)
inflation_rate = st.sidebar.number_input("Annual Inflation (%)", value=2.5, step=0.1) / 100
tax_rate = st.sidebar.slider("Effective Tax Rate (%)", 0, 50, 35, 1) / 100

st.sidebar.header("2. Asset Allocation (%)")
weight_pub_eq = st.sidebar.number_input("U.S. Large Cap Equities", value=35)
weight_muni = st.sidebar.number_input("Municipal Bonds (Tax-Free)", value=20)
weight_pe = st.sidebar.number_input("Private Equity", value=20)
weight_pcredit = st.sidebar.number_input("Private Credit", value=15)
weight_hedge = st.sidebar.number_input("Hedge Funds", value=10)

st.sidebar.header("3. Stress Testing")
crash_year_1 = st.sidebar.checkbox("Simulate -25% Crash in Year 1")

# Normalize weights
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
        # JPM 2026 Projections
        ret_pub_eq = random.gauss(0.067, 0.15)     
        ret_muni = random.gauss(0.040, 0.05)       
        ret_pe = random.gauss(0.103, 0.19)         
        ret_pcredit = random.gauss(0.076, 0.07)    
        ret_hedge = random.gauss(0.041, 0.06)      
        
        # Calculate Taxable vs. Tax-Free Returns
        taxable_return = (w_eq * ret_pub_eq) + (w_pe * ret_pe) + (w_pcredit * ret_pcredit) + (w_hedge * ret_hedge)
        after_tax_return = taxable_return * (1 - tax_rate)
        
        # Add the Tax-Free Muni return back in
        total_return = after_tax_return + (w_muni * ret_muni)
        
        # Sequence Risk Black Swan Event Override
        if year == 0 and crash_year_1:
            total_return = -0.25
        
        # Apply math
        current_money = current_money + (current_money * total_return)
        current_money = current_money - current_withdrawal
        current_withdrawal = current_withdrawal * (1 + inflation_rate)
        
        if current_money < 0:
            current_money = 0
            
        portfolio_history.append(current_money)
        if current_money <= 0:
            break 

    if current_money > 0:
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

st.markdown("### Monte Carlo Simulation Results (30-Year Horizon)")

# Massive metrics display
col1, col2, col3, col4 = st.columns(4)
col1.metric("Success Rate", f"{success_rate:.1f}%")
col2.metric("Worst Case (10th %ile)", f"${p10_terminal*1e-6:,.1f}M")
col3.metric("Base Case (50th %ile)", f"${p50_terminal*1e-6:,.1f}M")
col4.metric("Best Case (90th %ile)", f"${p90_terminal*1e-6:,.1f}M")

# Chart formatting
ax.set_ylabel("Account Balance")
ax.set_xlabel("Years in Retirement")
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'${x*1e-6:,.0f}M'))
ax.grid(True, alpha=0.3) # Adds a professional grid background
st.pyplot(fig)

# Add an explanation box at the bottom
st.info("Model accounts for annual inflation adjustments and applies a tax drag to non-municipal assets. Returns are simulated using a Gaussian distribution based on standard standard-deviation brackets and expected return targets.")
