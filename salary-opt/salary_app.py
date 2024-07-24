import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configure the page
st.set_page_config(page_title="Indian Income Tax Optimizer", page_icon="🇮🇳", layout="wide")

# Custom CSS to improve UI
st.markdown("""
    <style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .medium-font {
        font-size:20px !important;
    }
    .small-font {
        font-size:14px !important;
    }
    .result-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper functions
def calculate_tax(income):
    tax_slabs = [
        (0, 300000, 0),
        (300001, 600000, 0.05),
        (600001, 900000, 0.10),
        (900001, 1200000, 0.15),
        (1200001, 1500000, 0.20),
        (1500001, float('inf'), 0.30)
    ]
    tax = 0
    for lower, upper, rate in tax_slabs:
        if income > lower:
            taxable = min(income, upper) - lower
            tax += taxable * rate
    return tax

def optimize_salary(gross_salary):
    # Simplified optimization logic
    basic = min(gross_salary * 0.5, 180000)  # 50% of gross or 1.8L, whichever is lower
    hra = min(gross_salary * 0.4, 100000)    # 40% of gross or 1L, whichever is lower
    special = gross_salary - basic - hra
    
    section_80c = min(150000, gross_salary * 0.15)  # 15% of gross or 1.5L, whichever is lower
    section_80d = min(25000, gross_salary * 0.05)   # 5% of gross or 25K, whichever is lower
    
    taxable_income = gross_salary - hra - section_80c - section_80d
    tax_payable = calculate_tax(taxable_income)
    
    return {
        "Basic Salary": basic,
        "HRA": hra,
        "Special Allowance": special,
        "Section 80C": section_80c,
        "Section 80D": section_80d,
        "Taxable Income": taxable_income,
        "Tax Payable": tax_payable
    }

# Main app
def main():
    st.markdown("<p class='big-font'>Indian Income Tax Optimizer</p>", unsafe_allow_html=True)
    st.markdown("<p class='medium-font'>Optimize your salary structure to minimize taxes</p>", unsafe_allow_html=True)

    # Input section
    gross_salary = st.number_input("Enter your annual gross salary (₹)", min_value=0, value=500000, step=10000, format="%d")

    if st.button("Optimize My Salary"):
        if gross_salary > 0:
            results = optimize_salary(gross_salary)
            
            # Display results
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<p class='medium-font'>Salary Breakdown</p>", unsafe_allow_html=True)
                fig = px.pie(
                    values=[results["Basic Salary"], results["HRA"], results["Special Allowance"]],
                    names=["Basic Salary", "HRA", "Special Allowance"],
                    title="Optimized Salary Distribution"
                )
                st.plotly_chart(fig)

            with col2:
                st.markdown("<p class='medium-font'>Tax Savings</p>", unsafe_allow_html=True)
                original_tax = calculate_tax(gross_salary)
                tax_saved = original_tax - results["Tax Payable"]
                
                fig = go.Figure(go.Indicator(
                    mode = "number+delta",
                    value = results["Tax Payable"],
                    number = {'prefix': "₹"},
                    delta = {'position': "top", 'reference': original_tax, 'valueformat': '.0f'},
                    title = {"text": "Optimized Tax vs Original Tax"}
                ))
                st.plotly_chart(fig)

            # Detailed breakdown
            st.markdown("<div class='result-box'>", unsafe_allow_html=True)
            st.markdown("<p class='medium-font'>Detailed Breakdown</p>", unsafe_allow_html=True)
            for key, value in results.items():
                st.markdown(f"<p class='small-font'><b>{key}:</b> ₹{value:,.2f}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Tax saving tips
            st.markdown("<p class='medium-font'>Tax Saving Tips</p>", unsafe_allow_html=True)
            st.markdown("""
            - Maximize your 80C investments (up to ₹1.5 lakhs)
            - Consider health insurance for 80D deductions
            - If eligible, claim HRA benefits
            - Explore NPS investments for additional tax benefits
            """)

    # Information section
    with st.expander("Understanding Your Taxes"):
        st.markdown("""
        - **Basic Salary:** The core component of your salary.
        - **HRA (House Rent Allowance):** Allowance for rental expenses.
        - **Special Allowance:** Additional components of your salary.
        - **Section 80C:** Deductions for specified investments and expenses (up to ₹1.5 lakhs).
        - **Section 80D:** Deductions for health insurance premiums.
        
        ### Updates with the 2024 Tax Regime:
        - **Standard Deduction:** Increased to ₹75,000.
        - **Revised Tax Slabs:**
          - Up to ₹3,00,000: Nil
          - ₹3,00,001 to ₹6,00,000: 5%
          - ₹6,00,001 to ₹9,00,000: 10%
          - ₹9,00,001 to ₹12,00,000: 15%
          - ₹12,00,001 to ₹15,00,000: 20%
          - Above ₹15,00,000: 30%
        - **Leave Encashment Exemption:** Increased to ₹25 lakhs for non-government employees.
        - **Rebate under Section 87A:** Available for income up to ₹7 lakhs, making the tax liability zero.
        - **Reduced Surcharge:** Highest surcharge rate reduced to 25% for income above ₹5 crore.
        
        This tool provides a simplified calculation. For personalized advice, please consult a tax professional.
        """)

if __name__ == "__main__":
    main()
