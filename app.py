import streamlit as st
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

st.set_page_config(page_title="UHNW Simulator", layout="wide")
st.title("UHNW Portfolio Simulator: Institutional Quant Model")
st.write("Engine upgraded with Covariance Matrix (Correlated Returns), Student-t Distributions (Fat Tails), and Markov Regime Shifts.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("1. Client Profile")
initial_withdrawal = st.sidebar.slider("Initial Annual Spending ($)", 1000000, 10000000, 2000000, 500000)
legacy_target = st.sidebar.slider("Legacy Target ($)", 0, 50000000, 10000000, 1000000)
inflation_rate = st.sidebar.number_input("Annual Inflation (%)", value=2.5, step=0.1) / 100
tax_rate = st.sidebar.slider("Effective Tax Rate (%)", 0, 50, 35, 1) / 100
aum_fee = st.sidebar.slider("Bank Advisory Fee (AUM %)", 0.0, 2.0, 0.75, 0.05) / 100

st.sidebar.header("2. Asset Allocation (%)")
w_eq = st.sidebar.number_input("U.S. Equities", value=35) / 100
w_muni = st.sidebar.number_input("Municipal Bonds", value=20) / 100
w_pe = st.sidebar.number_input("Private Equity", value=20) / 100
w_pcredit = st.sidebar.number_input("Private Credit", value=15) / 100
w_hedge = st.sidebar.number_input("Hedge Funds", value=10) / 100

st.sidebar.header("3. Advanced Institutional Logic")
glide_path = st.sidebar.checkbox("Glide Path: Shift 1% Equity to Munis Annually")

# --- QUANTITATIVE ENGINE SETUP ---
# JPM 2026 Expected Returns (Bull Market State)
mu_bull = np.array([0.067, 0.040, 0.103, 0.076, 0.041])
# Bear Market State (Lower returns, higher stress)
mu_bear = np.array([-0.150, 0.050, -0.050, 0.020, -0.020])

# Standard Volatilities
vols = np.array([0.15, 0.05, 0.19, 0.07, 0.06])

# Correlation Matrix (Equities negatively correlated to Munis)
corr_matrix = np.array([
    [ 1.00, -0.30,  0.60,  0.40,  0.50],  # Equities
    [-0.30,  1.00, -0.10,  0.20, -0.10],  # Munis (Flight to safety)
    [ 0.60, -0.10,  1.00,  0.50,  0.40],  # PE
    [ 0.40,  0.20,  0.50,  1.00,  0.30],  # Private Credit
    [ 0.50, -0.10,  0.40,  0.30,  1.00]   # Hedge Funds
])

# Calculate Cholesky Decomposition
L = np.linalg.cholesky(corr_matrix)

starting_money = 50000000
simulations = 500
success_count = 0
terminal_values = []

fig, ax = plt.subplots(figsize=(10, 5))

for life in range(simulations):
    current_money = starting_money
    current_withdrawal = initial_withdrawal
    portfolio_history = [starting_money]
    
    # Regime Shift Initial State (0 = Bull, 1 = Bear)
    regime = 0 
    
    # Dynamic Weights
    curr_w_eq = w_eq
    curr_w_muni = w_muni
    
    for year in range(30):
        # 1. Markov Regime Shift (15% chance to switch states each year)
        if random.random() < 0.15:
            regime = 1 - regime 
        current_mu = mu_bear if regime == 1 else mu_bull
        
        # 2. Glide Path
        if glide_path:
            shift = min(curr_w_eq, 0.01)
            curr_w_eq -= shift
            curr_w_muni += shift
            
        weights = np.array([curr_w_eq, curr_w_muni, w_pe, w_pcredit, w_hedge])
        weights = weights / np.sum(weights) # Normalize

        # 3. Fat Tails & Correlated Returns
        # Generate independent Student-t shocks (Degrees of Freedom = 5)
        independent_shocks = np.random.standard_t(df=5, size=5)
        # Apply Cholesky matrix to correlate them
        correlated_shocks = L @ independent_shocks
        
        # Calculate final returns: Mean + (Volatility * Shock)
        asset_returns = current_mu + (vols * correlated_shocks)
        
        # 4. Tax Drag Logic (Tax everything except index 1: Munis)
        after_tax_returns = asset_returns.copy()
        after_tax_returns[0] *= (1 - tax_rate) # Eq
        after_tax_returns[2] *= (1 - tax_rate) # PE
        after_tax_returns[3] *= (1 - tax_rate) # PCredit
        after_tax_returns[4] *= (1 - tax_rate) # Hedge
        
        total_return = np.dot(weights, after_tax_returns)
        
        # 5. Apply Financial Math
        current_money = current_money * (1 + total_return)
        current_money -= current_withdrawal
        current_money *= (1 - aum_fee)
        current_withdrawal *= (1 + inflation_rate)
        
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
ax.axhline(y=legacy_target, color='red', linestyle='--', alpha=0.5, label="Legacy Target")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)
