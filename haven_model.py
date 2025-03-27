import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📘 Haven Online School – Two-Year Financial Scenario Planner")

# ----------- USER INPUTS -----------
st.header("🔢 Core Settings")
students_y1 = st.slider("Year 1: Number of students", 1, 50, 10)
students_y2 = st.slider("Year 2: Number of students", 1, 100, 20)
offer_type = st.radio("Offer Type", ["Core Only", "Full Offer"])
price_per_block = 2000 if offer_type == "Core Only" else 2500
registration_fee = st.number_input("Registration Fee (£)", value=250)

st.header("💼 Staff Salaries")
teacher_salary = st.number_input("Full-Time Teacher (£)", value=37000)
senco_salary = st.number_input("SENCO (£)", value=40000)
mentor_salary = st.number_input("Mentor (£)", value=25000)
community_salary = st.number_input("Community Manager (£)", value=25000)

st.header("🖥️ Platform Costs")
platform_mode = st.radio("Platform Phase", ["Start-Up", "Scaling"])
platform_base_cost = 25 if platform_mode == "Start-Up" else 60

# ----------- GCSE CONFIG -----------
st.header("🎓 GCSE Course Planning")
gcse_to_create_y1 = st.slider("GCSE Courses to Create (Year 1)", 0, 5, 2)
gcse_selected_y2 = st.slider("Avg GCSEs per Student (Year 2)", 0, 5, 3)

gcse_setup_cost_y1 = gcse_to_create_y1 * 5000
gcse_maintenance_cost_y2 = gcse_to_create_y1 * 1000
gcse_revenue_y2 = students_y2 * gcse_selected_y2 * 1000

# ----------- OTHER COSTS -----------
st.header("📋 Additional Costs")
consulting_retainer = 1500
july_days = 2
august_days = 4
consulting_day_rate = 750
july_august_fee = (july_days + august_days) * consulting_day_rate

initial_funding = st.number_input("Initial Funding (£)", value=50000)

# ----------- FIXED STRUCTURE -----------
blocks_per_year = 6
weeks_per_block = 5
sessions_per_week = 4
session_duration_hours = 0.5
async_hours_per_week = 2

months = ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
block_months = ['Sep', 'Nov', 'Jan', 'Mar', 'May', 'Jun']

# ----------- FUNCTIONS -----------
def build_year(year_label, students, include_gcse=False):
    monthly_salary = (teacher_salary + senco_salary + mentor_salary + community_salary) / 12
    live_hours = students * 1 * session_duration_hours * sessions_per_week * weeks_per_block
    live_cost = live_hours * 0.08
    async_hours = students * async_hours_per_week * weeks_per_block
    async_cost = async_hours * 0.04

    revenue, expenses, net_cash, cumulative = [], [], [], []
    cash = 0

    for i, month in enumerate(months):
        rev = 0
        if month in block_months:
            rev += price_per_block * students
            if month == 'Sep' and year_label == "Year 1":
                rev += registration_fee * students
        if include_gcse and month == 'Sep':
            rev += gcse_revenue_y2

        # Expenses
        platform_admin_cost = platform_base_cost
        if month in block_months:
            platform_usage = live_cost + async_cost
        else:
            platform_usage = 0

        expense = monthly_salary + platform_usage + platform_admin_cost
        if month == 'Sep' and year_label == "Year 1":
            expense += gcse_setup_cost_y1
        if month == 'Sep' and year_label == "Year 2":
            expense += gcse_maintenance_cost_y2

        # Add consulting fees
        expense += consulting_retainer
        if month == 'Jun' and year_label == "Year 1":
            expense += july_august_fee

        # Marketing budget
        marketing_cost = rev * 0.08
        expense += marketing_cost

        net = rev - expense
        cash += net

        revenue.append(rev)
        expenses.append(expense)
        net_cash.append(net)
        cumulative.append(cash)

    df = pd.DataFrame({
        "Month": [f"{year_label} - {m}" for m in months],
        "Revenue (£)": revenue,
        "Expenses (£)": expenses,
        "Net Cash (£)": net_cash,
        "Cumulative Cash (£)": cumulative
    })
    return df

# ----------- BUILD BOTH YEARS -----------
df_y1 = build_year("Year 1", students_y1, include_gcse=False)
df_y2 = build_year("Year 2", students_y2, include_gcse=True)
df_total = pd.concat([df_y1, df_y2], ignore_index=True)

# Add initial funding to cumulative
df_total.loc[0, "Cumulative Cash (£)"] += initial_funding
for i in range(1, len(df_total)):
    df_total.loc[i, "Cumulative Cash (£)"] = df_total.loc[i - 1, "Cumulative Cash (£)"] + df_total.loc[i, "Net Cash (£)"]

# ----------- DISPLAY -----------
st.subheader("📊 Two-Year Monthly Cash Flow")
st.dataframe(df_total.style.format({
    "Revenue (£)": "£{:.2f}",
    "Expenses (£)": "£{:.2f}",
    "Net Cash (£)": "£{:.2f}",
    "Cumulative Cash (£)": "£{:.2f}"
}))

st.line_chart(df_total.set_index("Month")["Cumulative Cash (£)"])

# ----------- BREAK-EVEN ALERT -----------
break_even = (df_total["Cumulative Cash (£)"].min() < 0)
if break_even:
    st.error("⚠️ Alert: You break even (go below £0) at some point. Consider reducing costs or increasing income.")
else:
    st.success("✅ You remain above break-even throughout the forecast.")

# ----------- DOWNLOAD -----------
st.subheader("📥 Download Your Forecast")

# Append summary parameters to CSV
summary = pd.DataFrame({
    "Parameter": [
        "Students Year 1", "Students Year 2", "Offer Type", "Price per Block", "Registration Fee",
        "Teacher Salary", "SENCO Salary", "Mentor Salary", "Community Manager Salary",
        "Platform Mode", "Platform Cost", "GCSEs to Create", "Avg GCSEs per Student Year 2",
        "GCSE Setup Cost Y1", "GCSE Maintenance Y2", "Initial Funding"
    ],
    "Value": [
        students_y1, students_y2, offer_type, price_per_block, registration_fee,
        teacher_salary, senco_salary, mentor_salary, community_salary,
        platform_mode, platform_base_cost, gcse_to_create_y1, gcse_selected_y2,
        gcse_setup_cost_y1, gcse_maintenance_cost_y2, initial_funding
    ]
})

combined_csv = pd.concat([summary, pd.DataFrame([[]]), df_total], ignore_index=False)

csv = combined_csv.to_csv(index=False).encode('utf-8')
st.download_button("Download as CSV", data=csv, file_name='haven_financial_model.csv', mime='text/csv')

st.caption("Model includes salaries, platform costs, consulting, GCSE setup/maintenance, and marketing. Based on your assumptions above.")
