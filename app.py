import streamlit as st
import random
import matplotlib.pyplot as plt

# --- 1. Website Design ---
st.title("UHNW Portfolio Simulator")
st.write("Stress-testing a $50M Endowment Model portfolio using Monte Carlo simulations.")

# --- 2. The Interactive Slider ---
# This line creates a slider on the website that the user can drag!
withdrawal_amount = st.slider("Annual Lifestyle Spending ($)", min_value=1000000, max_value=10000000, value=2000000, step=500000)

# --- 3. The Engine ---
starting_money = 50000000
simulations = 500  # Lowered slightly so the website loads super fast
success_count = 0

fig, ax = plt.subplots(figsize=(10, 5))

for life in range(simulations):
    current_money = starting_money
    portfolio_history = [starting_money]
    
    for year in range(30):
        # Using conservative targets for a realistic model
        ret_pub_eq = random.gauss(0.07, 0.15)     
        ret_muni = random.gauss(0.04, 0.05)       
        ret_pe = random.gauss(0.10, 0.18)         
        ret_pcredit = random.gauss(0.07, 0.06)    
        ret_hedge = random.gauss(0.05, 0.05)      
        
        total_return = (0.35 * ret_pub_eq) + (0.20 * ret_muni) + \
                       (0.20 * ret_pe) + (0.15 * ret_pcredit) + \
                       (0.10 * ret_hedge)
        
        current_money = current_money + (current_money * total_return)
        current_money = current_money - withdrawal_amount
        
        if current_money < 0:
            current_money = 0
            
        portfolio_history.append(current_money)
        if current_money <= 0:
            break 

    if current_money > 0:
        success_count += 1
        
    if life < 100:
        ax.plot(portfolio_history, color='purple', alpha=0.1)

# --- 4. Displaying the Results on the Website ---
success_rate = (success_count / simulations) * 100
st.subheader(f"Portfolio Success Rate: {success_rate:.1f}%")

ax.set_title("30-Year Wealth Trajectory")
ax.set_ylabel("Account Balance ($)")
ax.set_xlabel("Years in Retirement")

# This tells Streamlit to draw the chart on the webpage
st.pyplot(fig)
