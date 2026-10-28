"""Smart Study Planner: priorities, study logs, multi-day calendar and backup."""
import calendar
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
    st.session_state.theme_mode = False

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
    [data-testid='stAppViewContainer'] .stMarkdown p,[data-testid='stAppViewContainer'] .stMarkdown li {{color:{text};}}
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
    /* ให้ข้อความในปุ่มและส่วนโต้ตอบมี contrast ตามโหมด */
    [data-testid='stAppViewContainer'] button[kind='secondary'] *,
    [data-testid='stAppViewContainer'] button[kind='secondary'] p,
    [data-testid='stAppViewContainer'] button[kind='secondary'] span {{color:{text} !important;}}
    [data-testid='stAppViewContainer'] button[kind='primary'] *,
    [data-testid='stAppViewContainer'] button[kind='primary'] p,
    [data-testid='stAppViewContainer'] button[kind='primary'] span {{color:#17343A !important;}}
    /* Expander: แถบหัวข้อไม่ควรเป็นสีขาวในโหมดมืด */
    [data-testid='stExpander'] details,
    [data-testid='stExpander'] details > summary,
    [data-testid='stExpander'] [data-testid='stExpanderDetails'] {{background:{panel} !important;color:{text} !important;}}
    [data-testid='stExpander'] summary *,
    [data-testid='stExpander'] summary p,
    [data-testid='stExpander'] summary svg {{color:{text} !important;fill:currentColor;}}
    /* ปุ่ม popover และกล่องที่เปิดขึ้นมา */
    [data-testid='stPopover'] > button {{background:{panel} !important;color:{text} !important;border:1px solid {line} !important;}}
    [data-testid='stPopover'] > button * {{color:{text} !important;}}
    [data-testid='stPopoverBody'],[data-testid='stPopoverBody'] > div,
    [data-baseweb='popover'] [data-baseweb='popover-content'],
    [data-baseweb='popover'] [data-baseweb='popover-content'] > div {{background:{panel} !important;color:{text} !important;}}
    [data-testid='stPopoverBody'] p,[data-testid='stPopoverBody'] label,
    [data-testid='stPopoverBody'] span {{color:{text} !important;}}
    /* Fix: ปุ่มบันทึกเวลาอ่านและปุ่ม popover มองเห็นชัดในโหมดมืดและสว่าง */
    [data-testid='stPopover'] button,
    [data-testid='stPopover'] button[kind],
    [data-testid='stPopover'] [data-baseweb='button'],
    [data-testid='stPopover'] [data-baseweb='popover'] button {{
        background-color:{panel} !important;
        color:{text} !important;
        border:1.5px solid {line} !important;
        opacity:1 !important;
        -webkit-text-fill-color:{text} !important;
    }}
    [data-testid='stPopover'] button *,
    [data-testid='stPopover'] button p,
    [data-testid='stPopover'] button span,
    [data-testid='stPopover'] button svg,
    [data-testid='stPopover'] [data-baseweb='button'] * {{
        color:{text} !important;
        fill:currentColor;
        -webkit-text-fill-color:{text} !important;
        opacity:1 !important;
    }}
    [data-testid='stPopover'] button:hover,
    [data-testid='stPopover'] [data-baseweb='button']:hover {{
        background-color:{hover} !important;
        border-color:#4ECDC4 !important;
    }}
    /* กรณี Streamlit ใช้ popover container class ในเวอร์ชันใหม่ */
    div[class*='stPopover'] button,
    div[class*='stPopover'] button * {{color:{text} !important;-webkit-text-fill-color:{text} !important;}}
    div[class*='stPopover'] button {{background:{panel} !important;border-color:{line} !important;}}
    /* ตัวเลือก ตัวกรอกข้อมูล และปุ่มลบที่ยังไม่ได้กด */
    [data-baseweb='input'] > div,[data-baseweb='select'] > div,
    [data-baseweb='textarea'] > div {{background:{panel} !important;color:{text} !important;border-color:{line} !important;}}
    [data-baseweb='input'] input,[data-baseweb='textarea'] textarea {{color:{text} !important;}}
    [data-testid='stCheckbox'] label span {{color:{text} !important;}}
    [data-testid='stCaptionContainer'] p {{color:{muted} !important;}}
    /* ป้าย 'แสดงรายการ' และตัวเลือก ทั้งหมด/ยังไม่เสร็จ/เสร็จแล้ว ในโหมดมืด */
    [data-testid='stSegmentedControl'] label,
    [data-testid='stSegmentedControl'] > div > label,
    [data-testid='stSegmentedControl'] p,
    [data-testid='stSegmentedControl'] span,
    [data-testid='stSegmentedControl'] button,
    [data-testid='stSegmentedControl'] button * {{color:{text} !important;}}
    [data-testid='stSegmentedControl'] button,
    [data-testid='stSegmentedControl'] [role='radiogroup'] label {{background:{panel} !important;border-color:{line} !important;}}
    [data-testid='stSegmentedControl'] button[aria-pressed='true'],
    [data-testid='stSegmentedControl'] [role='radio'][aria-checked='true'],
    [data-testid='stSegmentedControl'] [data-checked='true'] {{background:#4ECDC4 !important;color:#17343A !important;}}
    [data-testid='stSegmentedControl'] button[aria-pressed='true'] *,
    [data-testid='stSegmentedControl'] [role='radio'][aria-checked='true'] *,
    [data-testid='stSegmentedControl'] [data-checked='true'] * {{color:#17343A !important;}}
    /* ตัวหนังสือในป้ายของ widget ต้องไม่มืดกลืนพื้นหลัง */
    [data-testid='stWidgetLabel'] p {{color:{text} !important;}}
    [data-testid='stSegmentedControl'] [data-baseweb='button-group'] {{background:{panel} !important;border:1px solid {line} !important;border-radius:12px;}}
    [data-testid='stSegmentedControl'] button:hover {{background:{hover} !important;}}
    /* ไม่บังคับให้ตัวหนังสือสีเดียวกับพื้นหลังในกล่องแจ้งเตือน */
    [data-testid='stAlert'] p {{color:inherit !important;}}
    .study-progress-track {{height:13px;width:100%;background:#D5EFEB;border-radius:99px;overflow:hidden;margin:11px 0 5px;}}
    .study-progress-fill {{height:100%;background:#167C74;border-radius:99px 0 0 99px;transition:width .3s ease;}}
    .study-progress-legend {{display:flex;gap:16px;flex-wrap:wrap;color:{muted};font-size:.81rem;margin:5px 0 8px;}}
    .study-progress-legend b {{color:{text};}}
    .study-progress-dot {{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:middle;}}

    div[class*='st-key-home_done_'] button, div[class*='st-key-calendar_done_'] button, div[class*='st-key-focus_'] button {{background:#20A67A!important;color:white!important;border-color:#168963!important;}}
    div[class*='st-key-home_done_'] button:hover, div[class*='st-key-calendar_done_'] button:hover {{background:#168963!important;}}
    div[class*='st-key-home_del_'] button, div[class*='st-key-calendar_del_'] button {{background:#FF6B6B!important;color:white!important;border-color:#FF6B6B!important;}}
    div[class*='st-key-home_del_'] button:hover, div[class*='st-key-calendar_del_'] button:hover {{background:#DE4C4C!important;}}
    div[data-testid='stButton'] button:focus-visible {{outline:3px solid #F3AF50!important;outline-offset:2px;}}
    div[class*='st-key-new_task_launcher'] button {{min-height:64px!important;font-size:1.16rem!important;background:#4ECDC4!important;color:#17343A!important;border:2px solid #2ABDB2!important;box-shadow:0 8px 18px #4ECDC444!important;}}
    div[class*='st-key-new_task_launcher'] button:hover {{background:#F3AF50!important;border-color:#E89D33!important;}}
    .weekday-name {{display:block;text-align:center;padding:9px 2px;border-radius:12px;font-weight:800;font-size:clamp(11px,1.25vw,16px);letter-spacing:.01em;}}
    .study-task-title {{font-size:1.08rem;font-weight:700;color:{text};background:{hover};border-left:5px solid #F3AF50;padding:10px 14px;border-radius:9px;margin-bottom:5px;}}
    .study-progress-label {{font-size:.84rem;color:{muted};margin-top:5px;}}
    
    .hero-panel {{display:none;}}

    .dream-banner .quote-slide {{position:absolute;top:0;left:0;right:0;box-sizing:border-box;padding:25px 30px;opacity:0;visibility:hidden;animation:quote-cycle 40s linear infinite;z-index:2;width:75%;pointer-events:none;}}
    @keyframes quote-cycle {{0%,19.5% {{opacity:1;visibility:visible;transform:translateY(0)}} 20%,99.9% {{opacity:0;visibility:hidden;transform:translateY(-7px)}} 100% {{opacity:1;visibility:visible;transform:translateY(0)}}}}
    .dream-banner:hover .quote-slide {{animation-play-state:paused;}}
    .dream-banner .quote-slide strong {{color:#4ECDC4;font-family:'Mali','Prompt',sans-serif;font-size:clamp(1.05rem,2vw,1.4rem);line-height:1.55;display:block;}}
    .dream-banner .quote-slide p {{margin:8px 0 0;color:#F6F9F7 !important;line-height:1.65;font-size:clamp(.77rem,1.15vw,.92rem);}}
    /* Banner เคลื่อนไหวแบบเบา ๆ โดยไม่ต้องโหลดวิดีโอ */
    .dream-banner {{height:165px;position:relative;overflow:hidden;border-radius:22px;margin:12px 0 22px;background:radial-gradient(circle at 80% 30%,#315A66 0%,#292F36 53%,#172329 100%);border:1px solid #4ECDC480;box-shadow:0 10px 26px #12242A24;}}
    .dream-banner .orb {{position:absolute;border-radius:50%;border:1px solid #4ECDC475;width:205px;height:205px;right:11%;top:-43px;animation:orbit-float 12s ease-in-out infinite alternate;}}
    .dream-banner .orb::before {{content:'';position:absolute;width:25px;height:25px;background:#F3AF50;border-radius:50%;top:28px;left:23px;box-shadow:0 0 24px #F3AF5099;}}
    .dream-banner .orb.two {{width:115px;height:115px;right:18%;top:14px;border-color:#FF6B6B99;animation-duration:9s;animation-direction:alternate-reverse;}}
    .dream-banner .orb.two::before {{background:#FF6B6B;width:12px;height:12px;top:8px;left:12px;}}
    .dream-banner .stars {{position:absolute;right:4%;top:17px;font-size:26px;letter-spacing:14px;color:#F3AF50;animation:star-shine 4s ease-in-out infinite alternate;}}
    .dream-banner .banner-copy {{display:none;}}
    .dream-banner .banner-kicker {{color:#4ECDC4;font-weight:700;font-size:12px;letter-spacing:3px;}}
    .dream-banner .banner-title {{color:#FFFFFF;font-size:clamp(19px,2.7vw,31px);font-weight:700;line-height:1.45;margin-top:8px;}}
    .dream-banner .banner-sub {{color:#DDEBE9;font-size:12px;margin-top:7px;}}
    @keyframes orbit-float {{from {{transform:translateY(-7px) rotate(-12deg)}}to {{transform:translateY(12px) rotate(20deg)}}}}
    @keyframes star-shine {{from {{opacity:.3;transform:translateY(5px)}}to {{opacity:1;transform:translateY(-5px)}}}}
    /* ปฏิทิน: วันแต่ละช่องขยับเล็กน้อยเมื่อชี้ ไม่เปลี่ยนความหมายของสี */
    div[class*='st-key-cal_'] button {{min-height:61px!important;border-radius:14px!important;border:1px solid {line}!important;background:{panel}!important;color:{text}!important;transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease!important;}}
    div[class*='st-key-cal_'] button:hover {{transform:translateY(-3px)!important;border-color:#4ECDC4!important;box-shadow:0 6px 15px #4ECDC433!important;}}
    div[class*='st-key-cal_'] button[kind='primary'] {{background:#4ECDC4!important;color:#17343A!important;border-color:#36BDB3!important;font-weight:700!important;}}
    /* วันนี้: ขอบสีส้มทองแม้ยังไม่ได้เลือก; วันที่เลือก: สีมิ้นต์ */
    div[class*='st-key-cal_'][class*='-today'] button {{border:3px solid #F3AF50!important;box-shadow:0 0 0 2px #F3AF5040!important;}}
    div[class*='st-key-cal_'][class*='-today'] button:hover {{border-color:#F3AF50!important;}}
    div[class*='st-key-cal_'][class*='-today'] button[kind='primary'] {{background:#4ECDC4!important;border:3px solid #F3AF50!important;}}
    .calendar-legend {{display:flex;gap:9px;flex-wrap:wrap;margin:8px 0 14px;}}
    .calendar-pill {{font-size:12px;font-weight:600;padding:6px 11px;border-radius:999px;background:{panel};color:{text};border:1px solid {line};}}
    .calendar-pill.study {{border-color:#4ECDC4;}} .calendar-pill.due {{border-color:#F3AF50;}} .calendar-pill.today {{border-color:#FF6B6B;}}
    .calendar-summary {{padding:14px 18px;border-radius:14px;background:{hover};border-left:4px solid #4ECDC4;margin:12px 0;}}
    @media (max-width:640px) {{.dream-banner .quote-slide {{width:95%;padding:20px 16px;}} .dream-banner {{height:146px;}} .dream-banner .banner-copy {{max-width:90%;padding:22px 18px;}} .dream-banner .orb {{right:-60px;opacity:.5;}} div[class*='st-key-cal_'] button {{min-height:54px!important;font-size:11px!important;padding:4px!important;}}}}
    .stAlert {{border-radius:13px;}}
    @media (prefers-reduced-motion:reduce) {{.dream-banner .orb,.dream-banner .stars {{animation:none!important;}} div[class*="st-key-cal_"] button {{transition:none!important;}} .quote-slide {{animation:none;opacity:0;}} .quote-slide:first-child {{opacity:1;}}h1,h2,h3,div.stButton > button,div.stFormSubmitButton > button {{transition:none!important;transform:none!important;}}}}

    /* สำรองข้อมูล: ปุ่มดาวน์โหลดและช่องอัปโหลดอ่านชัดทั้งสองโหมด */
    [data-testid='stDownloadButton'] button {{background:{panel} !important;color:{text} !important;border:1.5px solid #4ECDC4 !important;}}
    [data-testid='stDownloadButton'] button *,[data-testid='stDownloadButton'] button p {{color:{text} !important;-webkit-text-fill-color:{text} !important;}}
    [data-testid='stDownloadButton'] button:hover {{background:{hover} !important;}}
    [data-testid='stFileUploader'] [data-testid='stFileUploaderDropzone'] {{background:{panel} !important;border:1.5px dashed {line} !important;}}
    [data-testid='stFileUploader'] [data-testid='stFileUploaderDropzone'] *,
    [data-testid='stFileUploader'] [data-testid='stFileUploaderDropzone'] p,
    [data-testid='stFileUploader'] [data-testid='stFileUploaderDropzone'] span {{color:{text} !important;-webkit-text-fill-color:{text} !important;}}
    [data-testid='stFileUploader'] button {{background:{hover} !important;color:{text} !important;border:1px solid {line} !important;opacity:1 !important;}}
    [data-testid='stFileUploader'] button * {{color:{text} !important;-webkit-text-fill-color:{text} !important;}}
    [data-testid='stFileUploader'] label p {{color:{text} !important;}}
    /* สรุปงาน: ตัวเลขใหญ่ อ่านได้ทันทีทั้งสองโหมด */
    div[class*='st-key-stat_'] button {{min-height:112px!important;padding:14px 8px!important;border-radius:18px!important;}}
    div[class*='st-key-stat_'] button p {{white-space:pre-line!important;font-size:1.05rem!important;line-height:1.65!important;font-weight:700!important;text-align:center!important;}}
    div[class*='st-key-stat_'] button p::first-line {{font-size:2.05rem!important;font-weight:800!important;}}
    div[class*='st-key-stat_'] button:hover {{transform:translateY(-2px);box-shadow:0 7px 17px #4ECDC43A!important;}}
    @media (max-width:640px) {{div[class*='st-key-stat_'] button {{min-height:96px!important;}} div[class*='st-key-stat_'] button p {{font-size:.85rem!important;}} div[class*='st-key-stat_'] button p::first-line {{font-size:1.6rem!important;}}}}
    /* Dashboard cards: responsive, legible in both themes */
    .dashboard-intro {{padding:16px 20px;margin:10px 0 16px;border-radius:18px;background:linear-gradient(110deg,#24465D,#326C7A);border:1px solid #4ECDC477;box-shadow:0 7px 20px #102A3520;}}
    .dashboard-intro strong {{display:block;color:#FFFFFF;font-size:1.24rem;}}
    .dashboard-intro span {{display:block;color:#E2F5F2;font-size:.88rem;margin-top:5px;}}
    .dashboard-card {{background:{panel};border:1px solid {line};border-radius:18px;padding:16px 18px;margin:5px 0 12px;box-shadow:0 5px 17px #102A3510;}}
    .dashboard-card-heading {{font-weight:700;font-size:1.05rem;color:{text};margin-bottom:9px;}}
    .dashboard-card-note {{color:{muted};font-size:.82rem;margin-top:9px;}}
    .dashboard-progress-track {{height:13px;border-radius:999px;background:{line};overflow:hidden;}}
    .dashboard-progress-fill {{height:100%;border-radius:999px;background:linear-gradient(90deg,#4ECDC4,#67B7F7);}}
    .dashboard-chart-note {{color:{muted};font-size:.82rem;}}
    div[class*='st-key-stat_'] button {{border:1px solid {line}!important;box-shadow:0 5px 15px #102A3512!important;}}
    div[class*='st-key-stat_'] button:hover {{border-color:#4ECDC4!important;box-shadow:0 8px 19px #4ECDC433!important;}}
    @media(max-width:640px) {{.dashboard-intro {{padding:14px 15px;}}.dashboard-card {{padding:13px 14px;}}}}
    .deadline-banner {{background:linear-gradient(115deg,#FFF0DB,#FFE1DD);border:2px solid #F3AF50;border-left:7px solid #FF6B6B;border-radius:17px;padding:16px 20px;display:flex;align-items:center;gap:14px;margin:18px 0 10px;color:#292F36;box-shadow:0 5px 16px #F3AF5026;}}
    .deadline-banner strong {{display:block;font-size:1.12rem;color:#292F36 !important;}}
    .deadline-banner span {{display:block;font-size:.86rem;color:#674D44 !important;margin-top:3px;}}
    .deadline-bell {{font-size:1.65rem;}}
    /* Shared branded masthead across all pages; independent of task data. */
    .ssp-brand {{position:relative;isolation:isolate;overflow:hidden;display:flex;align-items:center;gap:19px;padding:24px 27px;margin:6px 0 13px;border-radius:23px;background:linear-gradient(115deg,#153E63 0%,#226E8A 52%,#3DB6B0 100%);box-shadow:0 12px 28px #164D6B30;border:1px solid #92E9E180;}}
    .ssp-brand:before {{content:'';position:absolute;z-index:-1;right:-52px;top:-105px;width:260px;height:260px;border:2px solid #FFFFFF26;border-radius:50%;box-shadow:0 0 0 38px #FFFFFF0C,0 0 0 82px #FFFFFF09;}}
    .ssp-brand-mark {{width:63px;height:63px;flex:0 0 63px;border-radius:20px;display:grid;place-items:center;background:#FFFFFF25;border:1px solid #FFFFFF70;font-size:31px;box-shadow:0 5px 14px #082D3C25;animation:ssp-float 4s ease-in-out infinite;}}
    .ssp-brand-copy {{min-width:0;}}
    .ssp-brand-kicker {{color:#C5FFF1!important;font-size:.72rem;letter-spacing:.14em;font-weight:700;}}
    .ssp-brand-name {{margin:2px 0 5px!important;color:#FFFFFF!important;font-family:'Prompt',sans-serif;font-size:clamp(1.5rem,3.2vw,2.6rem);line-height:1.23;font-weight:800;letter-spacing:-.035em;text-shadow:0 3px 10px #0A354B33;}}
    .ssp-brand-sub {{color:#ECFFFC!important;font-size:clamp(.73rem,1.3vw,.91rem);line-height:1.6;}}
    .ssp-brand-spark {{position:absolute;right:25px;bottom:14px;color:#FFF3AD;font-size:25px;animation:ssp-twinkle 3s ease-in-out infinite;}}
    @keyframes ssp-float {{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-4px)}}}}
    @keyframes ssp-twinkle {{0%,100%{{opacity:.5;transform:scale(.88)}}50%{{opacity:1;transform:scale(1.13)}}}}
    @media(max-width:640px) {{.ssp-brand{{padding:17px 16px;gap:12px;border-radius:17px;}}.ssp-brand-mark{{width:46px;height:46px;flex-basis:46px;font-size:23px;border-radius:14px;}}.ssp-brand-spark{{right:10px;bottom:7px;font-size:17px;}}}}
    @media(prefers-reduced-motion:reduce) {{.ssp-brand-mark,.ssp-brand-spark{{animation:none!important;}}}}
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


SUBJECT_ICONS = {
    '📖 หนังสือ': '📖', '💻 คอมพิวเตอร์': '💻',
    '🧮 คณิตศาสตร์': '🧮', '🔬 วิทยาศาสตร์': '🔬',
    '🎨 ศิลปะ': '🎨',
}

def icon_for_subject(subject, tasks):
    for task in reversed(tasks):
        if task['subject'] == subject and task.get('subject_icon') in SUBJECT_ICONS.values():
            return task['subject_icon']
    lower = subject.casefold()
    if 'python' in lower or 'โปรแกรม' in lower or 'เทคโนโลยี' in lower:
        return '💻'
    if 'คณิต' in lower:
        return '🧮'
    if 'วิทยา' in lower:
        return '🔬'
    if 'ออกแบบ' in lower or 'ศิลป' in lower:
        return '🎨'
    return '📖'


def readable_time(hours):
    total = int(round(float(hours) * 60))
    h, m = divmod(total, 60)
    if h and m:
        return f'{h} ชม. {m} นาที'
    if h:
        return f'{h} ชม.'
    return f'{m} นาที'


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
        t.pop('image_b64', None)  # เลิกเก็บรูปในข้อมูลใหม่ แต่รองรับไฟล์สำรองเก่า
        t['subject_icon'] = str(t.get('subject_icon', ''))
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
    """เพิ่มชุดงานเริ่มต้น 30 รายการโดยไม่ลบงานเดิมและไม่สร้างซ้ำ."""
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
            done = False
            generated.append({
                'id': next_id, 'subject': subject, 'name': name,
                'due': (today + timedelta(days=offset)).isoformat(),
                'difficulty': difficulty, 'hours': hours, 'studied': 0.0,
                'done': done, 'logs': [], 'demo_key': key, 'subject_icon': '',
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
            alerts.append(('error', task, f"เลยกำหนด {abs(days)} วัน"))
        elif days == 0:
            alerts.append(('error', task, 'ครบกำหนดวันนี้'))
        elif days <= 3:
            alerts.append(('warning', task, f'เหลือ {days} วัน'))
    return sorted(alerts, key=lambda a: a[1]['due'])



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


def render_task(task, prefix, rank=None):
    """การ์ดงานพร้อมลำดับ ปุ่มสถานะ และการยืนยันก่อนลบ."""
    with st.container(border=True):
        left, right = st.columns([4, 1.35], vertical_alignment='center')
        with left:
            rank_label = f'{rank}. ' if rank is not None else ''
            title = f"{rank_label}{html.escape(task['name'])}"
            st.markdown(f'<div class="study-task-title">{title}</div>', unsafe_allow_html=True)
            st.caption(f"ส่ง {task['due']} · เหลือ {readable_time(remaining_hours(task))} จาก {readable_time(task['hours'])} · {priority_label(priority_score(task))}")
        with right:
            label = '↩️ ยังไม่เสร็จ (เปิดใหม่)' if task['done'] else '✓ เสร็จแล้ว'
            if st.button(label, key=f'{prefix}_done_{task["id"]}', type='secondary' if task['done'] else 'primary', use_container_width=True):
                toggle_done(task['id'])
        pct = 1.0 if task['done'] else min(1.0, max(0.0, float(task['studied']) / max(float(task['hours']), 0.01)))
        read_time = readable_time(task['hours'] if task['done'] else task['studied'])
        left_time = readable_time(0 if task['done'] else remaining_hours(task))
        st.markdown(
            f'<div class="study-progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{pct*100:.0f}" aria-label="ความคืบหน้าการอ่าน">'
            f'<div class="study-progress-fill" style="width:{pct*100:.2f}%"></div></div>'
            f'<div class="study-progress-legend">'
            f'<span><i class="study-progress-dot" style="background:#167C74"></i><b>{"งานเสร็จแล้ว (100%)" if task["done"] else f"อ่านแล้ว {read_time} ({pct:.0%})"}</b></span>'
            f'<span><i class="study-progress-dot" style="background:#D5EFEB;border:1px solid #9ACFC7"></i>เหลือ {left_time}</span>'
            f'</div>', unsafe_allow_html=True
        )
        tools, delete_col = st.columns([3.8, 1.2], vertical_alignment='bottom')
        with tools:
            if not task['done']:
                with st.popover('⏱️ บันทึกเวลาอ่าน'):
                    if remaining_hours(task) > 0:
                        with st.form(f'{prefix}_log_{task["id"]}'):
                            col_h, col_m = st.columns(2)
                            with col_h:
                                add_h = st.number_input('ชั่วโมง', min_value=0, max_value=100, value=0, step=1, key=f'{prefix}_add_h_{task["id"]}')
                            with col_m:
                                add_m = st.number_input('นาที', min_value=0, max_value=59, value=30, step=5, key=f'{prefix}_add_m_{task["id"]}')
                            if st.form_submit_button('บันทึกเวลาอ่าน', type='primary'):
                                total_minutes = add_h * 60 + add_m
                                available_minutes = int(round(remaining_hours(task) * 60))
                                if total_minutes <= 0:
                                    st.warning('กรุณาระบุเวลาอย่างน้อย 1 นาที')
                                elif total_minutes > available_minutes:
                                    st.warning(f'เหลือเวลาอ่านเพียง {readable_time(remaining_hours(task))} กรุณาระบุไม่เกินเวลาที่เหลือ')
                                else:
                                    updated = [dict(t) for t in st.session_state.tasks]
                                    selected = next(t for t in updated if t['id'] == task['id'])
                                    actual = round(total_minutes / 60, 6)
                                    selected['studied'] = min(selected['hours'], round(selected['studied'] + actual, 6))
                                    selected['logs'] = [*selected.get('logs', []), {'date': date.today().isoformat(), 'hours': actual}]
                                    if remaining_hours(selected) < 1/120:
                                        selected['studied'] = selected['hours']
                                        selected['done'] = True
                                    commit(updated, 'บันทึกเวลาอ่านเรียบร้อย')
        with delete_col:
            with st.popover('🗑️ ลบงาน'):
                st.warning(f"ยืนยันลบงาน “{task['name']}” หรือไม่? การลบจะนำงานและประวัติการอ่านออกด้วย")
                confirm = st.checkbox('ฉันยืนยันว่าต้องการลบ', key=f'{prefix}_confirm_{task["id"]}')
                if st.button('ยืนยันลบถาวร', key=f'{prefix}_del_{task["id"]}', disabled=not confirm, use_container_width=True):
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
        # ลำดับงานเริ่มที่ 1 ใหม่ทุกวิชา ไม่ใช้ลำดับรวมทั้งเว็บไซต์
        ordered = sorted(subject_tasks, key=lambda t: (t['done'], -priority_score(t), t['due'], t['id']))
        with st.expander(f'{icon_for_subject(subject, st.session_state.tasks)} {subject}  ·  {done}/{len(subject_tasks)} งานเสร็จ', expanded=len(groups) == 1):
            for subject_rank, task in enumerate(ordered, start=1):
                render_task(task, prefix, subject_rank)


def go_to_calendar(task_id=None, due=None):
    # ต้องทำผ่าน callback ก่อนที่ radio widget จะถูกสร้างในรอบถัดไป
    st.session_state.navigation = '📅 ปฏิทิน'
    if due is not None:
        st.session_state.selected_day = due
        st.session_state.cal_month = date.fromisoformat(due).replace(day=1)
        st.session_state.calendar_target_task = task_id


def go_to_home():
    st.session_state.navigation = '🏠 หน้าหลัก'


if 'tasks' not in st.session_state:
    st.session_state.tasks = load_tasks()
tasks = st.session_state.tasks
if 'navigation' not in st.session_state:
    st.session_state.navigation = '🏠 หน้าหลัก'

header_left, header_right = st.columns([5, 1], vertical_alignment='center')
with header_right:
    st.toggle('🌙 โหมดมืด', key='theme_mode', help='เลื่อนสวิตช์เพื่อเปลี่ยนโหมดสว่างหรือมืด')
st.markdown(theme_styles(st.session_state.theme_mode), unsafe_allow_html=True)
with header_left:
    st.markdown('''
    <header class="ssp-brand" aria-label="Smart Study Planner">
      <div class="ssp-brand-mark" aria-hidden="true">📚</div>
      <div class="ssp-brand-copy">
        <div class="ssp-brand-kicker">✦ YOUR STUDY COMPANION</div>
        <h1 class="ssp-brand-name">Smart Study Planner</h1>
        <div class="ssp-brand-sub">วางแผนการเรียน · ติดตามความคืบหน้า · จัดงานตามรายวิชา</div>
      </div>
      <span class="ssp-brand-spark" aria-hidden="true">✦</span>
    </header>
    ''', unsafe_allow_html=True)
st.info('🧪 เว็บไซต์นี้เป็นระบบทดลองเพื่อการศึกษา ยังไม่พัฒนาสำหรับใช้งานจริง ข้อมูลที่บันทึกอาจสูญหายเมื่อระบบรีสตาร์ต และผู้ใช้เว็บไซต์เดียวกันอาจเห็นข้อมูลร่วมกัน กรุณาอย่าใส่ข้อมูลส่วนตัวหรือข้อมูลสำคัญ')
page = st.sidebar.radio('เมนู', ['🏠 หน้าหลัก', '📅 ปฏิทิน', '📘 คู่มือใช้งาน'], key='navigation')
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
    quote_order = [(st.session_state.quote_index + i) % len(QUOTES) for i in range(5)]
    slides = ''.join(f'<div class="quote-slide" style="animation-delay:{j*8}s"><strong>✧ {html.escape(QUOTES[i][0])}</strong><p>{html.escape(QUOTES[i][1])}</p></div>' for j, i in enumerate(quote_order))
    st.markdown(
        '<div class="dream-banner" aria-label="คำคมการเรียนรู้เคลื่อนไหว">'
        '<div class="orb"></div><div class="orb two"></div>'
        '<div class="stars">✦ ✧ ✦</div>' + slides + '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dashboard-intro"><strong>✦ แดชบอร์ดการเรียนของฉัน</strong>'
        '<span>ติดตามงาน ความคืบหน้า และแผนการอ่านได้ในหน้าเดียว</span></div>',
        unsafe_allow_html=True,
    )
    completed = sum(t['done'] for t in tasks)
    pending = [t for t in tasks if not t['done']]
    # คลิกการ์ดแล้วรายการที่กรองจะแสดงใต้การ์ดทันที (ไม่ต้องเลื่อนหาด้านล่าง)
    if 'task_filter' not in st.session_state:
        st.session_state.task_filter = 'ทั้งหมด'
    a,b,c = st.columns(3)
    with a:
        if st.button(f'{len(tasks)}\n📚 งานทั้งหมด', key='stat_all',
                     use_container_width=True, type='primary' if st.session_state.task_filter == 'ทั้งหมด' else 'secondary'):
            st.session_state.task_filter = 'ทั้งหมด'
            st.rerun()
    with b:
        if st.button(f'{completed}\n✅ เสร็จแล้ว', key='stat_done',
                     use_container_width=True, type='primary' if st.session_state.task_filter == 'เสร็จแล้ว' else 'secondary'):
            st.session_state.task_filter = 'เสร็จแล้ว'
            st.rerun()
    with c:
        if st.button(f'{len(pending)}\n🕒 รอดำเนินการ', key='stat_pending',
                     use_container_width=True, type='primary' if st.session_state.task_filter == 'ยังไม่เสร็จ' else 'secondary'):
            st.session_state.task_filter = 'ยังไม่เสร็จ'
            st.rerun()
    completion_pct = (completed / len(tasks) * 100) if tasks else 0
    st.markdown(
        '<div class="dashboard-card">'
        '<div style="display:flex;justify-content:space-between;gap:12px;align-items:center">'
        '<div class="dashboard-card-heading">📈 ความคืบหน้าการเรียน</div>'
        f'<strong style="color:#36B9AA;font-size:1.12rem">{completion_pct:.0f}%</strong></div>'
        '<div class="dashboard-progress-track" role="progressbar" aria-label="สัดส่วนงานที่เสร็จแล้ว" '
        f'aria-valuenow="{completion_pct:.0f}" aria-valuemin="0" aria-valuemax="100">'
        f'<div class="dashboard-progress-fill" style="width:{completion_pct:.2f}%"></div></div>'
        f'<div class="dashboard-card-note">ทำเสร็จแล้ว {completed} จาก {len(tasks)} งาน · คำนวณจากสถานะงานจริง</div>'
        '</div>', unsafe_allow_html=True,
    )
    st.caption('เลือกการ์ดเพื่อแสดงรายการที่ตรงกับสถานะด้านล่างทันที')
    # ตำแหน่งแสดงผลของรายการ: เติมเนื้อหาภายหลัง แต่แสดงใกล้การ์ดสรุป
    filtered_list_area = st.container()

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
        overdue_count = sum(level == 'error' for level, _, _ in alerts)
        st.markdown(
            f'<div class="deadline-banner"><div class="deadline-bell">🔔</div>'
            f'<div><strong>งานที่ต้องติดตาม {len(alerts)} รายการ</strong>'
            f'<span>ใกล้กำหนดส่งและเลยกำหนด'
            f'{f" · เลยกำหนด {overdue_count} งาน" if overdue_count else ""}</span></div></div>',
            unsafe_allow_html=True
        )
        with st.expander('📋 เปิดดูงานเร่งด่วนและรายละเอียด', expanded=True):
            st.caption('กดปุ่ม “ดูงานในปฏิทิน” เพื่อเปิดวันที่และรายละเอียดงานนั้น')
            for level, alert_task, message in alerts:
                c1, c2 = st.columns([5, 1], vertical_alignment='center')
                with c1:
                    (st.error if level == 'error' else st.warning)(f"{icon_for_subject(alert_task['subject'], tasks)} {alert_task['subject']} — {alert_task['name']}: {message}")
                with c2:
                    st.button('ดูงานในปฏิทิน', key=f'alert_open_{alert_task["id"]}',
                              use_container_width=True, on_click=go_to_calendar,
                              args=(alert_task['id'], alert_task['due']))
            selected_alert = next((t for t in tasks if t['id'] == st.session_state.get('alert_selected') and not t['done']), None)
            if selected_alert:
                st.markdown('#### 🔎 รายละเอียดงานที่เลือก')
                st.caption(selected_alert['subject'])
                render_task(selected_alert, 'alert')

    st.subheader('🎯 Today Focus · งานที่ควรทำวันนี้')
    st.caption('ระบบให้ความสำคัญกับวันกำหนดส่งก่อน แล้วจึงพิจารณาความยากและเวลาที่ต้องใช้')
    daily_hours = st.session_state.get('daily_hours', 2.0)
    schedule, _ = build_schedule(tasks, daily_hours, today)
    focus = [r for r in schedule if r['date'] == today.isoformat()]
    if focus:
        for row in focus[:3]:
            task = next(t for t in tasks if t['id'] == row['id'])
            with st.container(border=True):
                col1,col2 = st.columns([4,1], vertical_alignment='center')
                with col1:
                    st.markdown(f"**{icon_for_subject(task['subject'], tasks)} {html.escape(task['subject'])} — {html.escape(task['name'])}**")
                    st.caption(f"แนะนำวันนี้ {readable_time(row['hours'])} · กำหนดส่ง {task['due']}")
                with col2:
                    if st.button('✓ เสร็จแล้ว', key=f'focus_{task["id"]}', type='primary', use_container_width=True):
                        toggle_done(task['id'])
        st.caption('บันทึกเวลาอ่านบางส่วนได้ที่หัวข้อรายวิชาด้านล่าง')
    else:
        st.success('วันนี้ไม่มีงานค้างตามแผน')

    # แยกสรุปเวลาอ่านจริงออกจากรายการรายวิชาอย่างชัดเจน
    st.markdown('### 📈 ภาพรวมการอ่านของฉัน')
    with st.container(border=True):
        st.markdown('**📈 กราฟเวลาอ่านจริงใน 7 วันล่าสุด**')
        progress_rows = week_progress(tasks, today)
        total_week = sum(row['ชั่วโมง'] for row in progress_rows)
        st.metric('เวลาอ่านจริงรวม 7 วัน', readable_time(total_week))
        chart_data = pd.DataFrame(progress_rows).set_index('วันที่')
        st.line_chart(chart_data, color='#4ECDC4', height=245, use_container_width=True)
        st.caption('กราฟเส้นแสดงจำนวนชั่วโมงที่บันทึกจริงในแต่ละวัน ไม่ใช่เวลาที่วางแผนไว้')
    st.divider()

    st.markdown('<div id="my-subjects"></div>', unsafe_allow_html=True)
    st.subheader('📝 งานและรายวิชาของฉัน')
    # ซ่อนเครื่องมือสร้าง/ลบชุดเริ่มต้น แต่คงงานทั้ง 30 รายการในข้อมูลไว้ตามเดิม
    if 'show_add_form' not in st.session_state:
        st.session_state.show_add_form = not bool(tasks)
    if st.button('✦  เพิ่มงานใหม่  ·  Create a New Task', key='new_task_launcher', use_container_width=True, type='primary'):
        st.session_state.show_add_form = not st.session_state.show_add_form
    if st.session_state.show_add_form:
        st.caption('กรอกข้อมูลด้านล่างเพื่อเพิ่มงานลงในรายวิชา')
    with st.expander('📝 แบบฟอร์มเพิ่มงาน', expanded=st.session_state.show_add_form):
        with st.form('add_task', clear_on_submit=True):
            subject = st.text_input('ชื่อวิชา', placeholder='เช่น ภาษาไทยเพื่อการสื่อสาร')
            task_name = st.text_input('ชื่องาน', placeholder='เช่น แบบฝึกหัดบทที่ 2')
            chosen_icon = st.selectbox('ไอคอนรายวิชา', list(SUBJECT_ICONS.keys()), index=0)
            due = st.date_input('กำหนดส่ง', min_value=date.today())
            difficulty = st.slider('ความยาก', 1, 5, 3)
            hour_col, minute_col = st.columns(2)
            with hour_col:
                planned_h = st.number_input('เวลาที่คาดว่าจะใช้ (ชั่วโมง)', 0, 100, 2, 1)
            with minute_col:
                planned_m = st.number_input('เวลาที่คาดว่าจะใช้ (นาที)', 0, 59, 0, 5)
            hours = planned_h + planned_m / 60
            submitted = st.form_submit_button('＋ เพิ่มงาน', type='primary', use_container_width=True)
        if submitted:
            if not subject.strip() or not task_name.strip():
                st.error('กรุณากรอกชื่อวิชาและชื่องาน')
            elif hours <= 0:
                st.error('กรุณาระบุเวลาที่คาดว่าจะใช้อย่างน้อย 1 นาที')
            else:
                new_task = {'id': max([t['id'] for t in tasks], default=0)+1,
                    'subject':subject.strip(), 'name':task_name.strip(), 'due':due.isoformat(),
                    'difficulty':difficulty, 'hours':float(hours), 'studied':0.0,
                    'done':False, 'logs':[], 'subject_icon':SUBJECT_ICONS[chosen_icon]}
                commit([*tasks, new_task], 'เพิ่มงานสำเร็จ')

    # รายการงานถูกวางไว้ใต้การ์ดสรุปด้านบน เพื่อให้คลิกแล้วเห็นผลทันที
    with filtered_list_area:
        st.markdown('<div id="my-subjects"></div>', unsafe_allow_html=True)
        st.subheader('📚 รายการงานตามสถานะ')
        filter_mode = st.segmented_control(
            'แสดงรายการ', ['ทั้งหมด','ยังไม่เสร็จ','เสร็จแล้ว'],
            key='task_filter'
        )
        visible = [t for t in tasks if filter_mode == 'ทั้งหมด' or
                   (filter_mode == 'ยังไม่เสร็จ' and not t['done']) or
                   (filter_mode == 'เสร็จแล้ว' and t['done'])]
        render_subjects(visible)


elif page == '📅 ปฏิทิน':
    st.subheader('📅 ปฏิทินการเรียน')
    st.caption('ตารางอ่านเป็นคำแนะนำอัตโนมัติ ไม่ใช่ประวัติเวลาที่อ่านจริง')
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
    st.markdown('<div class="calendar-legend"><span class="calendar-pill study">● มิ้นต์: มีแผนอ่าน</span><span class="calendar-pill due">● ส้ม: วันกำหนดส่ง</span><span class="calendar-pill today">★ วันนี้</span></div>', unsafe_allow_html=True)
    weekdays = [
        ('Monday', '#F3AF50', '#292F36'),
        ('Tuesday', '#FF9AC0', '#292F36'),
        ('Wednesday', '#7AD5A4', '#173E32'),
        ('Thursday', '#FFAF73', '#292F36'),
        ('Friday', '#8FD9F7', '#173A4B'),
        ('Saturday', '#B9A2F4', '#292F36'),
        ('Sunday', '#FF6B6B', '#FFFFFF'),
    ]
    for col, (label, background, foreground) in zip(st.columns(7), weekdays):
        col.markdown(
            f'<span class="weekday-name" style="background:{background};color:{foreground}">{label}</span>',
            unsafe_allow_html=True,
        )
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
                    suffix += f' 📖{readable_time(hours_today)}'
                if due_count:
                    suffix += f' 🟠{due_count}'
                if st.button(f'{day}{suffix}', key=f'cal_{key}' + ('-today' if key == date.today().isoformat() else ''), use_container_width=True,
                    type='primary' if st.session_state.get('selected_day') == key else 'secondary'):
                    st.session_state.selected_day = key
                    st.session_state.calendar_target_task = None
                    st.rerun()
    chosen = st.session_state.get('selected_day', date.today().isoformat())
    selected = date.fromisoformat(chosen)
    st.markdown(f'#### 📖 รายละเอียดวันที่ {selected.strftime("%d/%m/%Y")}')
    day_hours = sum(r['hours'] for r in by_day.get(chosen, []))
    day_due_count = len(due_by_day.get(chosen, []))
    st.markdown(f'<div class="calendar-summary">✦ แผนอ่าน {readable_time(day_hours)} &nbsp; · &nbsp; กำหนดส่ง {day_due_count} งาน</div>', unsafe_allow_html=True)
    rows = by_day.get(chosen, [])
    dues = due_by_day.get(chosen, [])
    if not rows and not dues:
        st.info('วันนี้ไม่มีแผนอ่านหรือกำหนดส่ง')
    for row in rows:
        st.markdown(f"📗 **{html.escape(row['subject'])} — {html.escape(row['name'])}** · {readable_time(row['hours'])}" + (' · ⚠️ หลังวันส่ง' if row['late'] else ''))
    for task in dues:
        st.markdown(f"🔔 กำหนดส่ง **{html.escape(task['subject'])} — {html.escape(task['name'])}**" + (' · ✅ เสร็จแล้ว' if task['done'] else ''))
    if rows or dues:
        unique_ids = list(dict.fromkeys([r['id'] for r in rows]+[t['id'] for t in dues]))
        target_id = st.session_state.get('calendar_target_task')
        with st.expander('🔎 เปิดรายละเอียดและทำเครื่องหมายงาน', expanded=target_id in unique_ids):
            for task in sorted(tasks, key=lambda item: (item['id'] != target_id, item['due'])):
                if task['id'] in unique_ids:
                    if task['id'] == target_id:
                        st.info(f'กำลังดูงาน: {task["subject"]} — {task["name"]}')
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


elif page == '📘 คู่มือใช้งาน':
    st.subheader('📘 คู่มือใช้งาน Smart Study Planner')
    st.caption('เริ่มต้นใช้งานได้ในไม่กี่ขั้นตอน · เว็บไซต์ทดลองเพื่อการศึกษา')
    st.markdown('### 🌟 Smart Study Planner คืออะไร?')
    st.write('คือเว็บไซต์ที่ช่วยให้นักศึกษาวางแผนการเรียนและจัดการงานได้อย่างเป็นระบบ โดยสามารถเพิ่มและจัดกลุ่มงานตามรายวิชา กำหนดวันส่ง บันทึกเวลาเรียน ติดตามความคืบหน้า จัดการสถานะงาน และตรวจสอบตารางงานผ่านปฏิทินได้อย่างสะดวกในที่เดียว')

    st.info('ข้อมูลอาจสูญหายเมื่อระบบรีสตาร์ต และผู้ใช้เว็บไซต์เดียวกันอาจเห็นข้อมูลร่วมกัน อย่าใส่ข้อมูลส่วนตัวหรือข้อมูลสำคัญ')

    st.markdown('### 🚀 เริ่มต้นใน 4 ขั้นตอน')
    steps = [
        ('1', 'เพิ่มงาน', 'ไปที่หน้าหลัก กด “เพิ่มงานใหม่” แล้วกรอกชื่อวิชา ชื่องาน วันกำหนดส่ง ความยาก และเวลาที่คาดว่าจะใช้ จากนั้นกด “เพิ่มงาน”'),
        ('2', 'ดูงานและจัดลำดับ', 'กดการ์ด “งานทั้งหมด” “เสร็จแล้ว” หรือ “รอดำเนินการ” เพื่อกรองงาน ระบบให้ความสำคัญกับวันกำหนดส่งก่อน'),
        ('3', 'บันทึกความคืบหน้า', 'เปิดหัวข้อรายวิชา เลือกงาน แล้วบันทึกเวลาอ่านจริงเป็นชั่วโมงและนาที เมื่อทำงานเสร็จ กด “เสร็จแล้ว”'),
        ('4', 'วางแผนด้วยปฏิทิน', 'ไปที่ “ปฏิทิน” เลือกเวลาว่างต่อวัน แล้วกดวันที่ต้องการเพื่อดูแผนอ่านและงานที่ครบกำหนด'),
    ]
    for number, heading, detail in steps:
        with st.container(border=True):
            st.markdown(f'#### {number}. {heading}')
            st.write(detail)

    st.markdown('### 🔎 คำอธิบายปุ่มที่ใช้บ่อย')
    with st.expander('📚 งานทั้งหมด / เสร็จแล้ว / รอดำเนินการ', expanded=True):
        st.write('กดเพื่อเลือกดูงานตามสถานะ โดยงานยังคงอยู่ในรายวิชาเดิม ไม่ได้ย้ายหรือลบข้อมูล')
    with st.expander('🔔 งานใกล้กำหนด และ Today Focus'):
        st.write('แสดงงานที่ควรติดตามและงานแนะนำสำหรับวันนี้ โดยเรียงให้วันกำหนดส่งสำคัญที่สุด')
    with st.expander('⏱️ บันทึกเวลาอ่าน และ ✓ เสร็จแล้ว'):
        st.write('บันทึกเวลาอ่านที่ทำจริงได้ก่อนงานเสร็จ หากกด “เสร็จแล้ว” งานจะถือว่าจบ ไม่ต้องบันทึกเวลาเพิ่ม')
    with st.expander('🗑️ ลบงาน'):
        st.write('หากกรอกข้อมูลผิด สามารถลบงานแล้วเพิ่มใหม่ได้ โปรดตรวจสอบก่อนยืนยัน เพราะการลบงานจะลบประวัติของงานนั้นด้วย')
    with st.expander('💾 สำรองและกู้คืนข้อมูล'):
        st.write('บนหน้าหลักกด “ไปที่สำรองข้อมูล” เพื่อดาวน์โหลด tasks.json เก็บไว้ หากต้องการกู้คืน ให้อัปโหลดไฟล์ JSON แล้วติ๊กยืนยันการแทนที่ข้อมูลปัจจุบัน')
    with st.expander('🌙 โหมดมืดและโหมดสว่าง'):
        st.write('ใช้สวิตช์ด้านขวาบนของเว็บไซต์เพื่อเปลี่ยนโหมดสีได้ตามต้องการ')

    st.markdown('### 🎬 วิดีโอแนะนำการใช้งาน')
    st.caption('วิดีโอสรุปขั้นตอน 1–2 นาที ใช้ประกอบการสาธิตโปรเจกต์')
    video_path = Path(__file__).with_name('study_guide.mp4')
    if video_path.exists():
        st.video(str(video_path))
    else:
        st.info('เพิ่มไฟล์ study_guide.mp4 ลงใน GitHub เพื่อแสดงวิดีโอในหน้านี้ หรือใช้คู่มือข้อความด้านบนได้ทันที')
    col_home, col_calendar = st.columns(2)
    col_home.button('🏠 เริ่มเพิ่มงาน', on_click=go_to_home, use_container_width=True, type='primary')
    col_calendar.button('📅 เปิดปฏิทิน', on_click=go_to_calendar, use_container_width=True)
