import json
import re
from datetime import datetime
from html import escape
from urllib.parse import quote


_CONFIGS = {
    "beauty": {
        "emoji": "✂️",
        "primary": "#f472b6",
        "secondary": "#fb7185",
        "surface": "rgba(244,114,182,0.14)",
        "gradient": "linear-gradient(135deg,#261019 0%,#6f1d4f 48%,#fb7185 100%)",
        "eyebrow": "סטנדרט פרימיום לטיפוח אישי",
        "tagline": "סטייל מדויק, קצב רגוע וחוויה שממשיכה גם אחרי המראה.",
        "about": "שילוב של מקצוענות, הקשבה ודיוק בפרטים הקטנים כדי שכל ביקור ירגיש אישי ומרשים.",
        "detail_title": "חבילות וטיפולים בולטים",
        "detail_intro": "מבנה שירות שמאפשר תיאום מהיר, תוצאה עקבית ונראות שמחזיקה לאורך זמן.",
        "trust": ["קביעת תור מהירה", "היגיינה מוקפדת", "התאמה אישית", "לקוחות חוזרים קבועים"],
        "why": ["פגישת התאמה קצרה לפני כל טיפול", "קצב עבודה מדויק בלי לחץ", "קווים נקיים ותוצאה פוטוגנית", "תקשורת מהירה גם אחרי הטיפול"],
        "faq": [
            ("איך קובעים תור?", "אפשר להתקשר או לשלוח WhatsApp ולקבל חלונות זמינים באותו היום או ליום הבא."),
            ("צריך להגיע עם הכנה מוקדמת?", "ברוב הטיפולים לא. אם יש הכנה מיוחדת נשלחת הודעה מסודרת אחרי קביעת התור."),
          ("יש חבילות לאירועים?", "כן. ניתן להרכיב חבילת יופי/שיער/טאץ'־אפ מותאמת לאירוע, ללוח הזמנים ולתקציב."),
            ("מה לגבי שינוי או ביטול?", "עדכון עד 24 שעות מראש מאפשר הזזה נוחה של התור בלי עומס מיותר."),
            ("אפשר להתייעץ לפני שמחליטים?", "כן. נשלחת המלצה ראשונית לפי תמונות, סגנון מועדף ומטרת הטיפול."),
        ],
        "hours": ["יום א': 09:00-20:00", "יום ב': 09:00-20:00", "יום ג': 09:00-20:00", "יום ד': 09:00-20:00", "יום ה': 09:00-21:00", "יום ו': 08:00-15:00", "שבת: סגור"],
    },
    "health": {
        "emoji": "🩺",
        "primary": "#22c55e",
        "secondary": "#14b8a6",
        "surface": "rgba(34,197,94,0.14)",
        "gradient": "linear-gradient(135deg,#071b15 0%,#0f766e 44%,#34d399 100%)",
        "eyebrow": "בריאות, שקט וביטחון בכל שלב",
        "tagline": "ליווי מקצועי שמתרגם אבחון ברור לתהליך מדויק ונעים יותר.",
        "about": "הגישה משלבת מקצועיות קלינית, הסבר ברור ויחס אנושי כדי שכל טיפול ירגיש בטוח, מסודר ומובן.",
        "detail_title": "מסלולי טיפול ותהליך עבודה",
        "detail_intro": "כל שלב בנוי ליצירת ודאות, מדידה ומעקב ברור מהפגישה הראשונה ועד לתוצאה בפועל.",
        "trust": ["ליווי צמוד", "הסבר ברור", "סטנדרט שירות גבוה", "מענה מהיר להמשך טיפול"],
        "why": ["שילוב בין אבחון מקצועי להסבר פשוט", "תהליך מסודר עם יעדים ברורים", "גמישות בקביעת ביקורים ומעקב", "שקט וביטחון גם בין הפגישות"],
        "faq": [
            ("איך מתחילים?", "השלב הראשון הוא שיחת התאמה קצרה או ביקור ראשוני שבו מגדירים מטרה, מצב קיים ותכנית המשך."),
            ("מקבלים סיכום או תכנית?", "כן. אחרי הביקור נמסר סיכום ברור עם המלצות, דגשים וצעדי המשך רלוונטיים."),
            ("כמה זמן נמשך טיפול?", "משך הטיפול משתנה לפי סוג השירות, אך לוח הזמנים מוסבר מראש בצורה מלאה."),
            ("אפשר לתאם ביקור מהיר?", "במקרים רבים כן. נשמרים חלונות דחופים למטופלים קיימים ולפניות דחופות."),
            ("יש מעקב אחר ההתקדמות?", "כן. כאשר נדרש, נבנה מעקב מתוזמן כדי למדוד תוצאות ולהתאים את ההמשך."),
        ],
        "hours": ["יום א': 08:00-19:00", "יום ב': 08:00-19:00", "יום ג': 08:00-19:00", "יום ד': 08:00-19:00", "יום ה': 08:00-18:00", "יום ו': 08:00-13:00", "שבת: בתיאום מראש"],
    },
    "vehicles": {
        "emoji": "🚗",
        "primary": "#f59e0b",
        "secondary": "#fb7185",
        "surface": "rgba(245,158,11,0.14)",
        "gradient": "linear-gradient(135deg,#241607 0%,#92400e 40%,#f59e0b 100%)",
        "eyebrow": "אמינות, קצב ותוצאה שחוזרים אליה",
        "tagline": "שירות רכב מדויק עם שקיפות, זמינות וניהול עבודה שמכבד את הזמן שלך.",
        "about": "המטרה היא לייצר טיפול ברור, מתועד ויעיל בלי הפתעות מיותרות ועם תקשורת ישירה לאורך כל הדרך.",
        "detail_title": "חבילות שירות ובדיקות פופולריות",
        "detail_intro": "מבנה עבודה שמתחיל באבחון חד, ממשיך בהצעת מחיר שקופה ומסתיים במסירה מסודרת." ,
        "trust": ["אבחון שקוף", "עדכונים בזמן אמת", "עמידה בזמנים", "אחריות מסודרת"],
        "why": ["פירוט ברור לפני תחילת עבודה", "עדכון מצולם או טלפוני כשצריך", "תמחור ענייני בלי שכבות מיותרות", "מסירה מסודרת עם הסבר להמשך"],
        "faq": [
            ("איך יודעים מה הבעיה ברכב?", "מתחילים בבדיקת קבלה ואבחון מסודר. רק אחרי שמבינים את מקור התקלה מתקדמים להצעת מחיר."),
            ("מקבלים הערכת זמן?", "כן. זמן הטיפול ומועד המסירה המשוער ניתנים מראש ומתעדכנים אם נדרש."),
            ("יש שירותים מהירים?", "כן. בדיקות, טיפולים תקופתיים ושירותי תחזוקה רבים נסגרים בחלון קצר יחסית."),
            ("אפשר לעקוב אחרי ההתקדמות?", "כן. אפשר לקבל עדכון טלפוני או ב־WhatsApp לאורך הטיפול."),
            ("מה לגבי אחריות?", "בהתאם לסוג העבודה ניתן פירוט אחריות מסודר ומסירת המלצות להמשך תחזוקה."),
        ],
        "hours": ["יום א': 07:30-17:30", "יום ב': 07:30-17:30", "יום ג': 07:30-17:30", "יום ד': 07:30-17:30", "יום ה': 07:30-17:00", "יום ו': 07:30-12:30", "שבת: סגור"],
    },
    "repairs": {
        "emoji": "🛠️",
        "primary": "#60a5fa",
        "secondary": "#22d3ee",
        "surface": "rgba(96,165,250,0.14)",
        "gradient": "linear-gradient(135deg,#081120 0%,#1d4ed8 44%,#22d3ee 100%)",
        "eyebrow": "ביצוע נקי, תקשורת ברורה ואפס מריחות",
        "tagline": "עבודת שטח מסודרת עם הגעה מהירה, אבחון חד וגמר שמרגיש מקצועי.",
        "about": "השירות בנוי כדי לתת פתרון אמיתי בשטח: להגיע, להבין מהר, להסביר נכון ולבצע ברמה גבוהה.",
        "detail_title": "תהליך שירות מהפנייה ועד הסיום",
        "detail_intro": "כל עבודה מתחילה באבחון ברור וממשיכה לביצוע מסודר, נקי ועם סגירה מלאה של הפרטים.",
        "trust": ["הגעה מהירה", "תמחור ברור", "ביצוע נקי", "זמינות לעבודות המשך"],
        "why": ["אבחון תקלה לפני כל הצעת מחיר", "דגש על עמידה בזמנים", "סביבת עבודה נקייה ומסודרת", "מענה מהיר גם לאחר סיום העבודה"],
        "faq": [
            ("איך מזמינים ביקור?", "שולחים מיקום קצר ותיאור הבעיה ומקבלים חלון הגעה זמין."),
            ("אפשר לקבל הערכה מראש?", "כן. לאחר תיאור התקלה ניתנת הערכה ראשונית, ובשטח מקבלים תמונה מדויקת יותר."),
            ("מה קורה אם נדרש חלק או תיקון נוסף?", "המשך עבודה מתבצע רק אחרי עדכון ואישור ברור מצד הלקוח."),
            ("יש שירות דחוף?", "במקרים רבים כן. נשמרים חלונות מהירים לקריאות דחופות."),
            ("אפשר להזמין עבודות תחזוקה שוטפות?", "כן. ניתן לבנות ביקורים תקופתיים ותחזוקה מונעת לפי הצורך."),
        ],
        "hours": ["יום א': 08:00-18:30", "יום ב': 08:00-18:30", "יום ג': 08:00-18:30", "יום ד': 08:00-18:30", "יום ה': 08:00-18:00", "יום ו': 08:00-13:00", "שבת: קריאות חירום"],
    },
    "events": {
        "emoji": "🎉",
        "primary": "#a855f7",
        "secondary": "#f472b6",
        "surface": "rgba(168,85,247,0.14)",
        "gradient": "linear-gradient(135deg,#1e1033 0%,#6d28d9 42%,#f472b6 100%)",
        "eyebrow": "הפקה חכמה עם נוכחות, קצב ושליטה בפרטים",
        "tagline": "אירועים שנבנים נכון מהבריף הראשון ועד הרגע שבו הכל מתחבר במקום.",
        "about": "המיקוד הוא להוריד עומס, לחדד את הקונספט ולייצר חוויה מסודרת, יפה ומדויקת לאורך כל היום.",
        "detail_title": "מסלולי הפקה וחבילות בולטות",
        "detail_intro": "מתחילים בבריף, בונים קו יצירתי ברור ומנהלים את ההפקה כך שכל פרט יקבל מענה בזמן.",
        "trust": ["בריף מסודר", "ניהול ספקים", "לוחות זמנים ברורים", "חוויה מוקפדת לאורחים"],
        "why": ["שקיפות מלאה על שלבים ותקציב", "אחידות עיצובית ואווירה מדויקת", "ניהול לוגיסטי שמוריד עומס", "יכולת תגובה מהירה לשינויים"],
        "faq": [
            ("מתי כדאי להתחיל לתכנן?", "ככל שמתחילים מוקדם יותר, אפשר לבנות קונספט מדויק יותר ולתפוס תאריכים מבוקשים."),
            ("אפשר לקבל חבילה מלאה?", "כן. ניתן לקבל מעטפת מלאה או לבחור שירותים נקודתיים לפי צורך."),
            ("איך מתנהלים מול ספקים?", "כל ספק מקבל תיאום מסודר, חלוקת אחריות ולוח זמנים ברור מראש."),
            ("יש ליווי ביום האירוע?", "כן. בהתאם לחבילה ניתן לקבל ניהול, תפעול ופיקוח בזמן אמת."),
            ("אפשר להפיק גם אירועים קטנים?", "בהחלט. גם אירועים אינטימיים מקבלים אותה רמת ירידה לפרטים."),
        ],
        "hours": ["יום א': 09:00-18:00", "יום ב': 09:00-18:00", "יום ג': 09:00-18:00", "יום ד': 09:00-18:00", "יום ה': 09:00-20:00", "יום ו': לפי אירוע", "שבת: לפי אירוע"],
    },
    "education": {
        "emoji": "📚",
        "primary": "#38bdf8",
        "secondary": "#818cf8",
        "surface": "rgba(56,189,248,0.14)",
        "gradient": "linear-gradient(135deg,#091628 0%,#0f766e 24%,#6366f1 100%)",
        "eyebrow": "למידה בנויה נכון, ברורה ומקדמת",
        "tagline": "מסגרת מקצועית שמייצרת שגרה, בהירות והתקדמות שמרגישים לאורך זמן.",
        "about": "הגישה משלבת תהליך מסודר, יחס אישי ויעדים מדידים כדי לייצר למידה יציבה ובטוחה יותר.",
        "detail_title": "מסלולי למידה ותכנית עבודה",
        "detail_intro": "כל תהליך נבנה סביב מטרה ברורה, קצב מותאם וכלים שמאפשרים לייצר התקדמות רציפה.",
        "trust": ["יחס אישי", "תכנית מסודרת", "מעקב התקדמות", "תקשורת שוטפת"],
        "why": ["בניית מסלול לפי רמה ויעד", "שילוב בין תרגול להבנה עמוקה", "מעקב ברור אחר התקדמות", "קצב למידה מותאם ולא גנרי"],
        "faq": [
            ("איך בונים תכנית לימוד?", "מתחילים באפיון רמה, מטרה ולוח זמנים ואז בונים מסלול ברור ומדורג."),
            ("יש מפגשים פרטניים או קבוצתיים?", "בהתאם למסגרת ניתן לבחור פרטני, זוגי, קבוצתי או שילוב ביניהם."),
            ("איך מודדים התקדמות?", "באמצעות אבני דרך, משימות קצרות ומעקב שוטף לאורך התהליך."),
            ("אפשר לשלב אונליין?", "כן. במידת הצורך ניתן לשלב מפגשים דיגיטליים וכלי עבודה מרחוק."),
            ("יש עדכונים להורים או למלווים?", "כן. כאשר זה רלוונטי מתקבלים עדכונים תקופתיים עם תמונת מצב ברורה."),
        ],
        "hours": ["יום א': 09:00-19:00", "יום ב': 09:00-19:00", "יום ג': 09:00-19:00", "יום ד': 09:00-19:00", "יום ה': 09:00-18:00", "יום ו': 09:00-13:00", "שבת: סגור"],
    },
    "professional": {
        "emoji": "⭐",
        "primary": "#8b5cf6",
        "secondary": "#3b82f6",
        "surface": "rgba(139,92,246,0.14)",
        "gradient": "linear-gradient(135deg,#16122b 0%,#5b21b6 44%,#3b82f6 100%)",
        "eyebrow": "נוכחות דיגיטלית חדה לעסק מקומי מוביל",
        "tagline": "שירות מקומי שמחבר בין מקצוענות, זמינות ותחושת ביטחון כבר מהמגע הראשון.",
        "about": "דף שמציג עסק מקומי באופן יוקרתי, ברור ומשכנע כדי להפוך התעניינות לפנייה ממשית.",
        "detail_title": "שירותים ומסלולי עבודה מובילים",
        "detail_intro": "מבנה שמאפשר ללקוח להבין מהר מה מקבלים, איך מתקדמים ולמה דווקא כאן.",
        "trust": ["זמינות גבוהה", "תהליך ברור", "שירות אישי", "מוניטין מקומי"],
        "why": ["הצעת ערך ברורה כבר מהפתיחה", "נראות פרימיום שמבדלת בעיר", "מעבר מהיר מפנייה לשיחה", "מבנה תוכן שמייצר אמון"],
        "faq": [
            ("מה כוללת הפנייה הראשונית?", "שיחה קצרה להבנת הצורך, יעד השירות והדרך המהירה ביותר להתקדם."),
            ("אפשר לקבל הצעת מחיר?", "כן. לאחר אפיון קצר ניתן לקבל כיוון ברור או הצעת מחיר מסודרת."),
            ("יש זמינות קרובה?", "במקרים רבים כן. מומלץ לשלוח WhatsApp ולקבל מענה מהיר."),
            ("השירות מתאים גם לעסקים/ארגונים?", "כן. ניתן להתאים את אופי השירות גם לעבודה מול ארגונים וצוותים."),
            ("אפשר להגיע פיזית?", "בהתאם לעסק ולסוג השירות, מוצעת הגעה, קבלה במקום או עבודה מרחוק."),
        ],
        "hours": ["יום א': 09:00-18:00", "יום ב': 09:00-18:00", "יום ג': 09:00-18:00", "יום ד': 09:00-18:00", "יום ה': 09:00-17:00", "יום ו': 09:00-13:00", "שבת: סגור"],
    },
}


def _clean_phone(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _to_wa_phone(value: str) -> str:
    digits = _clean_phone(value)
    if not digits:
        return "972546363350"
    if digits.startswith("972"):
        return digits
    if digits.startswith("0"):
        return f"972{digits[1:]}"
    return digits


def _safe_href(url: str) -> str:
    candidate = (url or "").strip()
    if candidate.startswith(("http://", "https://", "tel:", "mailto:")):
        return escape(candidate, quote=True)
    return "#"


def _coerce_list(value) -> list:
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except Exception:
            return [part.strip() for part in re.split(r"\n|\|\|", raw) if part.strip()]
        return parsed if isinstance(parsed, list) else []
    return []


def _normalize_services(services, kind: str) -> list[dict]:
    normalized = []
    for item in services or []:
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("title") or "שירות")
            desc = str(item.get("desc") or item.get("description") or "")
            price = str(item.get("price") or "")
        else:
            name = str(item)
            desc = ""
            price = ""
        if not name.strip():
            continue
        normalized.append({
            "name": escape(name.strip()),
            "desc": escape(desc.strip()),
            "price": escape(price.strip()),
        })

    if normalized:
        return normalized[:6]

    fallbacks = {
        "beauty": [
            {"name": "ייעוץ והתאמה", "desc": "אבחון קצר והמלצה למסלול", "price": "בתיאום"},
            {"name": "טיפול דגל", "desc": "השירות המבוקש ביותר במקום", "price": "פרימיום"},
            {"name": "טאץ'־אפ מהיר", "desc": "שיפור נראות לפני אירוע", "price": "מהיר"},
        ],
        "health": [
            {"name": "פגישת אבחון", "desc": "היכרות, בדיקה ותכנית המשך", "price": "ראשוני"},
            {"name": "טיפול פרטני", "desc": "מפגש ממוקד עם יעדים ברורים", "price": "מותאם"},
            {"name": "מעקב והתקדמות", "desc": "מדידה ועדכון מסודר", "price": "שוטף"},
        ],
        "vehicles": [
            {"name": "בדיקת קבלה", "desc": "אבחון מהיר והצעת כיוון", "price": "מהיר"},
            {"name": "טיפול מרכזי", "desc": "תחזוקה או תיקון נפוץ", "price": "שקוף"},
            {"name": "מסירה והסבר", "desc": "סיכום עבודה והמשך תחזוקה", "price": "מסודר"},
        ],
        "repairs": [
            {"name": "קריאת שירות", "desc": "הגעה, בדיקה והמלצה", "price": "זמין"},
            {"name": "ביצוע בשטח", "desc": "פתרון מקצועי ונקי", "price": "מדויק"},
            {"name": "תחזוקה שוטפת", "desc": "ביקורים יזומים והמשך טיפול", "price": "קבוע"},
        ],
        "events": [
            {"name": "בריף ראשוני", "desc": "הבנת קהל, תקציב וקונספט", "price": "פתיחה"},
          {"name": "הפקה פעילה", "desc": "ניהול ספקים ולוח זמנים", "price": "מלא"},
            {"name": "ליווי יום האירוע", "desc": "נוכחות ותפעול בזמן אמת", "price": "פרימיום"},
        ],
        "education": [
            {"name": "מיפוי רמה", "desc": "בדיקת פתיחה והגדרת יעד", "price": "פתיחה"},
            {"name": "מסלול למידה", "desc": "מפגשים בקצב מותאם", "price": "מותאם"},
            {"name": "מעקב התקדמות", "desc": "יעדים, משימות ושיקוף", "price": "שוטף"},
        ],
        "professional": [
            {"name": "שיחת אפיון", "desc": "מגדירים צורך ויעד", "price": "מהיר"},
            {"name": "שירות מוביל", "desc": "הפתרון המרכזי ללקוח", "price": "מותאם"},
            {"name": "ליווי המשך", "desc": "מענה רציף גם אחרי הפנייה", "price": "זמין"},
        ],
    }
    return fallbacks[kind]


def _normalize_reviews(raw_reviews, fallback_text: str) -> list[dict]:
    reviews = []
    for item in _coerce_list(raw_reviews):
        if isinstance(item, dict):
            text = str(item.get("text") or item.get("comment") or item.get("review") or "").strip()
            author = str(item.get("author_name") or item.get("author") or item.get("user") or "לקוח/ה מרוצה").strip()
            rating = item.get("rating") or 5
        else:
            text = str(item).strip()
            author = "לקוח/ה מרוצה"
            rating = 5
        if not text:
            continue
        try:
            score = float(rating)
        except Exception:
            score = 5.0
        if score < 4:
            continue
        reviews.append({
            "text": escape(text[:280]),
            "author": escape(author[:64]),
            "rating": max(4.0, min(5.0, score)),
        })

    if reviews:
        return reviews[:5]

    seed = (fallback_text or "שירות חד, יחס מצוין ותוצאה שמרגישים מיד.").strip()
    fallback = escape(seed[:220])
    return [
        {"text": fallback, "author": "ביקורת נבחרת", "rating": 5.0},
        {"text": "מענה מהיר, תהליך ברור ותחושת ביטחון מהרגע הראשון.", "author": "לקוח/ה חוזר/ת", "rating": 5.0},
        {"text": "הביצוע היה מדויק, נעים ומאוד מקצועי. בדיוק מה שחיפשנו.", "author": "המלצה מקומית", "rating": 5.0},
    ]


def _stars(value: float) -> str:
    full = max(1, min(5, int(round(value))))
    return "★" * full + "☆" * (5 - full)


def _hours_rows(hours: list[str]) -> str:
    rows = []
    for item in hours[:7]:
        day, _, span = str(item).partition(":")
        day_text = escape(day.strip() or str(item).strip())
        span_text = escape(span.strip() or "בתיאום מראש")
        rows.append(
            f'<div class="hours-row"><span>{day_text}</span><strong>{span_text}</strong></div>'
        )
    return "".join(rows)


def _faq_html(items: list[tuple[str, str]]) -> str:
    return "".join(
        f'<details class="faq-item reveal"><summary>{escape(question)}</summary><div class="faq-answer">{escape(answer)}</div></details>'
        for question, answer in items
    )


def _render_premium_site(c: dict, kind: str, services) -> str:
    config = _CONFIGS[kind]
    name_raw = re.sub(r"\s*Draft Site$", "", c.get("site_title") or c.get("hero_title") or c.get("business_name") or "העסק")
    name = escape(name_raw)
    hero_title = escape(c.get("hero_title") or c.get("site_title") or c.get("business_name") or name_raw)
    phone_raw = c.get("phone") or ""
    phone = escape(phone_raw)
    phone_clean = _clean_phone(phone_raw)
    wa_phone = _to_wa_phone(c.get("wa_admin_phone") or phone_raw)
    city_raw = c.get("city") or ""
    city = escape(city_raw)
    address_raw = c.get("address") or city_raw
    address = escape(address_raw)
    category = escape(c.get("category") or "")
    business_types = escape(c.get("business_types") or "")
    tagline = escape(c.get("tagline") or config["tagline"])
    about_text_raw = c.get("about_text") or c.get("top_review") or config["about"]
    about_text = escape(str(about_text_raw).strip())
    photo_url = _safe_href(c.get("photo_url") or "")
    website_url = _safe_href(c.get("website") or "")
    maps_seed = c.get("maps_url") or c.get("google_maps_url") or ""
    if not maps_seed and address_raw:
        maps_seed = f"https://www.google.com/maps/search/{quote(address_raw)}"
    maps_url = _safe_href(maps_seed)
    reviews = _normalize_reviews(c.get("reviews_json"), str(about_text_raw))
    opening_hours = [str(item) for item in _coerce_list(c.get("opening_hours")) if str(item).strip()] or config["hours"]
    service_items = _normalize_services(services, kind)
    rating = float(c.get("rating") or 0) if c.get("rating") else 0.0
    reviews_count = int(c.get("reviews_count") or 0)
    today = datetime.utcnow().strftime("%d/%m/%Y")
    year = datetime.utcnow().year

    stats = [
        {
            "value": len(service_items),
            "label": "תחומי מומחיות",
            "suffix": "+",
            "decimals": 0,
        },
        {
            "value": rating if rating else 24,
            "label": "דירוג ממוצע" if rating else "זמן מענה",
            "suffix": "" if rating else "h",
            "decimals": 1 if rating else 0,
        },
        {
            "value": reviews_count if reviews_count else len(opening_hours),
            "label": "ביקורות" if reviews_count else "ימי פעילות",
            "suffix": "+" if reviews_count else "",
            "decimals": 0,
        },
    ]

    hero_chip = (
        f'<div class="hero-chip">⭐ {rating:.1f} · {reviews_count} ביקורות</div>'
        if rating and reviews_count
        else f'<div class="hero-chip">{config["eyebrow"]}</div>'
    )
    claim_url = (
        "https://tazo-sync.com/dashboard?action=claim"
        f"&phone={quote(phone_clean)}&business={quote(name_raw)}&source=tazo-web"
    )
    owner_bar = (
        '<div class="owner-claim">'
        '<span>בעל/ת העסק?</span>'
        f'<a href="{claim_url}" target="_blank" rel="noopener">תבעו בעלות וערכו תוכן, תמונות ומחירים</a>'
        '</div>'
    )

    service_cards = "".join(
        (
            '<article class="service-card reveal">'
            f'<div class="service-icon">{config["emoji"]}</div>'
            f'<h3>{item["name"]}</h3>'
            f'<p>{item["desc"] or "שירות מותאם אישית לפי צורך, זמינות ולוח זמנים."}</p>'
            f'<div class="service-price">{item["price"] or "פרטים בשיחה"}</div>'
            '</article>'
        )
        for item in service_items
    )
    review_cards = "".join(
        (
            '<article class="review-card">'
            f'<div class="review-stars">{_stars(item["rating"])}<span>{item["rating"]:.1f}</span></div>'
            f'<p>{item["text"]}</p>'
            f'<strong>{item["author"]}</strong>'
            '</article>'
        )
        for item in reviews
    )
    review_track = review_cards * (2 if len(reviews) > 1 else 1)
    trust_badges = "".join(f'<div class="trust-pill">{escape(text)}</div>' for text in config["trust"])
    why_cards = "".join(
        f'<div class="why-card"><span>✓</span><p>{escape(point)}</p></div>' for point in config["why"]
    )
    detail_cards = "".join(
        (
            '<article class="detail-card reveal">'
            f'<span class="detail-kicker">מסלול {index + 1:02d}</span>'
            f'<h3>{item["name"]}</h3>'
            f'<p>{item["desc"] or "מבנה שירות ברור, התאמה אישית וליווי לאורך כל התהליך."}</p>'
            f'<div class="detail-value">{item["price"] or "בתיאום"}</div>'
            '</article>'
        )
        for index, item in enumerate(service_items[:3])
    )
    stats_html = "".join(
        (
            '<div class="stat-card reveal">'
            f'<strong class="stat-number" data-counter data-target="{item["value"]}" data-decimals="{item["decimals"]}" data-suffix="{item["suffix"]}">0</strong>'
            f'<span>{item["label"]}</span>'
            '</div>'
        )
        for item in stats
    )

    nav_phone = f'<a class="header-phone" href="tel:{phone_clean}">📞 {phone}</a>' if phone_clean else ""
    call_cta = f'<a class="btn btn-primary" href="tel:{phone_clean}">📞 התקשרו עכשיו</a>' if phone_clean else ""
    maps_cta = f'<a class="btn btn-ghost" href="{maps_url}" target="_blank" rel="noopener">🗺️ ניווט מהיר</a>' if maps_url != "#" else ""
    website_cta = f'<a class="btn btn-ghost" href="{website_url}" target="_blank" rel="noopener">🌐 אתר / מידע נוסף</a>' if website_url != "#" else ""
    photo_block = (
        f'<div class="about-photo reveal"><img src="{photo_url}" alt="{name}" loading="lazy"/></div>'
        if photo_url != "#" else '<div class="about-photo reveal about-photo-fallback">' + config["emoji"] + '</div>'
    )

    return f'''<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <meta name="robots" content="index,follow"/>
  <title>{name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800;900&display=swap" rel="stylesheet"/>
  <style>
    :root{{
      --bg:#0b1120;
      --panel:#111a2e;
      --panel-2:#15213a;
      --line:rgba(255,255,255,.08);
      --text:#f8fafc;
      --muted:rgba(248,250,252,.68);
      --primary:{config["primary"]};
      --secondary:{config["secondary"]};
      --surface:{config["surface"]};
      --gradient:{config["gradient"]};
      --shadow:0 24px 80px rgba(2,6,23,.42);
    }}
    *{{box-sizing:border-box}}
    html{{scroll-behavior:smooth}}
    body{{margin:0;font-family:"Heebo",Arial,sans-serif;background:radial-gradient(circle at top right, rgba(255,255,255,.06), transparent 28%),linear-gradient(180deg,#08101d 0%,#0d1527 100%);color:var(--text)}}
    a{{color:inherit;text-decoration:none}}
    img{{display:block;max-width:100%}}
    .container{{width:min(1180px,calc(100% - 32px));margin:0 auto}}
    .owner-claim{{position:sticky;top:0;z-index:80;display:flex;align-items:center;justify-content:center;gap:10px;padding:9px 14px;background:#f8fafc;color:#111827;border-bottom:1px solid rgba(15,23,42,.08);font-size:13px;font-weight:800;direction:rtl}}
    .owner-claim a{{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;background:#111827;color:#fff;padding:7px 14px;font-weight:900;box-shadow:0 8px 22px rgba(15,23,42,.18)}}
    .site-header{{position:sticky;top:39px;z-index:40;background:rgba(8,14,27,.68);backdrop-filter:blur(18px);border-bottom:1px solid transparent;transition:.25s ease}}
    .site-header.scrolled{{border-color:var(--line);box-shadow:0 16px 40px rgba(2,6,23,.35)}}
    .header-inner{{display:flex;align-items:center;justify-content:space-between;gap:20px;min-height:78px}}
    .brand-block{{display:flex;flex-direction:column;gap:4px}}
    .brand-block strong{{font-size:19px;font-weight:900}}
    .brand-block span{{color:var(--muted);font-size:13px}}
    .nav-toggle{{display:none;background:rgba(255,255,255,.06);border:1px solid var(--line);color:var(--text);width:46px;height:46px;border-radius:14px;font-size:20px}}
    .site-nav{{display:flex;align-items:center;gap:18px}}
    .site-nav a{{color:var(--muted);font-weight:700;font-size:14px}}
    .site-nav a:hover{{color:var(--text)}}
    .header-phone{{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.06);border:1px solid var(--line);padding:12px 18px;border-radius:999px;font-weight:800}}
    .hero{{position:relative;overflow:hidden;padding:88px 0 48px;background:var(--gradient)}}
    .hero::before,.hero::after{{content:"";position:absolute;border-radius:999px;filter:blur(50px);opacity:.45}}
    .hero::before{{width:320px;height:320px;right:-70px;top:-50px;background:rgba(255,255,255,.18)}}
    .hero::after{{width:260px;height:260px;left:-40px;bottom:-60px;background:rgba(255,255,255,.12)}}
    .hero-grid{{position:relative;display:grid;grid-template-columns:1.2fr .8fr;gap:28px;align-items:end}}
    .hero-copy{{padding:18px 0 28px}}
    .hero-chip{{display:inline-flex;align-items:center;gap:10px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);border-radius:999px;padding:9px 16px;margin-bottom:18px;font-weight:800;font-size:13px}}
    .hero h1{{margin:0;font-size:clamp(38px,7vw,72px);line-height:1.02;font-weight:900;max-width:760px}}
    .hero p{{max-width:620px;font-size:18px;line-height:1.85;color:rgba(255,255,255,.84);margin:18px 0 0}}
    .hero-meta{{display:flex;flex-wrap:wrap;gap:12px;margin-top:22px;color:rgba(255,255,255,.82);font-weight:700}}
    .hero-actions{{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px}}
    .btn{{display:inline-flex;align-items:center;justify-content:center;gap:10px;border-radius:18px;padding:15px 22px;font-weight:800;transition:transform .22s ease, box-shadow .22s ease,border-color .22s ease}}
    .btn:hover{{transform:translateY(-2px)}}
    .btn-primary{{background:#fff;color:#0f172a;box-shadow:0 14px 28px rgba(15,23,42,.22)}}
    .btn-ghost{{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);color:#fff}}
    .hero-panel{{background:rgba(8,14,27,.44);border:1px solid rgba(255,255,255,.14);border-radius:30px;padding:24px;box-shadow:var(--shadow);backdrop-filter:blur(18px)}}
    .hero-panel .panel-title{{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}}
    .hero-panel .panel-title strong{{font-size:18px}}
    .hero-panel .panel-title span{{color:rgba(255,255,255,.68);font-weight:700}}
    .panel-stack{{display:grid;gap:12px}}
    .panel-item{{display:flex;justify-content:space-between;gap:12px;padding:14px 16px;border-radius:18px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08)}}
    .panel-item strong{{font-size:15px}}
    .panel-item span{{color:rgba(255,255,255,.7);font-size:14px}}
    .hero-scroll{{display:inline-flex;align-items:center;gap:8px;margin-top:26px;color:#fff;font-weight:800;opacity:.84;animation:floatY 1.8s ease-in-out infinite}}
    .stats-strip{{margin-top:-24px;position:relative;z-index:2}}
    .stats-wrap{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;background:rgba(6,12,23,.92);border:1px solid var(--line);border-radius:30px;padding:18px;box-shadow:var(--shadow)}}
    .stat-card{{padding:18px;border-radius:22px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);text-align:center}}
    .stat-number{{display:block;font-size:38px;font-weight:900;color:#fff}}
    .stat-card span{{display:block;color:var(--muted);font-size:14px;font-weight:700}}
    section{{padding:78px 0}}
    .section-head{{display:flex;justify-content:space-between;gap:18px;align-items:end;margin-bottom:28px}}
    .section-head h2{{margin:0;font-size:clamp(28px,4vw,42px);line-height:1.05}}
    .section-head p{{margin:0;color:var(--muted);max-width:680px;line-height:1.85}}
    .trust-strip{{padding:26px 0 0}}
    .trust-wrap{{display:flex;flex-wrap:wrap;gap:12px}}
    .trust-pill{{padding:12px 18px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.04);font-weight:800;color:#e2e8f0}}
    .services-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}
    .service-card,.detail-card,.about-copy,.about-photo,.hours-card,.faq-panel,.verify-card,.contact-card{{background:rgba(11,17,32,.8);border:1px solid var(--line);border-radius:28px;box-shadow:var(--shadow)}}
    .service-card{{padding:24px}}
    .service-icon{{width:54px;height:54px;border-radius:18px;display:grid;place-items:center;background:var(--surface);color:#fff;font-size:24px;margin-bottom:16px}}
    .service-card h3,.detail-card h3{{margin:0 0 10px;font-size:22px}}
    .service-card p,.detail-card p,.about-copy p,.verify-card p,.contact-meta{{color:var(--muted);line-height:1.85}}
    .service-price,.detail-value{{display:inline-flex;align-items:center;gap:8px;margin-top:16px;padding:10px 14px;border-radius:999px;background:rgba(255,255,255,.06);font-weight:800}}
    .reviews-shell{{overflow:hidden;border:1px solid var(--line);border-radius:30px;background:rgba(255,255,255,.03);padding:18px}}
    .reviews-track{{display:flex;gap:16px;width:max-content;animation:rv-scroll 34s linear infinite}}
    .review-card{{width:min(360px,82vw);padding:22px;border-radius:24px;background:#101a30;border:1px solid rgba(255,255,255,.08)}}
    .review-stars{{display:flex;align-items:center;gap:10px;color:#fbbf24;font-weight:900;margin-bottom:14px}}
    .review-card p{{margin:0 0 18px;color:#e2e8f0;line-height:1.85;min-height:118px}}
    .review-card strong{{color:#fff;font-size:14px}}
    .why-band{{background:linear-gradient(135deg,rgba(255,255,255,.08),var(--surface));border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}
    .why-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:22px}}
    .why-card{{padding:20px;border-radius:24px;background:rgba(7,11,22,.54);border:1px solid rgba(255,255,255,.08)}}
    .why-card span{{display:inline-grid;place-items:center;width:36px;height:36px;border-radius:12px;background:rgba(255,255,255,.1);font-weight:900;margin-bottom:14px}}
    .why-card p{{margin:0;line-height:1.75;color:#e2e8f0}}
    .detail-layout{{display:grid;grid-template-columns:.95fr 1.05fr;gap:22px;align-items:start}}
    .detail-copy{{padding:14px 4px}}
    .detail-copy ul{{margin:18px 0 0;padding:0;list-style:none;display:grid;gap:12px}}
    .detail-copy li{{padding:12px 16px;border-radius:16px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);color:#e2e8f0}}
    .detail-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}
    .detail-card{{padding:22px}}
    .detail-kicker{{display:inline-block;margin-bottom:12px;font-size:12px;font-weight:800;letter-spacing:.08em;color:#cbd5e1;text-transform:uppercase}}
    .hours-card{{padding:26px}}
    .hours-grid{{display:grid;gap:10px}}
    .hours-row{{display:flex;justify-content:space-between;gap:16px;padding:14px 16px;border-radius:18px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.05)}}
    .hours-row span{{color:var(--muted)}}
    .faq-panel{{padding:22px}}
    .faq-item{{border:1px solid rgba(255,255,255,.08);border-radius:18px;background:rgba(255,255,255,.03);padding:0 18px;margin-bottom:12px}}
    .faq-item summary{{cursor:pointer;list-style:none;padding:18px 0;font-weight:800}}
    .faq-item summary::-webkit-details-marker{{display:none}}
    .faq-answer{{padding:0 0 18px;color:var(--muted);line-height:1.85}}
    .about-layout{{display:grid;grid-template-columns:1fr .92fr;gap:22px;align-items:stretch}}
    .about-copy{{padding:28px}}
    .about-quote{{margin:24px 0 0;padding:18px 20px;border-radius:22px;background:var(--surface);font-weight:800;line-height:1.75}}
    .about-photo{{overflow:hidden;min-height:340px;display:grid;place-items:center}}
    .about-photo img{{width:100%;height:100%;object-fit:cover}}
    .about-photo-fallback{{font-size:72px;background:linear-gradient(135deg,rgba(255,255,255,.03),var(--surface))}}
    .verify-card{{padding:24px 28px;display:flex;align-items:center;justify-content:space-between;gap:18px;background:linear-gradient(135deg,rgba(255,255,255,.03),var(--surface))}}
    .verify-badge{{display:inline-flex;align-items:center;gap:10px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);padding:11px 16px;border-radius:999px;font-weight:900}}
    .contact-card{{padding:30px;display:grid;grid-template-columns:1fr auto;gap:18px;align-items:center}}
    .contact-actions{{display:flex;flex-wrap:wrap;gap:12px;margin-top:18px}}
    .contact-meta{{display:grid;gap:8px;text-align:left}}
    .site-footer{{padding:30px 0 54px;color:var(--muted)}}
    .footer-wrap{{display:flex;justify-content:space-between;gap:16px;align-items:center;border-top:1px solid var(--line);padding-top:24px}}
    .floating-wa,.back-top{{position:fixed;bottom:24px;z-index:45;width:58px;height:58px;border:none;border-radius:18px;display:grid;place-items:center;color:#fff;font-size:24px;box-shadow:0 18px 34px rgba(2,6,23,.32);cursor:pointer}}
    .floating-wa{{right:24px;background:linear-gradient(135deg,#22c55e,#16a34a)}}
    .back-top{{left:24px;background:rgba(15,23,42,.9);border:1px solid rgba(255,255,255,.12)}}
    .reveal{{opacity:0;transform:translateY(18px);transition:opacity .55s ease,transform .55s ease}}
    .reveal.visible{{opacity:1;transform:none}}
    @keyframes rv-scroll{{from{{transform:translateX(0)}}to{{transform:translateX(50%)}}}}
    @keyframes floatY{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(6px)}}}}
    @media (max-width: 1024px){{
      .hero-grid,.detail-layout,.about-layout,.contact-card{{grid-template-columns:1fr}}
      .services-grid,.detail-grid,.why-grid{{grid-template-columns:repeat(2,1fr)}}
      .contact-meta{{text-align:right}}
    }}
    @media (max-width: 760px){{
      .nav-toggle{{display:grid;place-items:center}}
      .site-nav{{position:absolute;top:78px;right:16px;left:16px;display:none;flex-direction:column;align-items:stretch;padding:14px;border-radius:24px;background:rgba(8,14,27,.96);border:1px solid var(--line)}}
      .site-nav.open{{display:flex}}
      .header-phone{{display:none}}
      .hero{{padding-top:64px}}
      .hero-actions{{flex-direction:column;align-items:stretch}}
      .stats-wrap,.services-grid,.detail-grid,.why-grid{{grid-template-columns:1fr}}
      .section-head{{flex-direction:column;align-items:start}}
      .verify-card,.footer-wrap{{flex-direction:column;align-items:start}}
      .floating-wa{{right:16px;bottom:18px}}
      .back-top{{left:16px;bottom:18px}}
    }}
  </style>
</head>
<body>
  {owner_bar}
  <header class="site-header" id="site-header">
    <div class="container header-inner">
      <div class="brand-block">
        <strong>{name}</strong>
        <span>{city or category or business_types or config["eyebrow"]}</span>
      </div>
      <button class="nav-toggle" id="nav-toggle" type="button" aria-label="פתח תפריט">☰</button>
      <nav class="site-nav" id="site-nav">
        <a href="#services">שירותים</a>
        <a href="#reviews">ביקורות</a>
        <a href="#hours">שעות פתיחה</a>
        <a href="#faq">שאלות</a>
        <a href="#contact">יצירת קשר</a>
      </nav>
      {nav_phone}
    </div>
  </header>

  <section class="hero" id="top">
    <div class="container hero-grid">
      <div class="hero-copy">
        {hero_chip}
        <h1>{hero_title}</h1>
        <p>{tagline}</p>
        <div class="hero-meta">
          <span>{config["emoji"]} {config["eyebrow"]}</span>
          {f'<span>📍 {address}</span>' if address else ''}
          {f'<span>🕒 {opening_hours[0]}</span>' if opening_hours else ''}
        </div>
        <div class="hero-actions">
          {call_cta}
          <a class="btn btn-ghost" href="https://wa.me/{wa_phone}?text={quote(f"שלום {name_raw}, אשמח לקבל פרטים נוספים")}" target="_blank" rel="noopener">💬 שלחו WhatsApp</a>
          {maps_cta}
        </div>
        <a class="hero-scroll" href="#services">↓ ממשיכים לשירותים</a>
      </div>
      <aside class="hero-panel reveal">
        <div class="panel-title">
          <strong>מה מקבלים כאן?</strong>
          <span>{config["emoji"]}</span>
        </div>
        <div class="panel-stack">
          <div class="panel-item"><strong>איכות</strong><span>נראות יוקרתית ושפה מקצועית</span></div>
          <div class="panel-item"><strong>קצב</strong><span>תהליך קצר וברור מרגע הפנייה</span></div>
          <div class="panel-item"><strong>אמון</strong><span>הצגת שירות, שעות ופרטי קשר בצורה מלאה</span></div>
        </div>
      </aside>
    </div>
  </section>

  <div class="stats-strip">
    <div class="container stats-wrap">
      {stats_html}
    </div>
  </div>

  <section class="trust-strip">
    <div class="container trust-wrap">
      {trust_badges}
    </div>
  </section>

  <section id="services">
    <div class="container">
      <div class="section-head">
        <div>
          <h2>שירותים מרכזיים עם נראות פרימיום</h2>
        </div>
        <p>עמוד שנבנה כדי להראות מה העסק עושה, איך פונים אליו ולמה הוא נראה כמו הבחירה הבטוחה והיוקרתית באזור.</p>
      </div>
      <div class="services-grid">
        {service_cards}
      </div>
    </div>
  </section>

  <section id="reviews">
    <div class="container">
      <div class="section-head">
        <div>
          <h2>ביקורות שמחזקות אמון</h2>
        </div>
        <p>כרטיסי המלצה שנעים אוטומטית ונותנים תחושת מותג חיה, עדכנית ובטוחה יותר.</p>
      </div>
      <div class="reviews-shell reveal">
        <div class="reviews-track">{review_track}</div>
      </div>
    </div>
  </section>

  <section class="why-band">
    <div class="container">
      <div class="section-head">
        <div>
          <h2>למה בוחרים ב{name}?</h2>
        </div>
        <p>לא רק שירות טוב, אלא גם דרך ברורה לעבוד מול העסק: מהירה, נקייה ומדויקת יותר.</p>
      </div>
      <div class="why-grid">
        {why_cards}
      </div>
    </div>
  </section>

  <section>
    <div class="container detail-layout">
      <div class="detail-copy reveal">
        <div class="section-head">
          <div>
            <h2>{config["detail_title"]}</h2>
          </div>
        </div>
        <p>{config["detail_intro"]}</p>
        <ul>
          <li>שיחת פתיחה או פנייה ראשונית קצרה שמבהירה צורך וזמינות.</li>
          <li>הצגת שירותים מרכזיים בפורמט ברור, עם היררכיה ויזואלית חזקה.</li>
          <li>מסר אמין, מקומי ויוקרתי שמגדיל את הסיכוי לפנייה אמיתית.</li>
        </ul>
      </div>
      <div class="detail-grid">
        {detail_cards}
      </div>
    </div>
  </section>

  <section id="hours">
    <div class="container">
      <div class="section-head">
        <div>
          <h2>שעות פעילות ונקודות זמינות</h2>
        </div>
        <p>כאשר נתוני Google Places זמינים הם מוצגים כאן; אחרת מוצגת תבנית פעילות אופיינית לסוג העסק.</p>
      </div>
      <div class="hours-card reveal">
        <div class="hours-grid">{_hours_rows(opening_hours)}</div>
      </div>
    </div>
  </section>

  <section id="faq">
    <div class="container">
      <div class="section-head">
        <div>
          <h2>שאלות נפוצות</h2>
        </div>
        <p>מבנה FAQ מובנה שעוזר להוריד חסמים עוד לפני הפנייה הראשונה.</p>
      </div>
      <div class="faq-panel">{_faq_html(config["faq"])}</div>
    </div>
  </section>

  <section>
    <div class="container about-layout">
      <article class="about-copy reveal">
        <div class="section-head">
          <div>
            <h2>קצת על {name}</h2>
          </div>
        </div>
        <p>{about_text}</p>
        <div class="about-quote">“{config["about"]}”</div>
      </article>
      {photo_block}
    </div>
  </section>

  <section>
    <div class="container">
      <div class="verify-card reveal">
        <div>
          <div class="verify-badge">✅ עסק זה אומת ונבדק על-ידי tazo-web</div>
          <p>האתר מציג את העסק בצורה חדה, נוחה לפנייה ומוכנה לעדכון שוטף של תוכן, תמונות ומחירים.</p>
        </div>
        {website_cta or f'<a class="btn btn-ghost" href="{claim_url}" target="_blank" rel="noopener">ניהול ועדכון האתר</a>'}
      </div>
    </div>
  </section>

  <section id="contact">
    <div class="container">
      <div class="contact-card reveal">
        <div>
          <div class="section-head">
            <div>
              <h2>מוכנים לשיחה הראשונה?</h2>
            </div>
          </div>
          <p class="contact-meta">כל מה שצריך כדי להפוך עניין לשיחת המשך נמצא כאן: טלפון, WhatsApp, כתובת ומסלול הגעה.</p>
          <div class="contact-actions">
            {call_cta}
            <a class="btn btn-primary" href="https://wa.me/{wa_phone}?text={quote(f"שלום {name_raw}, אשמח לשוחח על השירות")}" target="_blank" rel="noopener">💬 WhatsApp</a>
            {maps_cta}
            {website_cta}
          </div>
        </div>
        <div class="contact-meta">
          {f'<strong>{address}</strong>' if address else ''}
          {f'<span>טלפון: {phone}</span>' if phone else ''}
          {f'<span>קטגוריה: {category}</span>' if category else ''}
          {f'<span>סוגים: {business_types}</span>' if business_types else ''}
          <span>עודכן: {today}</span>
        </div>
      </div>
    </div>
  </section>

  <footer class="site-footer">
    <div class="container footer-wrap">
      <div>
        <strong>{name}</strong>
        <div>{tagline}</div>
      </div>
      <div>© {year} · {city or 'ישראל'}</div>
    </div>
  </footer>

  <a class="floating-wa" href="https://wa.me/{wa_phone}?text={quote(f"שלום {name_raw}, אשמח לקבל פרטים נוספים")}" target="_blank" rel="noopener" aria-label="WhatsApp">💬</a>
  <button class="back-top" id="back-top" type="button" aria-label="חזרה למעלה">↑</button>

  <script>
    const navToggle = document.getElementById('nav-toggle');
    const nav = document.getElementById('site-nav');
    const header = document.getElementById('site-header');
    if (navToggle && nav) {{
      navToggle.addEventListener('click', () => nav.classList.toggle('open'));
      nav.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => nav.classList.remove('open')));
    }}
    window.addEventListener('scroll', () => header.classList.toggle('scrolled', window.scrollY > 12));

    const revealObserver = new IntersectionObserver((entries) => {{
      entries.forEach((entry) => {{
        if (entry.isIntersecting) entry.target.classList.add('visible');
      }});
    }}, {{ threshold: 0.16 }});
    document.querySelectorAll('.reveal').forEach((node) => revealObserver.observe(node));

    const counterObserver = new IntersectionObserver((entries) => {{
      entries.forEach((entry) => {{
        if (!entry.isIntersecting || entry.target.dataset.done === '1') return;
        entry.target.dataset.done = '1';
        const target = Number(entry.target.dataset.target || 0);
        const decimals = Number(entry.target.dataset.decimals || 0);
        const suffix = entry.target.dataset.suffix || '';
        const started = performance.now();
        const duration = 1200;
        const step = (now) => {{
          const progress = Math.min(1, (now - started) / duration);
          const value = target * (1 - Math.pow(1 - progress, 3));
          entry.target.textContent = value.toFixed(decimals) + suffix;
          if (progress < 1) requestAnimationFrame(step);
        }};
        requestAnimationFrame(step);
      }});
    }}, {{ threshold: 0.35 }});
    document.querySelectorAll('[data-counter]').forEach((node) => counterObserver.observe(node));

    const backTop = document.getElementById('back-top');
    if (backTop) backTop.addEventListener('click', () => window.scrollTo({{ top: 0, behavior: 'smooth' }}));
  </script>
</body>
</html>'''


def render_beauty(c: dict, services) -> str:
    return _render_premium_site(c, "beauty", services)


def render_health(c: dict, services) -> str:
    return _render_premium_site(c, "health", services)


def render_vehicles(c: dict, services) -> str:
    return _render_premium_site(c, "vehicles", services)


def render_repairs(c: dict, services) -> str:
    return _render_premium_site(c, "repairs", services)


def render_events(c: dict, services) -> str:
    return _render_premium_site(c, "events", services)


def render_education(c: dict, services) -> str:
    return _render_premium_site(c, "education", services)


def render_generic(c: dict, services=None) -> str:
    return _render_premium_site(c, "professional", services)
