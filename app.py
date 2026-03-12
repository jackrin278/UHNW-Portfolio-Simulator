import streamlit as st
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# --- 1. Website Design & Sidebar ---
st.set_page_config(page_title="UHNW Simulator", layout="wide")
st.title("UHNW Portfolio Simulator")
st.write("Stress-testing a $50M Endowment Model using J.P. Morgan 2026 Capital Market Assumptions.")

# Sidebar for controls
st.sidebar.header("1. Client Lifestyle")
initial_withdrawal = st.sidebar.slider("Initial Annual Spending ($)", 1000000, 10000000, 2000000, 500000)
inflation_rate = st.sidebar.number_input("Annual Inflation (%)", value=2.5, step=0.1) / 100

st.sidebar.header("2. Asset Allocation (%)")
weight_pub_eq = st.sidebar.number_input("U.S. Large Cap Equities", value=35)
weight_muni = st.sidebar.number_input("Municipal Bonds", value=20)
weight_pe = st.sidebar.number_input("Private Equity", value=20)
weight_pcredit = st.sidebar.number_input("Private Credit", value=15)
weight_hedge = st.sidebar.number_input("Hedge Funds", value=10)

# Normalize weights so the app doesn't crash if the user doesn't equal exactly 100%
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
        # J.P. Morgan 2026 LTCMA Projections
        ret_pub_eq = random.gauss(0.067, 0.15)     
        ret_muni = random.gauss(0.040, 0.05)       
        ret_pe = random.gauss(0.103, 0.19)         
        ret_pcredit = random.gauss(0.076, 0.07)    
        ret_hedge = random.gauss(0.041, 0.06)      
        
        total_return = (w_eq * ret_pub_eq) + (w_muni * ret_muni) + \
                       (w_pe * ret_pe) + (w_pcredit * ret_pcredit) + \
                       (w_hedge * ret_hedge)
        
        # Apply growth and subtract that year's inflation-adjusted withdrawal
        current_money = current_money + (current_money * total_return)
        current_money = current_money - current_withdrawal
        
        # INCREASE next year's lifestyle cost by inflation!
        current_withdrawal = current_withdrawal * (1 + inflation_rate)
        
        if current_money < 0:
            current_money = 0
            
        portfolio_history.append(current_money)
        if current_money <= 0:
            break 

    if current_money > 0:
        success_count += 1
    
    # Save the final ending balance of this specific life
    terminal_values.append(current_money)
        
    if life < 100:
        ax.plot(portfolio_history, color='purple', alpha=0.1)

# --- 3. Displaying the Results ---
success_rate = (success_count / simulations) * 100
sorted_terminals = sorted(terminal_values)
median_terminal = sorted_terminals[len(sorted_terminals)//2]

# Create massive metrics at the top of the screen
col1, col2 = st.columns(2)
col1.metric("Portfolio Success Rate", f"{success_rate:.1f}%")
col2.metric("Median Ending Balance", f"${median_terminal:,.0f}")

# Chart formatting
ax.set_title("30-Year Wealth Trajectory (Inflation Adjusted)")
ax.set_ylabel("Account Balance")
ax.set_xlabel("Years in Retirement")

# Fix the 1e7 issue!
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'${x*1e-6:,.0f}M'))

st.pyplot(fig)
