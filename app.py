"""Smart Study Planner: priorities, study logs, multi-day calendar and backup."""
import calendar
import json
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Smart Study Planner', page_icon='📚', layout='wide')
DATA_FILE = Path(__file__).with_name('tasks.json')


def normalize(items):
    if not isinstance(items, list):
        raise ValueError('ไฟล์ต้องเป็นรายการงาน JSON')
    result = []
    ids = set()
    for t in items:
        if not isinstance(t, dict) or not all(k in t for k in ('id','subject','name','due','difficulty','hours')):
            raise ValueError('ข้อมูลบางงานไม่ครบ')
        t = dict(t)
        t['id'] = int(t['id'])
        if t['id'] in ids:
            raise ValueError('รหัสงานซ้ำ')
        ids.add(t['id'])
        date.fromisoformat(t['due'])
        t['hours'] = float(t['hours'])
        t['difficulty'] = int(t['difficulty'])
        if not 0 < t['hours'] <= 100 or not 1 <= t['difficulty'] <= 5:
            raise ValueError('ชั่วโมงหรือความยากไม่ถูกต้อง')
        t['subject'] = str(t['subject']).strip()
        t['name'] = str(t['name']).strip()
        if not t['subject'] or not t['name']:
            raise ValueError('ชื่อวิชาและชื่องานต้องไม่ว่าง')
        t['done'] = bool(t.get('done', False))
        t['studied'] = round(float(t.get('studied', 0)), 2)
        if not 0 <= t['studied'] <= t['hours']:
            raise ValueError('ชั่วโมงที่อ่านแล้วไม่ถูกต้อง')
        result.append(t)
    return result


def load_tasks():
    if not DATA_FILE.exists():
        return []
    try:
        return normalize(json.loads(DATA_FILE.read_text(encoding='utf-8')))
    except (ValueError, OSError, TypeError) as error:
        st.error(f'อ่านไฟล์งานไม่ได้: {error} กรุณากู้คืนจากไฟล์สำรอง')
        return []


def save_tasks(tasks):
    try:
        DATA_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding='utf-8')
        return True
    except OSError as error:
        st.error(f'บันทึกไม่สำเร็จ: {error}')
        return False


def remaining_hours(task):
    return 0 if task['done'] else max(0, round(task['hours'] - task['studied'], 2))


def priority_score(task):
    days = (date.fromisoformat(task['due']) - date.today()).days
    urgency = 50 if days <= 0 else 40 if days <= 1 else 30 if days <= 3 else 20 if days <= 7 else 10
    return int(urgency + task['difficulty'] * 6 + min(remaining_hours(task), 10) * 2)


def priority_label(score):
    if score >= 75:
        return '🔴 เร่งด่วนมาก'
    elif score >= 55:
        return '🟡 ควรทำเร็ว ๆ นี้'
    return '🟢 วางแผนล่วงหน้า'


def build_schedule(tasks, daily_hours, start, horizon=60):
    """Allocate remaining hours by due date, then priority, over multiple days."""
    pending = [t for t in tasks if remaining_hours(t) > 0]
    pending.sort(key=lambda t: (t['due'], -priority_score(t)))
    left = {t['id']: remaining_hours(t) for t in pending}
    rows = []
    for offset in range(horizon):
        current = start + timedelta(days=offset)
        capacity = float(daily_hours)
        for task in pending:
            if capacity <= 0:
                break
            if left[task['id']] <= 0:
                continue
            allocation = round(min(left[task['id']], capacity), 2)
            if allocation <= 0:
                continue
            rows.append({'date': current.isoformat(), 'id': task['id'], 'subject': task['subject'],
                         'name': task['name'], 'hours': allocation, 'due': task['due'],
                         'late': current > date.fromisoformat(task['due'])})
            left[task['id']] = round(left[task['id']] - allocation, 2)
            capacity = round(capacity - allocation, 2)
        if all(value <= 0 for value in left.values()):
            break
    return rows, sum(left.values())


def render_calendar(tasks, schedule):
    st.subheader('📅 ปฏิทินการเรียน')
    st.caption('ดูแผนอ่านและวันกำหนดส่งในที่เดียว')
    today = date.today()
    if 'cal_month' not in st.session_state:
        st.session_state.cal_month = today.replace(day=1)
    first = st.session_state.cal_month
    prev, middle, nxt = st.columns([1, 4, 1])
    if prev.button('◀', help='เดือนก่อนหน้า'):
        st.session_state.cal_month = (first - timedelta(days=1)).replace(day=1)
        st.rerun()
    middle.markdown(f'#### {first.month:02d}/{first.year + 543}')
    if nxt.button('▶', help='เดือนถัดไป'):
        st.session_state.cal_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
        st.rerun()

    by_day = {}
    due_by_day = {}
    for row in schedule:
        by_day.setdefault(row['date'], []).append(row)
    for task in tasks:
        due_by_day.setdefault(task['due'], []).append(task)

    st.caption('📘 มีแผนอ่าน   🔔 มีกำหนดส่ง   ⭐ วันนี้')
    for col, name in zip(st.columns(7), ['จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส', 'อา']):
        col.markdown(f'**{name}**')
    for week in calendar.monthcalendar(first.year, first.month):
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                with st.container(border=True, height=92):
                    if not day:
                        continue
                    key = date(first.year, first.month, day).isoformat()
                    st.markdown(f'**{day}**' + (' ⭐' if key == today.isoformat() else ''))
                    if key in by_day:
                        st.caption(f'📘 {sum(r["hours"] for r in by_day[key]):g} ชม.')
                    if key in due_by_day:
                        st.caption(f'🔔 {len(due_by_day[key])} งาน')

    selected = st.date_input('ดูรายละเอียดวันที่', value=today, key='calendar_selected', format='DD/MM/YYYY')
    key = selected.isoformat()
    with st.container(border=True):
        st.markdown(f'**รายละเอียดวันที่ {selected.strftime("%d/%m/%Y")}**')
        if not by_day.get(key) and not due_by_day.get(key):
            st.caption('ไม่มีแผนอ่านหรือกำหนดส่งในวันนี้')
        for row in by_day.get(key, []):
            st.write(f'📘 {row["subject"]} — {row["name"]}: {row["hours"]:g} ชม.' + (' ⚠️ เลยกำหนด' if row['late'] else ''))
        for task in due_by_day.get(key, []):
            st.write(f'🔔 กำหนดส่ง: {task["subject"]} — {task["name"]}' + (' ✅' if task['done'] else ''))

if 'tasks' not in st.session_state:
    st.session_state.tasks = load_tasks()
tasks = st.session_state.tasks
st.title('📚 Smart Study Planner')
st.caption('วางแผนการเรียนให้ง่ายขึ้นใน 3 หน้าหลัก')
page = st.sidebar.radio('เมนู', ['📊 หน้าหลัก', '📝 งานของฉัน', '📅 ปฏิทินการเรียน'])

if page == '📊 หน้าหลัก':
    completed = sum(t['done'] for t in tasks)
    pending = [t for t in tasks if not t['done']]
    a, b, c, d = st.columns(4)
    a.metric('งานทั้งหมด', len(tasks))
    b.metric('ทำเสร็จแล้ว', completed)
    c.metric('ยังไม่เสร็จ', len(pending))
    d.metric('อ่านแล้ว', f"{sum(t['studied'] for t in tasks):g} ชม.")
    st.progress(completed / len(tasks) if tasks else 0)
    st.subheader('งานที่ควรทำก่อน')
    if pending:
        ordered = sorted(pending, key=priority_score, reverse=True)
        rows = [{'วิชา': t['subject'], 'งาน': t['name'], 'กำหนดส่ง': t['due'],
                 'เหลือ (ชม.)': remaining_hours(t), 'คะแนน': priority_score(t),
                 'ระดับ': priority_label(priority_score(t))} for t in ordered]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        with st.expander('📊 ดูกราฟจำนวนงานค้างตามวิชา'):
            st.bar_chart(pd.Series([t['subject'] for t in pending]).value_counts())
    else:
        st.info('ยังไม่มีงานค้าง')

    with st.expander('💾 สำรองและกู้คืนข้อมูล'):
        st.caption('ควรดาวน์โหลดสำรองเป็นระยะ เพราะข้อมูลบน Streamlit Community Cloud อาจหายหลังรีสตาร์ตหรือ Deploy ใหม่')
        st.download_button('⬇️ ดาวน์โหลด tasks.json',
            data=json.dumps(tasks, ensure_ascii=False, indent=2),
            file_name='tasks.json', mime='application/json')
        uploaded = st.file_uploader('เลือกไฟล์ JSON ที่สำรองไว้', type=['json'])
        confirm = st.checkbox('ยืนยันว่าต้องการแทนที่รายการงานปัจจุบัน')
        if st.button('กู้คืนข้อมูล', disabled=uploaded is None or not confirm):
            try:
                restored = normalize(json.loads(uploaded.getvalue().decode('utf-8')))
            except (ValueError, UnicodeDecodeError, TypeError) as error:
                st.error(f'ไฟล์ไม่ถูกต้อง: {error}')
            else:
                if save_tasks(restored):
                    st.session_state.tasks = restored
                    st.rerun()

elif page == '📝 งานของฉัน':
    st.subheader('📝 งานของฉัน')
    with st.expander('➕ เพิ่มงานใหม่', expanded=not bool(tasks)):
        with st.form('add_task', clear_on_submit=True):
            subject = st.text_input('ชื่อวิชา')
            task_name = st.text_input('ชื่องาน')
            due = st.date_input('กำหนดส่ง', min_value=date.today())
            difficulty = st.slider('ระดับความยาก', 1, 5, 3)
            hours = st.number_input('เวลาที่คาดว่าจะใช้ (ชั่วโมง)', 0.5, 100.0, 2.0, 0.5)
            submitted = st.form_submit_button('บันทึกงาน', type='primary')
        if submitted:
            if not subject.strip() or not task_name.strip():
                st.error('กรุณากรอกชื่อวิชาและชื่องาน')
            else:
                task_id = max([t['id'] for t in tasks], default=0) + 1
                new_task = {'id': task_id, 'subject': subject.strip(), 'name': task_name.strip(),
                            'due': due.isoformat(), 'difficulty': difficulty, 'hours': float(hours),
                            'studied': 0.0, 'done': False}
                if save_tasks([*tasks, new_task]):
                    tasks.append(new_task)
                    st.rerun()

    st.markdown('#### รายการงาน')
    filter_mode = st.selectbox('แสดงงาน', ['ทั้งหมด', 'ยังไม่เสร็จ', 'เสร็จแล้ว'])
    visible = [t for t in tasks if filter_mode == 'ทั้งหมด' or
               (filter_mode == 'เสร็จแล้ว' and t['done']) or
               (filter_mode == 'ยังไม่เสร็จ' and not t['done'])]
    if not visible:
        st.info('ไม่มีงานในหมวดนี้')
    for task in sorted(visible, key=lambda t: (t['done'], t['due'])):
        with st.expander(('✅ ' if task['done'] else '📖 ') + task['subject'] + ' — ' + task['name']):
            st.caption(f"ส่ง {task['due']} | ความยาก {task['difficulty']}/5 | {priority_label(priority_score(task))}")
            st.write(f"อ่านแล้ว {task['studied']:g}/{task['hours']:g} ชั่วโมง")
            st.progress(min(1.0, task['studied'] / task['hours']))
            if not task['done'] and remaining_hours(task) > 0:
                with st.form(f"log_{task['id']}"):
                    amount = st.number_input('เพิ่มชั่วโมงที่อ่านจริง', min_value=0.1,
                        max_value=float(remaining_hours(task)),
                        value=min(0.5, float(remaining_hours(task))), step=0.1,
                        key=f"amount_{task['id']}")
                    if st.form_submit_button('📖 บันทึกเวลาอ่าน'):
                        task['studied'] = round(min(task['hours'], task['studied'] + amount), 2)
                        if task['studied'] >= task['hours']:
                            task['done'] = True
                        if save_tasks(tasks):
                            st.rerun()
            col1, col2 = st.columns(2)
            if col1.button('↩️ ยกเลิกเสร็จ' if task['done'] else '✅ ทำเสร็จ', key=f"done_{task['id']}"):
                task['done'] = not task['done']
                if save_tasks(tasks):
                    st.rerun()
            if col2.button('🗑️ ลบ', key=f"del_{task['id']}"):
                if save_tasks([t for t in tasks if t['id'] != task['id']]):
                    tasks.remove(task)
                    st.rerun()

elif page == '📅 ปฏิทินการเรียน':
    daily_hours = st.slider('เวลาว่างสำหรับอ่านหนังสือต่อวัน (ชั่วโมง)', 0.5, 12.0, 2.0, 0.5)
    schedule, unscheduled = build_schedule(tasks, daily_hours, date.today())
    render_calendar(tasks, schedule)
    if any(r['late'] for r in schedule):
        st.warning('บางช่วงถูกจัดให้อ่านหลังวันกำหนดส่ง ลองเพิ่มเวลาว่างต่อวัน')
    if unscheduled:
        st.warning(f'มีชั่วโมงอ่านที่ยังจัดไม่ครบ {unscheduled:g} ชั่วโมงในช่วง 60 วัน')
    with st.expander('📋 ดูตารางอ่านหนังสือทั้งหมด'):
        if schedule:
            rows = [{'วันที่': r['date'], 'วิชา': r['subject'], 'งาน': r['name'],
                     'เวลา (ชม.)': r['hours'], 'กำหนดส่ง': r['due'],
                     'หมายเหตุ': '⚠️ หลังวันส่ง' if r['late'] else ''} for r in schedule]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        else:
            st.info('ยังไม่มีงานที่ต้องจัดตาราง')
        st.caption('ตารางนี้เป็นคำแนะนำที่คำนวณใหม่ ไม่ใช่บันทึกเวลาอ่านจริง')
