from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
옵พอร์ต (ถ้าใช้ st.cache_data)
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(
    page_title="KPI Zone D Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# 1. เชื่อมต่อ Google Sheets
# ---------------------------------------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/1vgrTK7RhodK4KiBU63j2IJAfi-FgUg51nFamPdk8ktc/edit?gid=0#gid=0"


@st.cache_resource
def init_connection():
  # รองรับการดึงค่าจาก Streamlit Secrets
  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  if "gcp_service_account" in st.secrets:
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
  else:
    # สำหรับการทดสอบ Local (ถ้ามีไฟล์ service_account.json)
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "service_account.json", scope
    )
  client = gspread.authorize(creds)
  return client


try:
  client = init_connection()
  sheet = client.open_by_url(SHEET_URL).sheet1
except Exception as e:
  st.error(
      f"ไม่สามารถเชื่อมต่อ Google Sheets ได้: {e} กรุณาตรวจสอบการตั้งค่า Secrets"
  )


@st.cache_data(ttl=60)
def load_data():
  data = sheet.get_all_records()
  df = pd.DataFrame(data)
  return df


df = load_data()

# ---------------------------------------------------------
# 2. ส่วนหัวของ Dashboard
# ---------------------------------------------------------
st.title("📊 แดชบอร์ดติดตามตัวชี้วัด KPI Zone D")
st.markdown(
    "วิเคราะห์ข้อมูลประสิทธิภาพรายสาขา ปี, เดือน และตัวชี้วัดต่างๆ พร้อมทั้งสามารถเพิ่มข้อมูลใหม่ได้ทันที"
)

# ตรวจสอบโครงสร้างข้อมูลเบื้องต้น
if df.empty:
  st.warning("ยังไม่มีข้อมูลใน Google Sheets กรุณาเพิ่มข้อมูลใหม่")
  st.stop()

# ---------------------------------------------------------
# 3. Sidebar: ฟังก์ชันตัวกรอง (Global Filters)
# ---------------------------------------------------------
st.sidebar.header("🔍 ตัวกรองข้อมูล (Filters)")

# เลือกปี
years = (
    sorted(df["ปี"].unique().tolist()) if "ปี" in df.columns else []
)
selected_years = st.sidebar.multiselect(
    "เลือกปี", options=years, default=years
)

# เลือกสาขา
branches = (
    sorted(df["สาขา"].unique().tolist()) if "สาขา" in df.columns else []
)
selected_branches = st.sidebar.multiselect(
    "เลือกสาขา", options=branches, default=branches
)

# เลือกเดือน
months = (
    sorted(df["เดือน"].unique().tolist()) if "เดือน" in df.columns else []
)
selected_months = st.sidebar.multiselect(
    "เลือกเดือน", options=months, default=months
)

# กรองข้อมูลตามเงื่อนไขที่เลือก
filtered_df = df.copy()
if selected_years:
  filtered_df = filtered_df[filtered_df["ปี"].isin(selected_years)]
if selected_branches:
  filtered_df = filtered_df[filtered_df["สาขา"].isin(selected_branches)]
if selected_months:
  filtered_df = filtered_df[filtered_df["เดือน"].isin(selected_months)]

# ---------------------------------------------------------
# 4. ภาพรวม (Key Metrics Cards)
# ---------------------------------------------------------
st.subheader("📌 สรุปภาพรวมตัวชี้วัด (KPI Overview)")

# แปลงคอลัมน์ตัวเลขให้เป็น float เพื่อคำนวณ
numeric_cols = [
    "Chicklist",
    "ความสำเร็จบิล Prepaid",
    "มาตรฐานจัดส่ง",
    "ความสำเร็จของPDO",
    "สรุปผลคะแนน",
]
for col in numeric_cols:
  if col in filtered_df.columns:
    filtered_df[col] = pd.to_numeric(filtered_df[col], errors="coerce").fillna(
        0
    )

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
  avg_checklist = (
      filtered_df["Chicklist"].mean() if "Chicklist" in filtered_df else 0
  )
  st.metric(
      label="Checklist เฉลี่ย",
      value=f"{avg_checklist:.2f}%",
      delta=f"{avg_checklist - df['Chicklist'].astype(float).mean():.2f}% จากภาพรวม",
  )

with col2:
  avg_prepaid = (
      filtered_df["ความสำเร็จบิล Prepaid"].mean()
      if "ความสำเร็จบิล Prepaid" in filtered_df
      else 0
  )
  st.metric(
      label="ความสำเร็จบิล Prepaid", value=f"{avg_prepaid:.2f}%"
  )

with col3:
  avg_delivery = (
      filtered_df["มาตรฐานจัดส่ง"].mean()
      if "มาตรฐานจัดส่ง" in filtered_df
      else 0
  )
  st.metric(label="มาตรฐานจัดส่ง", value=f"{avg_delivery:.2f}%")

with col4:
  avg_pdo = (
      filtered_df["ความสำเร็จของPDO"].mean()
      if "ความสำเร็จของPDO" in filtered_df
      else 0
  )
  st.metric(label="ความสำเร็จของ PDO", value=f"{avg_pdo:.2f}%")

with col5:
  avg_score = (
      filtered_df["สรุปผลคะแนน"].mean()
      if "สรุปผลคะแนน" in filtered_df
      else 0
  )
  st.metric(label="สรุปผลคะแนนรวม", value=f"{avg_score:.2f}")

st.markdown("---")

# ---------------------------------------------------------
# 5. การแสดงผลกราฟแบบหลายมิติ (Multi-dimensional Charts)
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(
    ["📈 แนวโน้มตามเวลา (Trend)", "🏢 เปรียบเทียบรายสาขา", "📋 ตารางข้อมูลดิบ"]
)

with tab1:
  st.subheader("แนวโน้มคะแนนเฉลี่ยรายเดือน")
  if not filtered_df.empty and "เดือน" in filtered_df.columns:
    # จัดกลุ่มตามเดือนและคำนวณค่าเฉลี่ย
    trend_df = (
        filtered_df.groupby("เดือน")[numeric_cols].mean().reset_index()
    )
    fig_trend = px.line(
        trend_df,
        x="เดือน",
        y=numeric_cols,
        markers=True,
        title="เปรียบเทียบพัฒนาการ KPI ในแต่ละเดือน",
        labels={"value": "คะแนน (%)", "variable": "ตัวชี้วัด"},
    )
    fig_trend.update_layout(
        hovermode="x unified", legend_title="ตัวชี้วัด KPI"
    )
    st.plotly_chart(fig_trend, use_container_width=True)
  else:
    st.info("ไม่มีข้อมูลเพียงพอสำหรับแสดงกราฟแนวโน้ม")

with tab2:
  st.subheader("เปรียบเทียบผลงานแยกตามสาขา")
  if not filtered_df.empty and "สาขา" in filtered_df.columns:
    branch_df = (
        filtered_df.groupby("สาขา")[numeric_cols].mean().reset_index()
    )
    # ทำให้อยู่ในรูป Long format เพื่อทำ Bar chart แบบจัดกลุ่ม
    branch_melted = branch_df.melt(
        id_vars="สาขา", value_vars=numeric_cols, var_name="KPI", value_name="Score"
    )

    fig_bar = px.bar(
        branch_melted,
        x="สาขา",
        y="Score",
        color="KPI",
        barmode="group",
        title="เปรียบเทียบผลคะแนน KPI แยกตามสาขา",
        text_auto=".1f",
    )
    st.plotly_chart(fig_bar, use_container_width=True)
  else:
    st.info("ไม่มีข้อมูลเพียงพอสำหรับแสดงกราฟสาขา")

with tab3:
  st.subheader("ข้อมูลตาราง (Filtered Data)")
  st.dataframe(filtered_df, use_container_width=True)

# ---------------------------------------------------------
# 6. ฟอร์มสำหรับเพิ่มข้อมูลใหม่ (Add New Record) ลง Google Sheets
# ---------------------------------------------------------
st.markdown("---")
with st.expander("➕ เพิ่มข้อมูล KPI ใหม่ลงใน Google Sheets"):
  with st.form("add_data_form"):
    st.markdown("กรอกข้อมูลฟอร์มด้านล่างเพื่อบันทึกข้อมูลเข้า Google Sheets ทันที")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
      f_no = st.text_input("ที่ (ลำดับ)", value="1")
      f_branch = st.selectbox(
          "สาขา", options=["บางพลี", "สำโรง", "กิ่งแก้ว", "ประเวศ", "อื่นๆ"]
      )
    with col_f2:
      f_year = st.text_input("ปี", value=str(datetime.now().year))
      f_month = st.selectbox(
          "เดือน",
          options=[
              "01 มกราคม",
              "02 กุมภาพันธ์",
              "03 มีนาคม",
              "04 เมษายน",
              "05 พฤษภาคม",
              "06 มิถุนายน",
              "07 กรกฎาคม",
              "08 สิงหาคม",
              "09 กันยายน",
              "10 ตุลาคม",
              "11 พฤศจิกายน",
              "12 ธันวาคม",
          ],
      )
    with col_f3:
      f_checklist = st.number_input("Chicklist", value=0.0, format="%.2f")
      f_prepaid = st.number_input(
          "ความสำเร็จบิล Prepaid", value=0.0, format="%.2f"
      )

    col_f4, col_f5, col_f6 = st.columns(3)
    with col_f4:
      f_delivery = st.number_input("มาตรฐานจัดส่ง", value=0.0, format="%.2f")
    with col_f5:
      f_pdo = st.number_input("ความสำเร็จของ PDO", value=0.0, format="%.2f")
    with col_f6:
      f_score = st.number_input("สรุปผลคะแนน", value=0.0, format="%.2f")

    submitted = st.form_submit_button("💾 บันทึกข้อมูลไปยัง Google Sheets")

    if submitted:
      try:
        new_row = [
            f_no,
            f_branch,
            f_year,
            f_month,
            f_checklist,
            f_prepaid,
            f_delivery,
            f_pdo,
            f_score,
        ]
        sheet.append_row(new_row)
        st.success(
            "✅ บันทึกข้อมูลสำเร็จ! รีเฟรชหน้าจอหรือรอสักครู่เพื่อดูข้อมูลใหม่"
        )
        st.cache_data.clear()  # ล้าง Cache เพื่อดึงข้อมูลใหม่ล่าสุด
      except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")
