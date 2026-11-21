import json
import os
import random
import re
import requests
import streamlit as st
from openai import OpenAI

# ==========================================
# 1. НАСТРОЙКА СТРАНИЦЫ И ПОЛУЧЕНИЕ ФОТО ПАЧКИ
# ==========================================
st.set_page_config(
    page_title="СПИН-Тренажёр | Адсорбикс Экстра",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

POSTIMG_URL = "https://postimg.cc/CBXYHN2r/21aa9592"


@st.cache_data(ttl=86400)
def resolve_direct_image(url: str) -> str:
    if "i.postimg.cc" in url:
        return url
    try:
        resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        match = re.search(r'https://i\.postimg\.cc/[^"\'\s]+\.(?:jpg|jpeg|png|webp)', resp.text)
        if match:
            return match.group(0)
    except Exception:
        pass
    return ""


PACK_IMG_URL = resolve_direct_image(POSTIMG_URL)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .hero-banner {
        background: linear-gradient(135deg, #18181B 0%, #27272A 65%, #991B1B 100%);
        padding: 1.3rem 1.8rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.2rem;
        box-shadow: 0 6px 20px rgba(24, 24, 27, 0.22);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.5rem;
        border-bottom: 4px solid #DC2626;
    }
    .hero-text h1 {
        margin: 0;
        font-size: 1.6rem;
        font-weight: 800;
        color: white !important;
        letter-spacing: -0.02em;
    }
    .hero-text h1 span {
        color: #EF4444;
    }
    .hero-text p {
        margin: 0.4rem 0 0 0;
        font-size: 0.94rem;
        color: #E4E4E7;
    }
    .hero-pack-wrap {
        background: white;
        padding: 6px 12px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        flex-shrink: 0;
    }
    .hero-pack-wrap img {
        height: 82px;
        width: auto;
        display: block;
        object-fit: contain;
    }

    .product-sidebar-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-top: 4px solid #DC2626;
        border-radius: 12px;
        padding: 0.9rem;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .product-sidebar-card img {
        width: 100%;
        max-height: 150px;
        object-fit: contain;
        margin-bottom: 0.5rem;
    }
    .product-title {
        font-weight: 800;
        font-size: 1rem;
        color: #18181B;
    }
    .product-sub {
        font-size: 0.78rem;
        color: #52525B;
        margin-top: 2px;
        line-height: 1.35;
    }
    .product-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        justify-content: center;
        margin-top: 8px;
    }
    .product-pill {
        background: #FEF2F2;
        color: #B91C1C;
        border: 1px solid #FECACA;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 999px;
    }

    .doctor-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 5px solid #DC2626;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }
    .doctor-name {
        font-weight: 700;
        font-size: 1.05rem;
        color: #0F172A;
    }
    .doctor-meta {
        font-size: 0.86rem;
        color: #475569;
        margin-top: 3px;
    }
    .mood-badge {
        display: inline-block;
        margin-top: 8px;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        background: #FEE2E2;
        color: #991B1B;
    }

    .spin-tracker {
        display: flex;
        gap: 8px;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }
    .spin-step {
        flex: 1;
        min-width: 125px;
        padding: 0.55rem 0.7rem;
        border-radius: 10px;
        text-align: center;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid #E2E8F0;
        background: #FFFFFF;
        color: #64748B;
    }
    .spin-step.done {
        background: #ECFDF5;
        border-color: #10B981;
        color: #065F46;
    }
    .spin-step.active {
        background: #FEF2F2;
        border-color: #DC2626;
        color: #991B1B;
        box-shadow: 0 2px 6px rgba(220, 38, 38, 0.14);
    }

    .coach-box {
        background: #FFFBEB;
        border: 1px solid #FDE68A;
        border-left: 4px solid #F59E0B;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-size: 0.88rem;
        color: #92400E;
        margin-bottom: 1rem;
    }

    .score-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #FEF2F2 100%);
        border: 2px solid #DC2626;
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 1rem;
    }
    .score-big {
        font-size: 2.3rem;
        font-weight: 800;
        color: #DC2626;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==========================================
# 2. БАЗА ЗНАНИЙ: СЦЕНАРИИ СПИН (АДСОРБИКС)
# ==========================================
BASE_SCENARIOS = {
    "polisorb_vitamins": {
        "title": "Кейс 1: Полисорб (дефицит витаминов при диете)",
        "competitor": "Полисорб",
        "doctor_profile": "Асель Аскаровна — врач-дерматолог/аллерголог. Назначает Полисорб при аллергическом и атопическом дерматите.",
        "opening_hint": "Начните с ситуационного вопроса: узнайте, какие сорбенты врач обычно рекомендует при аллергическом и атопическом дерматите.",
        "cheat_sheet": """
- **Конкурент:** Полисорб
- **Скрытая проблема:** Приём сорбента совмещён с пищей → адсорбирует витамины, минералы и микроэлементы у пациента, который и так ограничен по диете.
- **Проблемный вопрос:** К чему приведёт резкое снижение поступления питательных веществ? *(К авитаминозу и затяжному течению болезни)*.
- **Усугубляющий вопрос:** Какие симптомы авитаминоза возникнут при таком лечении? *(Выпадение волос, ломкие ногти, слабость)*.
- **Выгода Адсорбикса:** Применяется за 1–2 часа до или после еды, НЕ влияет на усвоение витаминов и микроэлементов, не тормозит выздоровление.
        """,
        "system_prompt": """
Ты играешь роль врача Асель Аскаровны на визите медицинского представителя фармкомпании «Сэлтфар ЛТД» (препарат Адсорбикс Экстра).
СЦЕНАРИЙ: Ты назначаешь ПОЛИСОРБ при аллергическом и атопическом дерматите.

ТВОЯ ЛОГИКА ПОВЕДЕНИЯ ПО ЭТАПАМ СПИН:
1. [S - Ситуационный]: Когда МП спрашивает, какие сорбенты ты рекомендуешь при аллергическом/атопическом дерматите — ответь коротко и естественно: «Обычно я рекомендую Полисорб».
2. [P_info - Обозначение проблемы]: МП должен согласиться с важностью сорбентов (удаление эндо- и экзотоксинов), но указать на проблему: приём Полисорба совмещён с приёмом пищи, из-за чего он адсорбирует витамины, минералы и микроэлементы, а пациент на диете и так лишается минимального объёма питательных веществ.
3. [P_q - Проблемный вопрос]: Если МП спрашивает, какие последствия можно ожидать при резком снижении поступления питательных веществ — подтверди: «Это приводит к авитаминозу и затяжному течению болезни».
4. [I_q - Усугубляющий вопрос]: Если МП спрашивает о симптомах авитаминоза при лечении сорбентами, совмещёнными с приёмом пищи — ответь: «Выпадение волос, ломкие ногти, слабость».
5. [N_q - Вопрос о выгодности решения]: Если МП спрашивает, рекомендовала бы ты препарат, который применяется за 1–2 часа до или после приёма пищи, НЕ влияет на усвоение витаминов, минералов и микроэлементов и не тормозит процесс выздоровления — согласись: «Да, такой препарат при атопическом дерматите я бы рекомендовала».

ПРАВИЛА РЕАЛИЗМА:
- Отвечай как живой практикующий врач (2–4 предложения).
- НЕ перескакивай этапы сама. Если МП сразу рекламирует Адсорбикс, не раскрыв проблему с витаминами и диетой, возражай: «Меня Полисорб устраивает, пациенты к нему привыкли».
        """,
    },
    "polisorb_compliance": {
        "title": "Кейс 2: Полисорб (сложный расчёт дозы и низкий комплаенс)",
        "competitor": "Полисорб",
        "doctor_profile": "Асель Аскаровна — врач-аллерголог. Назначает Полисорб при атопическом дерматите, не задумываясь о сложности разведения.",
        "opening_hint": "Узнайте, какие сорбенты Асель Аскаровна рекомендует при аллергическом и атопическом дерматите.",
        "cheat_sheet": """
- **Конкурент:** Полисорб
- **Скрытая проблема:** По инструкции нужно высчитывать дозу по весу (0,1–0,2 г/кг в сутки), принимать 3–4 раза в день на 100 мл жидкости + обильно пить воду → падает комплаенс.
- **Проблемный вопрос:** К чему приведёт недополучение полноценной лечебной дозы из-за сложной схемы? *(Затягивается процесс выздоровления, сохраняются симптомы)*.
- **Усугубляющий вопрос:** Чем опасно длительное сохранение симптоматики и выделение медиаторов воспаления? *(Возможна хронизация заболевания с развитием экземы)*.
- **Выгода Адсорбикса:** Желатиновые капсулы 200 мг — не требуют сложного расчёта по массе тела и разведения в воде, быстро выводит эндо- и экзотоксины и не приводят к хронизации.
        """,
        "system_prompt": """
Ты играешь роль врача Асель Аскаровны на визите медицинского представителя фармкомпании «Сэлтфар ЛТД» (препарат Адсорбикс Экстра).
СЦЕНАРИЙ: Ты назначаешь ПОЛИСОРБ при аллергическом и атопическом дерматите.

ТВОЯ ЛОГИКА ПОВЕДЕНИЯ ПО ЭТАПАМ СПИН:
1. [S - Ситуационный]: На вопрос о сорбентах при дерматите ответь, что рекомендуешь Полисорб.
2. [P_info - Обозначение проблемы]: МП должен отметить сложность схемы Полисорба: расчёт разовой дозы по весу (0,1–0,2 г на 1 кг в сутки), приём 3–4 раза в день на 100 мл жидкости + обильное питьё. Чем чаще приём в сутки, тем ниже комплаенс.
3. [P_q - Проблемный вопрос]: На вопрос о последствиях недополучения лечебной дозы из-за сложности схемы — ответь: «У пациента затягивается процесс выздоровления и сохраняются симптомы заболевания».
4. [I_q - Усугубляющий вопрос]: На вопрос о последствиях длительного сохранения симптомов и выделения медиаторов воспаления — ответь: «Возможна хронизация заболевания с развитием экземы».
5. [N_q - Вопрос о выгодности решения]: На вопрос, рекомендовала бы ты препарат без расчёта по массе тела и разведения в воде, быстро выводящий токсины без риска хронизации — согласись: «Да, простая схема без разведения сильно повысила бы комплаенс, такой препарат я бы рекомендовала».

ПРАВИЛА РЕАЛИЗМА:
- Отвечай естественно (2–4 предложения).
- Без проработки проблемы расчёта по весу и низкого комплаенса не соглашайся менять назначения.
        """,
    },
    "enterosgel": {
        "title": "Кейс 3: Энтеросгель (ворсинки кишечника и размер молекул)",
        "competitor": "Энтеросгель",
        "doctor_profile": "Асель Аскаровна — врач-дерматолог/инфекционист. Назначает Энтеросгель при дерматитах и токсикоинфекциях.",
        "opening_hint": "Спросите Асель Аскаровну, какие сорбенты она обычно рекомендует при дерматитах.",
        "cheat_sheet": """
- **Конкурент:** Энтеросгель
- **Скрытая проблема:** По инструкции адсорбирует только среднемолекулярные метаболиты; микро- и макротоксины не связывает, так как не проникает между ворсинками кишечника.
- **Проблемный вопрос:** К чему приведёт сохранение микро- и макротоксинов между ворсинками? *(У пациента сохраняются симптомы заболевания)*.
- **Усугубляющий вопрос:** Что произойдёт при длительном выделении медиаторов воспаления? *(Хронизация процесса и развитие экземы)*.
- **Выгода Адсорбикса:** Благодаря микро- и мезопористости проникает между ворсинками и в труднодоступные места кишечника, тщательно вычищая токсины.
        """,
        "system_prompt": """
Ты играешь роль врача Асель Аскаровны на визите медицинского представителя фармкомпании «Сэлтфар ЛТД» (препарат Адсорбикс Экстра).
СЦЕНАРИЙ: Ты назначаешь ЭНТЕРОСГЕЛЬ при дерматитах и токсикоинфекциях.

ТВОЯ ЛОГИКА ПОВЕДЕНИЯ ПО ЭТАПАМ СПИН:
1. [S - Ситуационный]: На вопрос о сорбентах при дерматитах ответь, что рекомендуешь Энтеросгель.
2. [P_info - Обозначение проблемы]: МП должен указать, что по инструкции Энтеросгель адсорбирует только среднемолекулярные метаболиты, а микро- и макротоксины остаются между ворсинками кишечника и продолжают выделять медиаторы воспаления.
3. [P_q - Проблемный вопрос]: На вопрос о последствиях сохранения микро- и макротоксинов между ворсинками — ответь: «У пациента сохраняются симптомы заболевания».
4. [I_q - Усугубляющий вопрос]: На вопрос, что будет при длительном выделении медиаторов воспаления — ответь: «Хронизация процесса и развитие экземы».
5. [N_q - Вопрос о выгодности решения]: На вопрос о препарате с микро- и мезопористостью, который проникает между ворсинками и тщательно вычищает кишечник от токсинов — согласись: «Да, если препарат работает на уровне ворсинок и убирает микро- и макротоксины, я бы его рекомендовала».

ПРАВИЛА РЕАЛИЗМА:
- Говори как врач-профессионал (2–4 предложения).
- Без проработки проблемы среднемолекулярных метаболитов и ворсинок кишечника не соглашайся менять Энтеросгель.
        """,
    },
    "activated_charcoal": {
        "title": "Кейс 4: Активированный уголь (слизистая ЖКТ и 200 м²)",
        "competitor": "Активированный уголь",
        "doctor_profile": "Асель Аскаровна — врач-терапевт/дерматолог консервативных взглядов. Советует таблетированный активированный уголь.",
        "opening_hint": "Выясните у Асель Аскаровны, какие сорбенты она рекомендует при атопических дерматитах.",
        "cheat_sheet": """
- **Конкурент:** Активированный уголь (таблетированный)
- **Скрытая проблема:** Нужно разжёвывать → неоднородные крупные частицы травмируют слизистую ЖКТ и не попадают глубоко между ворсинками. Площадь сорбции всего 200 м².
- **Проблемный вопрос:** К чему приведёт, если в короткий срок не убрать причины воспаления? *(Симптомы сохраняются, переход в ремиссию затягивается)*.
- **Усугубляющий вопрос:** Что в конечном итоге ожидает такого пациента? *(Хронизация заболевания и присоединение экземы)*.
- **Выгода Адсорбикса:** Микронизированный уголь в желатиновых капсулах с максимальной адсорбирующей поверхностью 2000 м²/г — проникает глубоко между ворсинками, не травмируя слизистую кишечника.
        """,
        "system_prompt": """
Ты играешь роль врача Асель Аскаровны на визите медицинского представителя фармкомпании «Сэлтфар ЛТД» (препарат Адсорбикс Экстра).
СЦЕНАРИЙ: Ты назначаешь ТАБЛЕТИРОВАННЫЙ АКТИВИРОВАННЫЙ УГОЛЬ при атопических дерматитах.

ТВОЯ ЛОГИКА ПОВЕДЕНИЯ ПО ЭТАПАМ СПИН:
1. [S - Ситуационный]: На вопрос о сорбентах при атопических дерматитах ответь: «Рекомендую активированный уголь таблетированный».
2. [P_info - Обозначение проблемы]: МП должен объяснить, что таблетки нужно разжёвывать, неоднородные крупные частицы могут травмировать слизистую ЖКТ и не попадают глубоко между ворсинками, а адсорбирующая поверхность всего 200 м².
3. [P_q - Проблемный вопрос]: На вопрос, к чему приведёт, если в короткий срок не убрать причины воспаления — ответь: «У пациента сохраняются симптомы заболевания, процесс перехода в ремиссию затягивается».
4. [I_q - Усугубляющий вопрос]: На вопрос, что в конечном итоге ожидает такого пациента — ответь: «Хронизация заболевания и присоединение экземы».
5. [N_q - Вопрос о выгодности решения]: На вопрос о препарате с максимальной адсорбирующей поверхностью 2000 м²/г, который проникает глубоко между ворсинками и не травмирует слизистую — согласись: «Безусловно, 2000 м²/г без травматизации слизистой — это весомый аргумент, я бы его рекомендовала».

ПРАВИЛА РЕАЛИЗМА:
- Отвечай коротко и по-врачебному (2–4 предложения).
- Защищай привычный уголь («доступный и проверенный»), пока МП не раскроет проблему травмирования слизистой, ворсинок и малой площади (200 м² против 2000 м²/г).
        """,
    },
}

MENU_OPTIONS = {
    "polisorb_vitamins": BASE_SCENARIOS["polisorb_vitamins"]["title"],
    "polisorb_compliance": BASE_SCENARIOS["polisorb_compliance"]["title"],
    "enterosgel": BASE_SCENARIOS["enterosgel"]["title"],
    "activated_charcoal": BASE_SCENARIOS["activated_charcoal"]["title"],
    "random_exam": "🎲 Случайный визит (Экзамен — препарат неизвестен)",
}

SPIN_STAGES = [
    ("S", "1. Ситуационный"),
    ("P_info", "2. Проблема"),
    ("P_q", "3. Пробл. вопрос"),
    ("I_q", "4. Усугубл. вопрос"),
    ("N_q", "5. Выгода"),
]

# ==========================================
# 3. УСТОЙЧИВАЯ РАБОТА С СЕКРЕТАМИ И LLM
# ==========================================
def get_secret_safe(key: str, default: str = "") -> str:
    try:
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return os.getenv(key, default).strip()


def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {
        "doctor_reply": text,
        "completed_stages": [],
        "doctor_mood": "Внимательно слушает",
        "coach_hint": "Продолжайте вести врача по цепочке СПИН.",
        "is_finished": False,
    }


def call_llm_safe(api_keys_str: str, base_url: str, model: str, messages: list, temperature: float = 0.5) -> dict:
    keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
    current_key = random.choice(keys)
    client = OpenAI(api_key=current_key, base_url=base_url.strip())
    try:
        response = client.chat.completions.create(
            model=model.strip(),
            messages=messages,
            temperature=temperature,
        )
        return extract_json(response.choices[0].message.content)
    except Exception as e:
        return {
            "doctor_reply": f"⚠️ Ошибка API: {str(e)}",
            "completed_stages": [],
            "doctor_mood": "Ошибка подключения",
            "coach_hint": "Проверьте текст ошибки выше или настройки API в боковой панели.",
            "is_finished": False,
        }


def generate_turn(api_keys_str: str, base_url: str, model: str, scenario: dict, chat_history: list) -> dict:
    orchestrator_prompt = f"""
{scenario['system_prompt']}

ДОПОЛНИТЕЛЬНАЯ ЗАДАЧА ОЦЕНКИ:
Проанализируй всю историю диалога и верни ответ СТРОГО в формате JSON без markdown-обёрток:
{{
  "doctor_reply": "Твой ответ от лица врача Асель Аскаровны (2-4 предложения)",
  "completed_stages": ["список кодов пройденных МП этапов из: S, P_info, P_q, I_q, N_q"],
  "doctor_mood": "Краткий статус настроения врача (например: 'Скептична', 'Задумалась над аргументом', 'Готова рекомендовать Адсорбикс')",
  "coach_hint": "Краткая подсказка тренера для медпредставителя (1 предложение: что спросить или какие цифры/факты привести следующим шагом)",
  "is_finished": true или false
}}
"""
    messages = [{"role": "system", "content": orchestrator_prompt}]
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    return call_llm_safe(api_keys_str, base_url, model, messages, temperature=0.55)


def generate_final_report(api_keys_str: str, base_url: str, model: str, scenario: dict, chat_history: list) -> dict:
    eval_prompt = f"""
Ты — эксперт-тренер по медицинским продажам (методика СПИН) компании «Сэлтфар ЛТД».
Оцени диалог медпредставителя с врачом Асель Аскаровной по кейсу: {scenario['title']}.

ЭТАЛОННАЯ ЛОГИКА КЕЙСА:
{scenario['cheat_sheet']}

Верни разбор СТРОГО в формате JSON:
{{
  "total_score": число от 0 до 100,
  "stage_scores": {{
    "Ситуационный вопрос (С)": "балл из 20 и 1 фраза комментария",
    "Обозначение проблемы конкурента (П)": "балл из 20 и 1 фраза комментария",
    "Проблемный вопрос (П-вопрос)": "балл из 20 и 1 фраза комментария",
    "Усугубляющий вопрос (И-вопрос)": "балл из 20 и 1 фраза комментария",
    "Вопрос о выгодности решения (Н-вопрос)": "балл из 20 и 1 фраза комментария"
  }},
  "strengths": ["сильная сторона 1", "сильная сторона 2"],
  "improvements": ["что улучшить 1", "что улучшить 2"],
  "ideal_phrase": "Пример сильной финальной фразы о выгоде Адсорбикса для этого кейса"
}}
"""
    transcript = "\n".join(
        [f"{'МП' if m['role'] == 'user' else 'Врач'}: {m['content']}" for m in chat_history]
    )
    messages = [
        {"role": "system", "content": eval_prompt},
        {"role": "user", "content": f"Диалог:\n{transcript}"},
    ]
    return call_llm_safe(api_keys_str, base_url, model, messages, temperature=0.3)


# ==========================================
# 4. СОСТОЯНИЕ СЕССИИ (SESSION STATE)
# ==========================================
def resolve_active_case(menu_key: str) -> str:
    if menu_key == "random_exam":
        return random.choice(list(BASE_SCENARIOS.keys()))
    return menu_key


if "menu_choice" not in st.session_state:
    st.session_state.menu_choice = "polisorb_vitamins"
if "active_case_key" not in st.session_state:
    st.session_state.active_case_key = "polisorb_vitamins"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "completed_stages" not in st.session_state:
    st.session_state.completed_stages = []
if "doctor_mood" not in st.session_state:
    st.session_state.doctor_mood = "На приёме (ожидает начала диалога)"
if "coach_hint" not in st.session_state:
    st.session_state.coach_hint = BASE_SCENARIOS["polisorb_vitamins"]["opening_hint"]
if "final_report" not in st.session_state:
    st.session_state.final_report = None


def reset_session(menu_key: str):
    st.session_state.pop("visit_id", None)
    st.session_state.menu_choice = menu_key
    real_key = resolve_active_case(menu_key)
    st.session_state.active_case_key = real_key
    st.session_state.messages = []
    st.session_state.completed_stages = []
    st.session_state.doctor_mood = "На приёме (ожидает начала диалога)"
    st.session_state.coach_hint = BASE_SCENARIOS[real_key]["opening_hint"]
    st.session_state.final_report = None


# ==========================================
# 5. БОКОВАЯ ПАНЕЛЬ С КАРТОЧКОЙ ПРЕПАРАТА
# ==========================================
with st.sidebar:
    img_tag = (
        f'<img src="{PACK_IMG_URL}" alt="Адсорбикс Экстра">'
        if PACK_IMG_URL
        else ""
    )
    st.markdown(
        f"""
        <div class="product-sidebar-card">
            {img_tag}
            <div class="product-title">АДСОРБИКС® Экстра</div>
            <div class="product-sub">Уголь активированный микронизированный<br>200 мг • 15 желатиновых капсул</div>
            <div class="product-pills">
                <span class="product-pill">2000 м²/г</span>
                <span class="product-pill">Без расчёта по весу</span>
                <span class="product-pill">Не травмирует ЖКТ</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### ⚙️ Настройки симуляции")

    chosen_menu = st.selectbox(
        "Выберите сценарий визита:",
        options=list(MENU_OPTIONS.keys()),
        format_func=lambda k: MENU_OPTIONS[k],
        index=list(MENU_OPTIONS.keys()).index(st.session_state.menu_choice),
    )

    if chosen_menu != st.session_state.menu_choice:
        reset_session(chosen_menu)
        st.rerun()

    is_exam = st.session_state.menu_choice == "random_exam"
    coach_mode = st.toggle("💡 Подсказки ИИ-тренера", value=not is_exam, disabled=is_exam)

    if st.button("🔄 Начать визит заново", use_container_width=True):
        reset_session(chosen_menu)
        st.rerun()

    st.divider()

    if coach_mode and not is_exam:
        with st.expander("📋 Шпаргалка по кейсу", expanded=True):
            st.markdown(BASE_SCENARIOS[st.session_state.active_case_key]["cheat_sheet"])

        api_key = get_secret_safe("LLM_API_KEY")
    base_url = "https://api.groq.com/openai/v1"
    model_name = "openai/gpt-oss-20b"
# ==========================================
# 6. ОСНОВНОЙ ЭКРАН ТРЕНАЖЁРА
# ==========================================
current_scenario = BASE_SCENARIOS[st.session_state.active_case_key]
if st.sidebar.checkbox("📊 Результаты сотрудников"):
    import hmac

    st.title("Результаты сотрудников")
    password = st.text_input("Введите общий пароль", type="password")
    expected = get_secret_safe("RESULTS_PASSWORD")

    if not expected:
        st.info("Добавьте RESULTS_PASSWORD в настройках Streamlit.")
        st.stop()
    if not password:
        st.stop()
    if not hmac.compare_digest(password.encode(), expected.encode()):
        st.error("Пароль не подошёл. Попробуйте ещё раз.")
        st.stop()

    url = get_secret_safe("SUPABASE_URL").rstrip("/")
    key = get_secret_safe("SUPABASE_SECRET_KEY")

    try:
        response = requests.get(
            f"{url}/rest/v1/spin_results",
            headers={"apikey": key},
            params={
                "select": "finished_at,employee,scenario,score",
                "order": "finished_at.desc,visit_id.desc",
                "limit": 100,
            },
            timeout=10,
        )
        response.raise_for_status()
        rows = response.json()
    except requests.RequestException:
        st.error("Не удалось загрузить таблицу. Проверьте настройки Supabase.")
        st.stop()

    if rows:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        table = []
        for row in rows:
            date = datetime.fromisoformat(row["finished_at"].replace("Z", "+00:00"))
            table.append({
                "Дата и время (Алматы)": date.astimezone(
                    ZoneInfo("Asia/Almaty")
                ).strftime("%d.%m.%Y %H:%M"),
                "ФИО": row["employee"],
                "Сценарий": row["scenario"],
                "Балл из 100": row["score"],
            })
        st.caption("Последние 100 завершённых визитов")
        st.dataframe(table, hide_index=True, use_container_width=True)
    else:
        st.info("Пока нет завершённых визитов.")

    st.stop()
from uuid import uuid4

if "visit_id" not in st.session_state:
    st.session_state.visit_id = str(uuid4())

employee = st.text_input(
    "Ваше ФИО",
    key="employee_name",
    placeholder="Например, Майра Ибрагимова",
    disabled=bool(st.session_state.messages),
).strip()

if not employee:
    st.info("Введите ФИО, чтобы начать визит.")
    st.stop()

banner_pack_html = (
    f'<div class="hero-pack-wrap"><img src="{PACK_IMG_URL}" alt="Адсорбикс Экстра"></div>'
    if PACK_IMG_URL
    else ""
)

st.markdown(
    f"""
    <div class="hero-banner">
        <div class="hero-text">
            <h1>🩺 СПИН-Тренажёр: АДСОРБИКС <span>Экстра</span></h1>
            <p>Интерактивный симулятор визита к врачу • Представительство «Сэлтфар ЛТД» в РК</p>
        </div>
        {banner_pack_html}
    </div>
    """,
    unsafe_allow_html=True,
)

if is_exam and not st.session_state.final_report:
    doc_title = "👩‍⚕️ Асель Аскаровна — врач-дерматолог / терапевт (Режим экзамена)"
    doc_goal = "Цель визита: через ситуационный вопрос выяснить, какой сорбент назначает врач, и провести её по всем этапам СПИН к <b>Адсорбиксу Экстра</b>."
else:
    doc_title = f"👩‍⚕️ {current_scenario['doctor_profile']}"
    doc_goal = f"Цель визита: выявить скрытую проблему конкурента ({current_scenario['competitor']}) по методике СПИН и подвести к рекомендации <b>Адсорбикса Экстра</b>."

st.markdown(
    f"""
    <div class="doctor-card">
        <div class="doctor-name">{doc_title}</div>
        <div class="doctor-meta">{doc_goal}</div>
        <span class="mood-badge">Состояние врача: {st.session_state.doctor_mood}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

done_set = set(st.session_state.completed_stages)
next_active = None
for code, _ in SPIN_STAGES:
    if code not in done_set:
        next_active = code
        break

tracker_html = '<div class="spin-tracker">'
for code, label in SPIN_STAGES:
    if code in done_set:
        css_cls = "spin-step done"
        icon = "✅ "
    elif code == next_active:
        css_cls = "spin-step active"
        icon = "🎯 "
    else:
        css_cls = "spin-step"
        icon = ""
    tracker_html += f'<div class="{css_cls}">{icon}{label}</div>'
tracker_html += "</div>"
st.markdown(tracker_html, unsafe_allow_html=True)

if coach_mode and not is_exam and st.session_state.coach_hint and not st.session_state.final_report:
    st.markdown(
        f'<div class="coach-box"><b>💡 Подсказка тренера:</b> {st.session_state.coach_hint}</div>',
        unsafe_allow_html=True,
    )

if not st.session_state.messages:
    st.info("👋 Вы вошли в кабинет Асель Аскаровны. Поздоровайтесь и задайте первый ситуационный вопрос.")

for msg in st.session_state.messages:
    avatar = "🧑‍💼" if msg["role"] == "user" else "👩‍⚕️"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if not st.session_state.final_report:
    user_input = st.chat_input("Напишите реплику медпредставителя...")
    if user_input:
        if not api_key:
            st.error("Укажите API Key в боковой панели или в настройках Secrets на Streamlit.")
        else:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user", avatar="🧑‍💼"):
                st.markdown(user_input)

            with st.chat_message("assistant", avatar="👩‍⚕️"):
                with st.spinner("Асель Аскаровна отвечает..."):
                    turn_data = generate_turn(
                        api_key, base_url, model_name, current_scenario, st.session_state.messages
                    )
                    reply_text = turn_data.get("doctor_reply", "Продолжайте, коллега.")
                    st.markdown(reply_text)

            st.session_state.messages.append({"role": "assistant", "content": reply_text})
            st.session_state.completed_stages = turn_data.get(
                "completed_stages", st.session_state.completed_stages
            )
            st.session_state.doctor_mood = turn_data.get(
                "doctor_mood", st.session_state.doctor_mood
            )
            st.session_state.coach_hint = turn_data.get(
                "coach_hint", st.session_state.coach_hint
            )
            st.rerun()

if len(st.session_state.messages) >= 2 and not st.session_state.final_report:
    st.divider()
    if st.button("📊 Завершить визит и получить оценку по СПИН", type="primary"):
        if not api_key:
            st.error("Укажите API Key для формирования отчёта.")
        else:
            with st.spinner("ИИ-тренер анализирует ваш диалог..."):
                st.session_state.final_report = generate_final_report(
                    api_key, base_url, model_name, current_scenario, st.session_state.messages
                )
            st.rerun()

if st.session_state.final_report:
    report = st.session_state.final_report
    score = report.get("total_score")
    if type(score) is not int or not 0 <= score <= 100:
        st.error("ИИ не вернул балл. Нажмите кнопку, чтобы повторить оценку.")
        if st.button("Повторить оценку"):
            st.session_state.final_report = None
            st.rerun()
        st.stop()

    if st.session_state.get("saved_visit") != st.session_state.visit_id:
        url = get_secret_safe("SUPABASE_URL").rstrip("/")
        secret = get_secret_safe("SUPABASE_SECRET_KEY")
        if not url or not secret:
            st.error("Для сохранения заполните обе настройки Supabase в Secrets.")
            st.stop()

        try:
            response = requests.post(
                f"{url}/rest/v1/spin_results",
                headers={
                    "apikey": secret,
                    "Prefer": "resolution=ignore-duplicates,return=minimal",
                },
                json={
                    "visit_id": st.session_state.visit_id,
                    "employee": employee,
                    "scenario": current_scenario["title"],
                    "score": score,
                },
                timeout=10,
            )
            response.raise_for_status()
            st.session_state.saved_visit = st.session_state.visit_id
        except requests.RequestException:
            st.error("Не удалось сохранить результат. Оставьте страницу открытой.")
            if st.button("Повторить сохранение"):
                st.rerun()
            st.stop()

    st.success(f"Результат сохранён: {employee} — {score} из 100.")
    st.markdown('<div class="score-card">', unsafe_allow_html=True)
    if is_exam:
        st.caption(f"Раскрытый кейс экзамена: **{current_scenario['title']}**")

    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("#### Итоговый балл")
        st.markdown(f'<div class="score-big">{report.get("total_score", 0)} / 100</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("#### Детализация по этапам СПИН")
        for stage_name, comment in report.get("stage_scores", {}).items():
            st.markdown(f"- **{stage_name}:** {comment}")

    st.divider()
    c_good, c_bad = st.columns(2)
    with c_good:
        st.markdown("#### ✅ Что получилось отлично")
        for s in report.get("strengths", []):
            st.markdown(f"- {s}")
    with c_bad:
        st.markdown("#### 🎯 Точки роста")
        for imp in report.get("improvements", []):
            st.markdown(f"- {imp}")

    if report.get("ideal_phrase"):
        st.success(f"**Эталонная формулировка выгоды:** «{report['ideal_phrase']}»")

    st.markdown("</div>", unsafe_allow_html=True)
