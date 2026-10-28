"""Smart Study Planner: priorities, study logs, multi-day calendar and backup."""
import calendar
import base64
import html
import json
import random
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Smart Study Planner', page_icon='🌟', layout='wide')
DATA_FILE = Path(__file__).with_name('tasks.json')

# สีหลักจากธีมแฟนตาซี: charcoal / mint / coral / amber / white
# ใช้ state เพื่อไม่ให้โหมดสว่าง/มืดเปลี่ยนเมื่อกดปุ่มอื่น
if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = '☀️ โหมดสว่าง'

def theme_styles(dark):
    bg = '#192832' if dark else '#F7FBFA'
    panel = '#273941' if dark else '#FFFFFF'
    text = '#F5FAFA' if dark else '#292F36'
    muted = '#C4D6D6' if dark else '#52636B'
    line = '#496068' if dark else '#D9ECE9'
    hover = '#324A50' if dark else '#E8FAF7'
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@400;500;600;700&family=Mali:wght@500;600;700&display=swap');
    :root {{--ink:{text};--mint:#4ECDC4;--coral:#FF6B6B;--amber:#F3AF50;--paper:{panel};}}
    html,body,[data-testid='stAppViewContainer'],[data-testid='stSidebar'],button,input,textarea,select {{font-family:'Prompt','Noto Sans Thai',sans-serif !important;}}
    [data-testid='stAppViewContainer'] {{background:{bg};color:{text};}}
    [data-testid='stAppViewContainer'] p,[data-testid='stAppViewContainer'] label,[data-testid='stAppViewContainer'] span,[data-testid='stAppViewContainer'] li {{color:{text};}}
    [data-testid='stAppViewContainer'] small,[data-testid='stCaptionContainer'] p {{color:{muted} !important;}}
    [data-testid='stSidebar'] {{background:#292F36;}}
    [data-testid='stSidebar'] * {{color:white !important;}}
    [data-testid='stSidebar'] [role='radiogroup'] label {{border-radius:12px;padding:10px 12px;transition:background .2s ease,transform .2s ease;}}
    [data-testid='stSidebar'] [role='radiogroup'] label:hover {{background:#3D5558;transform:translateX(3px);}}
    h1,h2,h3,h4 {{color:{text} !important;letter-spacing:-.02em;}}
    h1,h2,h3 {{transition:transform .22s ease,color .22s ease;}}
    h1:hover,h2:hover,h3:hover {{transform:translateX(5px);color:#4ECDC4 !important;}}
    [data-testid='stMetric'],[data-testid='stVerticalBlockBorderWrapper'] {{background:{panel};border:1px solid {line};border-radius:17px;}}
    [data-testid='stMetric'] {{padding:15px;}}
    [data-testid='stMetricValue'],[data-testid='stMetricLabel'] {{color:{text} !important;}}
    [data-testid='stExpander'] {{background:{panel};border:1px solid {line};border-radius:14px;}}
    [data-testid='stExpander'] summary {{color:{text};}}
    [data-testid='stDataFrame'] {{border-radius:12px;}}
    div.stButton > button,div.stFormSubmitButton > button,div.stDownloadButton > button {{border-radius:13px;font-weight:600;transition:transform .17s ease,box-shadow .17s ease;}}
    div.stButton > button:hover,div.stFormSubmitButton > button:hover,div.stDownloadButton > button:hover {{transform:translateY(-2px);box-shadow:0 6px 17px #4ECDC433;}}
    div.stButton > button[kind='primary'],div.stFormSubmitButton > button[kind='primary'] {{background:#4ECDC4;color:#17343A;border:1px solid #36BDB3;}}
    div.stButton > button[kind='primary']:hover,div.stFormSubmitButton > button[kind='primary']:hover {{background:#F3AF50;color:#292F36;border-color:#F3AF50;}}
    div.stButton > button[kind='secondary'] {{background:{panel};color:{text};border:1px solid {line};}}
    div.stButton > button[kind='secondary']:hover {{background:{hover};border-color:#4ECDC4;color:{text};}}
    [data-testid='stProgress'] [role='progressbar'] > div {{background:#4ECDC4 !important;}}
    .hero-panel {{background:linear-gradient(120deg,#292F36,#36535A);border:1px solid #4ECDC477;border-radius:22px;padding:24px 26px;margin:8px 0 16px;box-shadow:0 10px 30px #111A2430;position:relative;overflow:hidden;}}
    .hero-panel::after {{content:'✦  ✧  ✦';position:absolute;right:18px;top:12px;color:#F3AF50;opacity:.65;letter-spacing:12px;font-size:21px;pointer-events:none;}}
    .hero-panel strong {{color:#4ECDC4;font-family:'Mali','Prompt',sans-serif;font-size:clamp(1.08rem,2.2vw,1.5rem);line-height:1.6;display:block;max-width:85%;}}
    .hero-panel p {{margin:8px 0 0;color:#F6F9F7 !important;line-height:1.75;}}
    .stAlert {{border-radius:13px;}}
    @media (prefers-reduced-motion:reduce) {{h1,h2,h3,div.stButton > button,div.stFormSubmitButton > button {{transition:none!important;transform:none!important;}}}}
    </style>"""

# คำคมเปลี่ยนเฉพาะเมื่อกลับมาหน้าหลัก ไม่เปลี่ยนทุกครั้งที่กดปุ่มในหน้าเดียวกัน
QUOTES = [
    ('ทุกความฝัน เริ่มจากหนึ่งหน้าที่ลงมืออ่าน', 'ก้าวเล็ก ๆ ในวันนี้ อาจกลายเป็นเรื่องราวยิ่งใหญ่ในวันหน้า'),
    ('เรียนรู้วันนี้ เปล่งประกายในวันหน้า', 'ทุกบทเรียนคือดาวอีกดวงบนเส้นทางความฝัน'),
    ('Little Steps, Big Dreams', 'ไม่ต้องรีบไปให้ถึง แค่ไม่หยุดเรียนรู้ก็พอ'),
    ('เปิดหนังสือหนึ่งหน้า เข้าใกล้ความฝันอีกหนึ่งก้าว', 'ทำวันนี้ให้ดี แล้วค่อย ๆ เติบโตในจังหวะของเรา'),
    ('Your Future Is Written Today', 'ทุกงานที่ลงมือทำ คือหนึ่งบรรทัดของอนาคต'),
    ('ความสำเร็จเริ่มจากความตั้งใจเล็ก ๆ', 'เริ่มจากงานหนึ่งชิ้น แล้วให้ความพยายามพาไปต่อ'),
    ('วันนี้อ่านอีกนิด พรุ่งนี้เก่งขึ้นอีกหน่อย', 'สะสมความรู้เหมือนเก็บดาวทีละดวง'),
    ('อย่าให้เป้าหมายใหญ่ ทำให้ลืมก้าวแรก', 'เริ่มจากสิ่งที่ทำได้ในวันนี้'),
    ('เติบโตไปพร้อมกับทุกบทเรียน', 'ไม่ต้องสมบูรณ์แบบ แค่เรียนรู้เพิ่มขึ้นทุกวัน'),
    ('สร้างจักรวาลของตัวเองด้วยความรู้', 'ทุกวิชามีเรื่องใหม่ให้ค้นพบเสมอ'),
]

def next_quote():
    previous = st.session_state.get('quote_index', -1)
    options = [i for i in range(len(QUOTES)) if i != previous]
    st.session_state.quote_index = random.choice(options)


def image_bytes(task):
    """อ่านรูปที่เก็บใน JSON อย่างปลอดภัย (ถ้าไม่มีให้คืน None)."""
    encoded = task.get('image_b64', '')
    if not encoded:
        return None
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error):
        return None


def subject_image(tasks, subject):
    """ใช้ภาพล่าสุดที่ผู้ใช้ใส่ให้รายวิชาเดียวกัน."""
    for task in reversed(tasks):
        if task['subject'] == subject and image_bytes(task):
            return image_bytes(task)
    return None



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
        t['image_b64'] = str(t.get('image_b64', ''))
        logs = t.get('logs', [])
        if not isinstance(logs, list):
            raise ValueError('ประวัติการอ่านต้องเป็นรายการ')
        cleaned_logs = []
        for entry in logs:
            if not isinstance(entry, dict):
                raise ValueError('รายการประวัติการอ่านไม่ถูกต้อง')
            log_date = date.fromisoformat(str(entry['date']))
            log_hours = float(entry['hours'])
            if not 0 < log_hours <= 100:
                raise ValueError('ชั่วโมงในประวัติไม่ถูกต้อง')
            cleaned_logs.append({'date': log_date.isoformat(), 'hours': log_hours})
        t['logs'] = cleaned_logs
        t['studied'] = round(float(t.get('studied', 0)), 2)
        if not 0 <= t['studied'] <= t['hours']:
            raise ValueError('ชั่วโมงที่อ่านแล้วไม่ถูกต้อง')
        # Older backups did not include logs. Their total is kept, but cannot be dated.
        if sum(x['hours'] for x in t['logs']) > t['studied'] + 0.011:
            raise ValueError('ประวัติการอ่านมากกว่าชั่วโมงที่อ่านสะสม')
        result.append(t)
    return result


def create_demo_tasks(existing, today=None):
    """สร้างงานตัวอย่าง 30 รายการ โดยไม่ลบงานจริงและไม่สร้างซ้ำ."""
    today = today or date.today()
    rng = random.Random(42631365)
    examples = {
        'ภาษาไทยเพื่อการสื่อสาร': [
            'สรุปหลักการสื่อสารอย่างมีประสิทธิภาพ', 'แบบฝึกหัดการเขียนจดหมาย', 'เตรียมพูดนำเสนอหน้าชั้น', 'วิเคราะห์บทความสั้น'],
        'ภาษาอังกฤษ': [
            'ทบทวนคำศัพท์ Unit 4', 'แบบฝึกหัด Past Simple', 'ฝึกบทสนทนาการแนะนำตัว', 'อ่านบทความแล้วตอบคำถาม'],
        'คณิตศาสตร์': [
            'แบบฝึกหัดสมการเชิงเส้น', 'ทบทวนกราฟฟังก์ชัน', 'สรุปสถิติเบื้องต้น', 'เตรียมสอบย่อยบทที่ 3'],
        'วิทยาศาสตร์': [
            'สรุประบบนิเวศ', 'รายงานการทดลองเรื่องสารละลาย', 'ทำใบงานพลังงาน', 'ทบทวนการเปลี่ยนสถานะของสาร'],
        'สังคมศาสตร์': [
            'ใบงานบทที่ 5', 'สรุปหน้าที่พลเมือง', 'ทำแผนผังเศรษฐกิจพอเพียง', 'เตรียมอภิปรายประเด็นสังคม'],
        'การเขียนโปรแกรม Python': [
            'ฝึก if elif else', 'ฝึก for และ while', 'เขียนฟังก์ชัน def', 'ทดสอบโปรเจกต์ Streamlit'],
        'การออกแบบและเทคโนโลยี': [
            'ออกแบบโปสเตอร์ประชาสัมพันธ์', 'จัดทำผังงาน Flowchart', 'ปรับหน้าเว็บให้ใช้งานง่าย'],
        'ประวัติศาสตร์': [
            'สรุปเหตุการณ์สำคัญ', 'ทำเส้นเวลาประวัติศาสตร์', 'ตอบคำถามท้ายบท'],
    }
    existing_demo = {t.get('demo_key') for t in existing}
    next_id = max((int(t['id']) for t in existing), default=0) + 1
    generated = []
    index = 0
    for subject, names in examples.items():
        for name in names:
            index += 1
            key = f'demo_2026_{index:02d}'
            if key in existing_demo:
                continue
            offset = rng.randint(-5, 35)
            difficulty = rng.randint(1, 5)
            hours = rng.choice([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0])
            done = index in (2, 7, 12, 18, 23, 29)
            generated.append({
                'id': next_id, 'subject': subject, 'name': name,
                'due': (today + timedelta(days=offset)).isoformat(),
                'difficulty': difficulty, 'hours': hours, 'studied': 0.0,
                'done': done, 'logs': [], 'image_b64': '', 'demo_key': key,
            })
            next_id += 1
    return generated


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
        temp = DATA_FILE.with_suffix('.tmp')
        temp.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding='utf-8')
        temp.replace(DATA_FILE)
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


def week_progress(tasks, today):
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    totals = {day.isoformat(): 0.0 for day in days}
    for task in tasks:
        for entry in task.get('logs', []):
            if entry['date'] in totals:
                totals[entry['date']] += float(entry['hours'])
    return [{'วันที่': d.strftime('%d/%m'), 'ชั่วโมง': round(totals[d.isoformat()], 2)} for d in days]


def deadline_alerts(tasks, today):
    alerts = []
    for task in tasks:
        if task['done']:
            continue
        days = (date.fromisoformat(task['due']) - today).days
        if days < 0:
            alerts.append(('error', f"{task['subject']} — {task['name']}: เลยกำหนด {abs(days)} วัน"))
        elif days == 0:
            alerts.append(('error', f"{task['subject']} — {task['name']}: ครบกำหนดวันนี้"))
        elif days <= 3:
            alerts.append(('warning', f"{task['subject']} — {task['name']}: เหลือ {days} วัน"))
    return alerts



# ---------- UI helpers ----------
def commit(new_tasks, message='บันทึกเรียบร้อย'):
    if save_tasks(new_tasks):
        st.session_state.tasks = new_tasks
        st.session_state.flash = message
        st.rerun()


def toggle_done(task_id):
    updated = [dict(t) for t in st.session_state.tasks]
    for task in updated:
        if task['id'] == task_id:
            task['done'] = not task['done']
            break
    commit(updated, 'อัปเดตสถานะงานแล้ว')


def render_task(task, prefix):
    """A compact task card used both on dashboard and calendar."""
    with st.container(border=True):
        left, right = st.columns([4, 1], vertical_alignment='center')
        with left:
            st.markdown(f"**{'✅ ' if task['done'] else '📌 '}{html.escape(task['name'])}**")
            st.caption(f"ส่ง {task['due']} · เหลือ {remaining_hours(task):g}/{task['hours']:g} ชม. · {priority_label(priority_score(task))}")
        with right:
            if st.button('↩️ เปิดใหม่' if task['done'] else '✓ เสร็จแล้ว', key=f'{prefix}_done_{task["id"]}', type='primary' if not task['done'] else 'secondary', use_container_width=True):
                toggle_done(task['id'])
        if not task['done']:
            st.progress(min(1.0, float(task['studied']) / float(task['hours'])))
            with st.popover('⏱️ บันทึกเวลา / ลบงาน'):
                if remaining_hours(task) > 0:
                    with st.form(f'{prefix}_log_{task["id"]}'):
                        amount = st.number_input('ชั่วโมงที่อ่านเพิ่ม', min_value=0.1,
                            max_value=max(0.1, float(remaining_hours(task))),
                            value=min(0.5, float(remaining_hours(task))), step=0.1)
                        if st.form_submit_button('บันทึกเวลาอ่าน', type='primary'):
                            updated = [dict(t) for t in st.session_state.tasks]
                            selected = next(t for t in updated if t['id'] == task['id'])
                            actual = round(min(float(amount), remaining_hours(selected)), 2)
                            selected['studied'] = round(min(selected['hours'], selected['studied'] + actual), 2)
                            selected['logs'] = [*selected.get('logs', []), {'date': date.today().isoformat(), 'hours': actual}]
                            if selected['studied'] >= selected['hours']:
                                selected['done'] = True
                            commit(updated, 'บันทึกเวลาอ่านเรียบร้อย')
                if st.button('🗑️ ลบงานนี้', key=f'{prefix}_del_{task["id"]}'):
                    commit([t for t in st.session_state.tasks if t['id'] != task['id']], 'ลบงานแล้ว')
        else:
            st.caption('งานนี้ทำเสร็จแล้ว สามารถกดเปิดใหม่ได้')
            if st.button('🗑️ ลบงานนี้', key=f'{prefix}_del_{task["id"]}'):
                commit([t for t in st.session_state.tasks if t['id'] != task['id']], 'ลบงานแล้ว')


def grouped_subjects(items):
    groups = {}
    for task in sorted(items, key=lambda t: (t['subject'].casefold(), t['due'], t['id'])):
        groups.setdefault(task['subject'], []).append(task)
    return groups


def render_subjects(items, prefix='home'):
    groups = grouped_subjects(items)
    if not groups:
        st.info('ยังไม่มีงาน กดเพิ่มงานเพื่อเริ่มต้น')
    for subject, subject_tasks in groups.items():
        done = sum(t['done'] for t in subject_tasks)
        with st.expander(f'📚 {subject}  ·  {done}/{len(subject_tasks)} งานเสร็จ', expanded=len(groups) == 1):
            picture = subject_image(st.session_state.tasks, subject)
            if picture:
                st.image(picture, width=150)
            for task in subject_tasks:
                render_task(task, prefix)


def go_to_calendar():
    st.session_state.navigation = '📅 ปฏิทิน'


def go_to_home():
    st.session_state.navigation = '🏠 หน้าหลัก'


if 'tasks' not in st.session_state:
    st.session_state.tasks = load_tasks()
tasks = st.session_state.tasks
if 'navigation' not in st.session_state:
    st.session_state.navigation = '🏠 หน้าหลัก'

st.sidebar.radio('🎨 รูปแบบสี', ['☀️ โหมดสว่าง', '🌙 โหมดมืด'], key='theme_mode')
st.markdown(theme_styles(st.session_state.theme_mode == '🌙 โหมดมืด'), unsafe_allow_html=True)
st.title('✦ Smart Study Planner')
st.caption('วางแผนการเรียน · ติดตามความคืบหน้า · จัดงานตามรายวิชา')
page = st.sidebar.radio('เมนู', ['🏠 หน้าหลัก', '📅 ปฏิทิน'], key='navigation')
if 'quote_index' not in st.session_state:
    next_quote()
if 'last_page' not in st.session_state:
    st.session_state.last_page = page
elif page == '🏠 หน้าหลัก' and st.session_state.last_page != page:
    next_quote()
st.session_state.last_page = page
if st.session_state.pop('flash', None):
    st.toast('บันทึกข้อมูลสำเร็จ ✓')

if page == '🏠 หน้าหลัก':
    quote_title, quote_desc = QUOTES[st.session_state.quote_index]
    st.markdown(f'<div class="hero-panel"><strong>✧ {html.escape(quote_title)}</strong><p>{html.escape(quote_desc)}</p></div>', unsafe_allow_html=True)
    completed = sum(t['done'] for t in tasks)
    pending = [t for t in tasks if not t['done']]
    # การ์ดสรุปคลิกได้: กรองรายการงานด้านล่างทันที
    if 'task_filter' not in st.session_state:
        st.session_state.task_filter = 'ทั้งหมด'
    a,b,c = st.columns(3)
    with a:
        if st.button(f'📚 งานทั้งหมด\\n\\n{len(tasks)} รายการ', key='stat_all',
                     use_container_width=True, type='primary' if st.session_state.task_filter == 'ทั้งหมด' else 'secondary'):
            st.session_state.task_filter = 'ทั้งหมด'
            st.rerun()
    with b:
        if st.button(f'✅ เสร็จแล้ว\\n\\n{completed} รายการ', key='stat_done',
                     use_container_width=True, type='primary' if st.session_state.task_filter == 'เสร็จแล้ว' else 'secondary'):
            st.session_state.task_filter = 'เสร็จแล้ว'
            st.rerun()
    with c:
        if st.button(f'🕒 รอดำเนินการ\\n\\n{len(pending)} รายการ', key='stat_pending',
                     use_container_width=True, type='primary' if st.session_state.task_filter == 'ยังไม่เสร็จ' else 'secondary'):
            st.session_state.task_filter = 'ยังไม่เสร็จ'
            st.rerun()
    st.progress(completed / len(tasks) if tasks else 0)
    st.caption('กดการ์ดด้านบนเพื่อเลือกดูงานทั้งหมด งานที่เสร็จแล้ว หรืองานที่ยังค้าง')
    st.markdown('<div id="task-list"></div>', unsafe_allow_html=True)
    st.markdown('[↓ ไปยังรายการงาน](#my-subjects)')

    action1, action2 = st.columns(2)
    with action1:
        st.button('📅 เปิดปฏิทินการเรียน', type='primary', use_container_width=True, on_click=go_to_calendar)
    with action2:
        if st.button('💾 ไปที่สำรองข้อมูล', use_container_width=True):
            st.session_state.show_backup = not st.session_state.get('show_backup', False)
    if st.session_state.get('show_backup', False):
        with st.container(border=True):
            st.markdown('**💾 สำรองและกู้คืนข้อมูล**')
            st.caption('ข้อมูลใน Streamlit Cloud อาจหายเมื่อรีสตาร์ต ควรดาวน์โหลดสำรองไว้')
            st.download_button('⬇️ ดาวน์โหลด tasks.json', json.dumps(tasks, ensure_ascii=False, indent=2),
                file_name='tasks.json', mime='application/json')
            uploaded = st.file_uploader('เลือกไฟล์ JSON เพื่อกู้คืน', type=['json'])
            confirm = st.checkbox('ยืนยันการแทนที่ข้อมูลปัจจุบัน')
            if st.button('กู้คืนข้อมูล', disabled=uploaded is None or not confirm):
                try:
                    restored = normalize(json.loads(uploaded.getvalue().decode('utf-8')))
                except (ValueError, UnicodeDecodeError, TypeError, KeyError) as error:
                    st.error(f'ไฟล์ไม่ถูกต้อง: {error}')
                else:
                    commit(restored, 'กู้คืนข้อมูลสำเร็จ')

    today = date.today()
    alerts = deadline_alerts(tasks, today)
    if alerts:
        with st.expander(f'🔔 งานใกล้กำหนด · {len(alerts)} รายการ', expanded=True):
            for level, message in alerts:
                (st.error if level == 'error' else st.warning)(message)

    st.subheader('🎯 Today Focus')
    daily_hours = st.session_state.get('daily_hours', 2.0)
    schedule, _ = build_schedule(tasks, daily_hours, today)
    focus = [r for r in schedule if r['date'] == today.isoformat()]
    if focus:
        for row in focus[:3]:
            task = next(t for t in tasks if t['id'] == row['id'])
            with st.container(border=True):
                col1,col2 = st.columns([4,1], vertical_alignment='center')
                with col1:
                    st.markdown(f"**{html.escape(task['subject'])} — {html.escape(task['name'])}**")
                    st.caption(f"แนะนำวันนี้ {row['hours']:g} ชม. · กำหนดส่ง {task['due']}")
                with col2:
                    if st.button('✓ เสร็จแล้ว', key=f'focus_{task["id"]}', type='primary', use_container_width=True):
                        toggle_done(task['id'])
        st.caption('บันทึกเวลาอ่านบางส่วนได้ที่หัวข้อรายวิชาด้านล่าง')
    else:
        st.success('วันนี้ไม่มีงานค้างตามแผน')

    st.markdown('<div id="my-subjects"></div>', unsafe_allow_html=True)
    st.subheader('📝 งานและรายวิชาของฉัน')
    with st.expander('🧪 ข้อมูลตัวอย่างสำหรับสาธิต (30 งาน)', expanded=False):
        st.caption('สร้างงานจำลอง 30 รายการจาก 8 วิชา สุ่มวันส่ง ความยาก และชั่วโมงอ่าน มีตัวอย่างงานเสร็จแล้ว 6 รายการ ไม่ลบงานที่คุณมี')
        demo_count = sum(bool(t.get('demo_key')) for t in tasks)
        st.write(f'มีงานตัวอย่างอยู่แล้ว {demo_count}/30 รายการ')
        if st.button('✨ เพิ่มงานตัวอย่างที่ยังไม่มี', key='seed_demo', type='primary'):
            new_samples = create_demo_tasks(tasks)
            if new_samples:
                commit([*tasks, *new_samples], f'เพิ่มตัวอย่าง {len(new_samples)} งานแล้ว')
            else:
                st.info('มีข้อมูลตัวอย่างครบ 30 งานแล้ว')
        if demo_count:
            if st.button('🧹 ลบเฉพาะงานตัวอย่าง', key='clear_demo'):
                commit([t for t in tasks if not t.get('demo_key')], 'ลบงานตัวอย่างแล้ว')

    with st.expander('➕ เพิ่มงานใหม่', expanded=not bool(tasks)):
        with st.form('add_task', clear_on_submit=True):
            subject = st.text_input('ชื่อวิชา', placeholder='เช่น ภาษาไทยเพื่อการสื่อสาร')
            task_name = st.text_input('ชื่องาน', placeholder='เช่น แบบฝึกหัดบทที่ 2')
            due = st.date_input('กำหนดส่ง', min_value=date.today())
            difficulty = st.slider('ความยาก', 1, 5, 3)
            hours = st.number_input('ชั่วโมงที่คาดว่าจะใช้', 0.5, 100.0, 2.0, 0.5)
            uploaded_image = st.file_uploader('ภาพรายวิชา (ไม่บังคับ · JPG/PNG ไม่เกิน 600 KB)', type=['jpg','jpeg','png'])
            submitted = st.form_submit_button('＋ เพิ่มงาน', type='primary', use_container_width=True)
        if submitted:
            if not subject.strip() or not task_name.strip():
                st.error('กรุณากรอกชื่อวิชาและชื่องาน')
            elif uploaded_image is not None and uploaded_image.size > 600*1024:
                st.error('ภาพต้องมีขนาดไม่เกิน 600 KB')
            else:
                encoded = base64.b64encode(uploaded_image.getvalue()).decode('ascii') if uploaded_image else ''
                new_task = {'id': max([t['id'] for t in tasks], default=0)+1,
                    'subject':subject.strip(), 'name':task_name.strip(), 'due':due.isoformat(),
                    'difficulty':difficulty, 'hours':float(hours), 'studied':0.0,
                    'done':False, 'logs':[], 'image_b64':encoded}
                commit([*tasks, new_task], 'เพิ่มงานสำเร็จ')

    filter_mode = st.segmented_control(
        'แสดงรายการ', ['ทั้งหมด','ยังไม่เสร็จ','เสร็จแล้ว'],
        key='task_filter'
    )
    visible = [t for t in tasks if filter_mode == 'ทั้งหมด' or
               (filter_mode == 'ยังไม่เสร็จ' and not t['done']) or
               (filter_mode == 'เสร็จแล้ว' and t['done'])]
    render_subjects(visible)

    with st.expander('📈 สรุปเวลาอ่านจริง 7 วันล่าสุด'):
        progress_rows = week_progress(tasks, today)
        total_week = sum(row['ชั่วโมง'] for row in progress_rows)
        st.metric('ชั่วโมงที่อ่านใน 7 วัน', f'{total_week:g} ชม.')
        st.bar_chart(pd.DataFrame(progress_rows).set_index('วันที่'), color='#4ECDC4')
        st.caption('กราฟนี้นับเฉพาะประวัติที่มีวันที่บันทึก')

elif page == '📅 ปฏิทิน':
    st.subheader('📅 ปฏิทินการเรียน')
    st.caption('เลือกวันที่เพื่อดูแผนอ่านและงานกำหนดส่ง · Smart Reschedule ปรับตามชั่วโมงที่เหลืออัตโนมัติ')
    daily_hours = st.slider('เวลาว่างอ่านหนังสือต่อวัน (ชั่วโมง)', 0.5, 12.0, 2.0, 0.5, key='daily_hours')
    schedule, unscheduled = build_schedule(tasks, daily_hours, date.today())
    if 'cal_month' not in st.session_state:
        st.session_state.cal_month = date.today().replace(day=1)
    first = st.session_state.cal_month
    prev, heading, nxt = st.columns([1,4,1], vertical_alignment='center')
    if prev.button('◀ เดือนก่อน', use_container_width=True):
        st.session_state.cal_month = (first-timedelta(days=1)).replace(day=1)
        st.rerun()
    heading.markdown(f'### {first.strftime("%m")}/{first.year+543}')
    if nxt.button('เดือนถัดไป ▶', use_container_width=True):
        st.session_state.cal_month = (first.replace(day=28)+timedelta(days=4)).replace(day=1)
        st.rerun()
    by_day, due_by_day = {}, {}
    for row in schedule:
        by_day.setdefault(row['date'], []).append(row)
    for task in tasks:
        due_by_day.setdefault(task['due'], []).append(task)
    st.caption('🟢 มีแผนอ่าน · 🟠 มีกำหนดส่ง · ⭐ วันนี้')
    for col, label in zip(st.columns(7), ['จ','อ','พ','พฤ','ศ','ส','อา']):
        col.markdown(f'**{label}**')
    for week in calendar.monthcalendar(first.year, first.month):
        cols = st.columns(7, gap='small')
        for i, day in enumerate(week):
            with cols[i]:
                if not day:
                    st.write(' ')
                    continue
                key = date(first.year,first.month,day).isoformat()
                hours_today = sum(r['hours'] for r in by_day.get(key, []))
                due_count = len(due_by_day.get(key, []))
                suffix = (' ⭐' if key == date.today().isoformat() else '')
                if hours_today:
                    suffix += f' 📗{hours_today:g}h'
                if due_count:
                    suffix += f' 🔔{due_count}'
                if st.button(f'{day}{suffix}', key=f'cal_{key}', use_container_width=True,
                    type='primary' if st.session_state.get('selected_day') == key else 'secondary'):
                    st.session_state.selected_day = key
                    st.rerun()
    chosen = st.session_state.get('selected_day', date.today().isoformat())
    selected = date.fromisoformat(chosen)
    st.markdown(f'#### 📖 รายละเอียดวันที่ {selected.strftime("%d/%m/%Y")}')
    rows = by_day.get(chosen, [])
    dues = due_by_day.get(chosen, [])
    if not rows and not dues:
        st.info('วันนี้ไม่มีแผนอ่านหรือกำหนดส่ง')
    for row in rows:
        st.markdown(f"📗 **{html.escape(row['subject'])} — {html.escape(row['name'])}** · {row['hours']:g} ชม." + (' · ⚠️ หลังวันส่ง' if row['late'] else ''))
    for task in dues:
        st.markdown(f"🔔 กำหนดส่ง **{html.escape(task['subject'])} — {html.escape(task['name'])}**" + (' · ✅ เสร็จแล้ว' if task['done'] else ''))
    if rows or dues:
        unique_ids = list(dict.fromkeys([r['id'] for r in rows]+[t['id'] for t in dues]))
        with st.expander('🔎 เปิดรายละเอียดและทำเครื่องหมายงาน', expanded=False):
            for task in tasks:
                if task['id'] in unique_ids:
                    render_task(task, f'calendar_{chosen}')
    st.button('🏠 ไปจัดการงานบนหน้าหลัก', type='primary', on_click=go_to_home)
    if any(r['late'] for r in schedule):
        st.warning('มีบางช่วงถูกจัดหลังวันกำหนดส่ง ลองเพิ่มเวลาว่างต่อวัน')
    if unscheduled:
        st.warning(f'มีชั่วโมงที่ยังจัดไม่ครบ {unscheduled:g} ชม. ใน 60 วัน')
    with st.expander('📋 ตารางอ่านแบบรายการ'):
        if schedule:
            st.dataframe(pd.DataFrame([{'วันที่':r['date'],'วิชา':r['subject'], 'งาน':r['name'],
                'ชั่วโมง':r['hours'],'กำหนดส่ง':r['due']} for r in schedule]), hide_index=True, use_container_width=True)
        else:
            st.info('ยังไม่มีงานที่ต้องจัดตาราง')
        st.caption('ตารางเป็นคำแนะนำ ไม่ใช่บันทึกเวลาอ่านจริง')
