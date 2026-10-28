import json
import calendar
from datetime import date
from pathlib import Path
import streamlit as st
import pandas as pd

DATA_FILE = Path(__file__).with_name('tasks.json')
st.set_page_config(page_title='Smart Study Planner', page_icon='📚', layout='wide')

def load_tasks():
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding='utf-8'))
            return data if isinstance(data, list) else []
        except (ValueError, OSError):
            st.warning('อ่านข้อมูลเดิมไม่ได้ เริ่มด้วยรายการว่าง')
    return []

def save_tasks(tasks):
    DATA_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding='utf-8')

def priority_score(task):
    days = (date.fromisoformat(task['due']) - date.today()).days
    urgency = 50 if days <= 0 else 40 if days <= 1 else 30 if days <= 3 else 20 if days <= 7 else 10
    return urgency + int(task['difficulty']) * 6 + min(float(task['hours']), 10) * 2

def priority_label(score):
    if score >= 75:
        return '🔴 เร่งด่วนมาก'
    elif score >= 55:
        return '🟡 ควรทำเร็ว ๆ นี้'
    return '🟢 วางแผนล่วงหน้า'

def render_calendar(tasks):
    st.subheader('🗓️ ปฏิทินงานและกำหนดส่ง')
    st.caption('แสดงวันกำหนดส่งของงานที่เพิ่มไว้ในระบบ')
    today = date.today()
    if 'calendar_year' not in st.session_state:
        st.session_state.calendar_year = today.year
    if 'calendar_month' not in st.session_state:
        st.session_state.calendar_month = today.month
    year = st.session_state.calendar_year
    month = st.session_state.calendar_month
    left, center, right = st.columns([1, 4, 1])
    with left:
        if st.button('◀ เดือนก่อน', use_container_width=True):
            st.session_state.calendar_year = year - 1 if month == 1 else year
            st.session_state.calendar_month = 12 if month == 1 else month - 1
            st.rerun()
    with center:
        st.markdown(f'<h3 style="text-align:center">{calendar.month_name[month]} {year + 543}</h3>', unsafe_allow_html=True)
    with right:
        if st.button('เดือนถัดไป ▶', use_container_width=True):
            st.session_state.calendar_year = year + 1 if month == 12 else year
            st.session_state.calendar_month = 1 if month == 12 else month + 1
            st.rerun()
    day_names = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัส', 'ศุกร์', 'เสาร์', 'อาทิตย์']
    headers = st.columns(7)
    for col, label in zip(headers, day_names):
        col.markdown(f'**{label}**')
    by_date = {}
    for task in tasks:
        by_date.setdefault(task['due'], []).append(task)
    for week in calendar.monthcalendar(year, month):
        cols = st.columns(7)
        for index, day in enumerate(week):
            with cols[index]:
                if day == 0:
                    st.container(height=116, border=False)
                    continue
                current = date(year, month, day)
                daily = by_date.get(current.isoformat(), [])
                with st.container(height=116, border=True):
                    st.markdown(f'**{day}**' + (' 🔵' if current == today else ''))
                    for task in daily[:2]:
                        marker = '✅' if task['done'] else ('🔴' if current < today else '🟡')
                        st.caption(f"{marker} {task['subject']}: {task['name']}")
                    if len(daily) > 2:
                        st.caption(f'+ อีก {len(daily)-2} งาน')
    st.divider()
    chosen = st.date_input('เลือกวันที่เพื่อดูรายละเอียด', value=today, key='calendar_selected_date')
    selected = by_date.get(chosen.isoformat(), [])
    if not selected:
        st.info('ไม่มีงานกำหนดส่งในวันที่เลือก')
    for task in selected:
        with st.container(border=True):
            st.write(f"**{task['subject']} — {task['name']}**")
            st.write(f"ความยาก {task['difficulty']}/5 · {task['hours']} ชั่วโมง · {priority_label(priority_score(task))}")
            st.caption('สถานะ: ทำเสร็จแล้ว' if task['done'] else 'สถานะ: ยังไม่เสร็จ')
    st.caption('หมายเหตุ: ปฏิทินนี้แสดงวันกำหนดส่ง ไม่ใช่ตารางแบ่งเวลาอ่านรายวัน')

if 'tasks' not in st.session_state:
    st.session_state.tasks = load_tasks()
tasks = st.session_state.tasks

st.title('📚 Smart Study Planner')
st.caption('ผู้ช่วยจัดการงานและจัดลำดับการอ่านหนังสือด้วย Python')
page = st.sidebar.radio('เมนู', ['📊 Dashboard', '➕ เพิ่มงาน', '📋 จัดการงาน', '🗓️ แผนอ่านหนังสือ', '📅 ปฏิทิน'])

if page == '➕ เพิ่มงาน':
    st.subheader('เพิ่มงานใหม่')
    with st.form('add_task'):
        subject = st.text_input('ชื่อวิชา')
        task_name = st.text_input('ชื่องาน')
        due = st.date_input('กำหนดส่ง', min_value=date.today())
        difficulty = st.slider('ระดับความยาก', 1, 5, 3)
        hours = st.number_input('เวลาที่คาดว่าจะใช้ (ชั่วโมง)', min_value=0.5, max_value=100.0, value=2.0, step=0.5)
        submitted = st.form_submit_button('บันทึกงาน')
    if submitted:
        if not subject.strip() or not task_name.strip():
            st.error('กรุณากรอกชื่อวิชาและชื่องาน')
        else:
            task_id = max([t['id'] for t in tasks], default=0) + 1
            tasks.append({'id':task_id,'subject':subject.strip(),'name':task_name.strip(),'due':due.isoformat(),'difficulty':difficulty,'hours':hours,'done':False})
            save_tasks(tasks)
            st.success('เพิ่มงานเรียบร้อยแล้ว')

elif page == '📊 Dashboard':
    total = len(tasks)
    completed = sum(1 for t in tasks if t['done'])
    pending = [t for t in tasks if not t['done']]
    a,b,c = st.columns(3)
    a.metric('งานทั้งหมด', total)
    b.metric('ทำเสร็จแล้ว', completed)
    c.metric('ยังไม่เสร็จ', len(pending))
    st.progress(completed / total if total else 0)
    st.subheader('งานที่ควรทำก่อน')
    if pending:
        ordered = sorted(pending, key=priority_score, reverse=True)
        rows = [{'วิชา':t['subject'],'งาน':t['name'],'กำหนดส่ง':t['due'],'คะแนน':priority_score(t),'ระดับ':priority_label(priority_score(t))} for t in ordered]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.subheader('จำนวนงานตามวิชา')
        counts = pd.Series([t['subject'] for t in pending]).value_counts()
        st.bar_chart(counts)
    else:
        st.info('ยังไม่มีงานค้าง เพิ่มงานใหม่ได้จากเมนูด้านซ้าย')

elif page == '📋 จัดการงาน':
    st.subheader('รายการงาน')
    if not tasks:
        st.info('ยังไม่มีงาน')
    for task in list(tasks):
        with st.container(border=True):
            st.write(f"**{task['subject']} — {task['name']}**")
            st.caption(f"ส่ง {task['due']} | ความยาก {task['difficulty']}/5 | {task['hours']} ชม. | {priority_label(priority_score(task))}")
            col1,col2 = st.columns(2)
            if col1.button('↩️ ยกเลิกเสร็จ' if task['done'] else '✅ ทำเสร็จ', key=f"done_{task['id']}"):
                task['done'] = not task['done']
                save_tasks(tasks)
                st.rerun()
            if col2.button('🗑️ ลบ', key=f"del_{task['id']}"):
                tasks.remove(task)
                save_tasks(tasks)
                st.rerun()

elif page == '🗓️ แผนอ่านหนังสือ':
    st.subheader('แนะนำงานที่ควรอ่าน')
    available = st.slider('เวลาว่างวันนี้ (ชั่วโมง)', 1, 12, 3)
    remaining = float(available)
    pending = sorted([t for t in tasks if not t['done']], key=priority_score, reverse=True)
    if not pending:
        st.info('ไม่มีงานค้าง')
    else:
        for task in pending:
            if remaining <= 0:
                break
            allocated = min(float(task['hours']), remaining)
            st.write(f"📖 **{task['subject']} — {task['name']}**: แนะนำ {allocated:g} ชั่วโมง")
            remaining -= allocated
        st.caption(f'เวลาว่างที่ยังไม่ถูกจัดสรร: {remaining:g} ชั่วโมง')
        st.info('แผนนี้เป็นคำแนะนำเบื้องต้น ยังไม่บันทึกเวลาอ่านจริงหรือแบ่งงานข้ามวัน')

elif page == '📅 ปฏิทิน':
    render_calendar(tasks)
