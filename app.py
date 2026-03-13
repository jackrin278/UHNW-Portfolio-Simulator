import streamlit as st
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

st.set_page_config(page_title="UHNW Simulator", layout="wide")
st.title("UHNW Portfolio Simulator: Institutional Quant Model")
st.write("Engine upgraded with Regime-Dependent Correlation Matrices and a Custom Deterministic Scenario Overlay.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("1. Client Profile")
initial_withdrawal = st.sidebar.slider("Initial Annual Spending ($)", 1000000, 10000000, 2000000, 500000)
legacy_target = st.sidebar.slider("Legacy Target ($)", 0, 50000000, 10000000, 1000000)
inflation_rate = st.sidebar.number_input("Base Annual Inflation (%)", value=2.5, step=0.1) / 100
tax_rate = st.sidebar.slider("Effective Tax Rate (%)", 0, 50, 35, 1) / 100
aum_fee = st.sidebar.slider("Bank Advisory Fee (AUM %)", 0.0, 2.0, 0.75, 0.05) / 100

st.sidebar.header("2. Asset Allocation (%)")
w_eq = st.sidebar.number_input("U.S. Equities", value=35) / 100
w_muni = st.sidebar.number_input("Municipal Bonds", value=20) / 100
w_pe = st.sidebar.number_input("Private Equity", value=20) / 100
w_pcredit = st.sidebar.number_input("Private Credit", value=15) / 100
w_hedge = st.sidebar.number_input("Hedge Funds", value=10) / 100

# --- NEW: CUSTOM SCENARIO OVERLAY ---
st.sidebar.header("3. Custom Stress Test (Red Line)")
show_custom = st.sidebar.checkbox("Plot Custom Scenario Overlay")
c_eq = st.sidebar.number_input("Custom Equity Return (%)", value=-2.0) / 100
c_muni = st.sidebar.number_input("Custom Muni Return (%)", value=1.0) / 100
c_pe = st.sidebar.number_input("Custom PE Return (%)", value=5.0) / 100
c_pcredit = st.sidebar.number_input("Custom Credit Return (%)", value=4.0) / 100
c_hedge = st.sidebar.number_input("Custom Hedge Return (%)", value=2.0) / 100

st.sidebar.header("4. Advanced Institutional Logic")
glide_path = st.sidebar.checkbox("Glide Path: Shift 1% Equity to Munis Annually")

# --- QUANTITATIVE ENGINE SETUP ---
mu_normal = np.array([0.067, 0.040, 0.103, 0.076, 0.041])
corr_normal = np.array([
    [ 1.00, -0.30,  0.60,  0.40,  0.50],  
    [-0.30,  1.00, -0.10,  0.20, -0.10],  
    [ 0.60, -0.10,  1.00,  0.50,  0.40],  
    [ 0.40,  0.20,  0.50,  1.00,  0.30],  
    [ 0.50, -0.10,  0.40,  0.30,  1.00]   
])
L_normal = np.linalg.cholesky(corr_normal)

mu_shock = np.array([-0.150, -0.050, -0.050, 0.020, -0.020])
corr_shock = np.array([
    [ 1.00,  0.40,  0.60,  0.40,  0.50],  
    [ 0.40,  1.00, -0.10,  0.20, -0.10],  
    [ 0.60, -0.10,  1.00,  0.50,  0.40],  
    [ 0.40,  0.20,  0.50,  1.00,  0.30],  
    [ 0.50, -0.10,  0.40,  0.30,  1.00]   
])
corr_shock = corr_shock + np.eye(5) * 0.0001
L_shock = np.linalg.cholesky(corr_shock)

vols = np.array([0.15, 0.05, 0.19, 0.07, 0.06])

starting_money = 50000000
simulations = 500
success_count = 0
terminal_values = []

fig, ax = plt.subplots(figsize=(10, 5))

# 1. Run the standard Monte Carlo simulation
for life in range(simulations):
    current_money = starting_money
    current_withdrawal = initial_withdrawal
    portfolio_history = [starting_money]
    
    regime = 0 
    curr_w_eq = w_eq
    curr_w_muni = w_muni
    
    for year in range(30):
        if random.random() < 0.15:
            regime = 1 - regime 
            
        current_mu = mu_shock if regime == 1 else mu_normal
        current_L = L_shock if regime == 1 else L_normal
        current_inflation = inflation_rate + 0.04 if regime == 1 else inflation_rate
        
        if glide_path:
            shift = min(curr_w_eq, 0.01)
            curr_w_eq -= shift
            curr_w_muni += shift
            
        weights = np.array([curr_w_eq, curr_w_muni, w_pe, w_pcredit, w_hedge])
        weights = weights / np.sum(weights)

        independent_shocks = np.random.standard_t(df=5, size=5)
        correlated_shocks = current_L @ independent_shocks
        asset_returns = current_mu + (vols * correlated_shocks)
        
        after_tax_returns = asset_returns.copy()
        after_tax_returns[0] *= (1 - tax_rate) 
        after_tax_returns[2] *= (1 - tax_rate) 
        after_tax_returns[3] *= (1 - tax_rate) 
        after_tax_returns[4] *= (1 - tax_rate) 
        
        total_return = np.dot(weights, after_tax_returns)
        
        current_money = current_money * (1 + total_return)
        current_money -= current_withdrawal
        current_money *= (1 - aum_fee)
        current_withdrawal *= (1 + current_inflation) 
        
        if current_money < 0:
            current_money = 0
            
        portfolio_history.append(current_money)
        if current_money <= 0:
            break 

    if current_money >= legacy_target:
        success_count += 1
    terminal_values.append(current_money)
        
    if life < 100:
        ax.plot(portfolio_history, color='purple', alpha=0.1)

# 2. OVERLAY THE CUSTOM DETERMINISTIC LINE
if show_custom:
    custom_history = [starting_money]
    c_money = starting_money
    c_withdrawal = initial_withdrawal
    
    # Calculate the exact blended return based on your custom inputs
    c_taxable_return = (w_eq * c_eq) + (w_pe * c_pe) + (w_pcredit * c_pcredit) + (w_hedge * c_hedge)
    c_after_tax = c_taxable_return * (1 - tax_rate)
    c_total_return = c_after_tax + (w_muni * c_muni)
    
    for year in range(30):
        c_money = c_money * (1 + c_total_return)
        c_money -= c_withdrawal
        c_money *= (1 - aum_fee)
        c_withdrawal *= (1 + inflation_rate)
        if c_money < 0:
            c_money = 0
        custom_history.append(c_money)
        
    ax.plot(custom_history, color='red', linewidth=3, label=f"Custom Fixed Return: {c_total_return*100:.2f}%")
    ax.legend()

# --- RESULTS & DISPLAY ---
success_rate = (success_count / simulations) * 100
sorted_terminals = np.sort(terminal_values)

p10_terminal = sorted_terminals[int(0.10 * len(sorted_terminals))]
p50_terminal = sorted_terminals[int(0.50 * len(sorted_terminals))]
p90_terminal = sorted_terminals[int(0.90 * len(sorted_terminals))]

st.markdown(f"### Likelihood of Securing ${legacy_target*1e-6:,.1f}M Legacy: **{success_rate:.1f}%**")

col1, col2, col3 = st.columns(3)
col1.metric("Worst Case (10th %ile)", f"${p10_terminal*1e-6:,.1f}M")
col2.metric("Base Case (50th %ile)", f"${p50_terminal*1e-6:,.1f}M")
col3.metric("Best Case (90th %ile)", f"${p90_terminal*1e-6:,.1f}M")

ax.set_ylabel("Account Balance")
ax.set_xlabel("Years in Retirement")
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'${x*1e-6:,.0f}M'))
ax.grid(True, alpha=0.3)
st.pyplot(fig)
