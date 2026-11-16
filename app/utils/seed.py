from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.database.repositories.category import CategoryRepository

INITIAL_CATEGORIES = [
    {
        "slug": "programming",
        "name_en": "Programming",
        "name_ru": "Программирование",
        "name_uz": "Dasturlash",
        "name_tr": "Programlama",
        "name_ar": "البرمجة",
        "name_de": "Programmierung",
        "name_fr": "Programmation",
        "name_es": "Programación",
        "icon": "💻",
        "is_textbook": False
    },
    {
        "slug": "computer-science",
        "name_en": "Computer Science",
        "name_ru": "Информатика и Computer Science",
        "name_uz": "Kompyuter fanlari",
        "name_tr": "Bilgisayar Bilimi",
        "name_ar": "علوم الحاسوب",
        "name_de": "Informatik",
        "name_fr": "Informatique",
        "name_es": "Ciencias de la Computación",
        "icon": "🖥️",
        "is_textbook": False
    },
    {
        "slug": "mathematics",
        "name_en": "Mathematics",
        "name_ru": "Математика",
        "name_uz": "Matematika",
        "name_tr": "Matematik",
        "name_ar": "الرياضيات",
        "name_de": "Mathematik",
        "name_fr": "Mathématiques",
        "name_es": "Matemáticas",
        "icon": "📐",
        "is_textbook": False
    },
    {
        "slug": "physics",
        "name_en": "Physics",
        "name_ru": "Физика",
        "name_uz": "Fizika",
        "name_tr": "Fizik",
        "name_ar": "الفيزياء",
        "name_de": "Physik",
        "name_fr": "Physique",
        "name_es": "Física",
        "icon": "⚛️",
        "is_textbook": False
    },
    {
        "slug": "chemistry",
        "name_en": "Chemistry",
        "name_ru": "Химия",
        "name_uz": "Kimyo",
        "name_tr": "Kimya",
        "name_ar": "الكيمياء",
        "name_de": "Chemie",
        "name_fr": "Chimie",
        "name_es": "Química",
        "icon": "🧪",
        "is_textbook": False
    },
    {
        "slug": "biology",
        "name_en": "Biology",
        "name_ru": "Биология",
        "name_uz": "Biologiya",
        "name_tr": "Biyoloji",
        "name_ar": "علم الأحياء",
        "name_de": "Biologie",
        "name_fr": "Biologie",
        "name_es": "Biología",
        "icon": "🧬",
        "is_textbook": False
    },
    {
        "slug": "medicine",
        "name_en": "Medicine",
        "name_ru": "Медицина",
        "name_uz": "Tibbiyot",
        "name_tr": "Tıp",
        "name_ar": "الطب",
        "name_de": "Medizin",
        "name_fr": "Médecine",
        "name_es": "Medicina",
        "icon": "🩺",
        "is_textbook": False
    },
    {
        "slug": "business",
        "name_en": "Business",
        "name_ru": "Бизнес и Менеджмент",
        "name_uz": "Biznes va Menejment",
        "name_tr": "İş Dünyası",
        "name_ar": "إدارة الأعمال",
        "name_de": "Wirtschaft",
        "name_fr": "Gestion & Affaires",
        "name_es": "Negocios",
        "icon": "💼",
        "is_textbook": False
    },
    {
        "slug": "economics",
        "name_en": "Economics",
        "name_ru": "Экономика",
        "name_uz": "Iqtisodiyot",
        "name_tr": "Ekonomi",
        "name_ar": "الاقتصاد",
        "name_de": "Volkswirtschaft",
        "name_fr": "Économie",
        "name_es": "Economía",
        "icon": "📊",
        "is_textbook": False
    },
    {
        "slug": "history",
        "name_en": "History",
        "name_ru": "История",
        "name_uz": "Tarix",
        "name_tr": "Tarih",
        "name_ar": "التاريخ",
        "name_de": "Geschichte",
        "name_fr": "Histoire",
        "name_es": "Historia",
        "icon": "🏛️",
        "is_textbook": False
    },
    {
        "slug": "philosophy",
        "name_en": "Philosophy",
        "name_ru": "Философия",
        "name_uz": "Falsafa",
        "name_tr": "Felsefe",
        "name_ar": "الفلسفة",
        "name_de": "Philosophie",
        "name_fr": "Philosophie",
        "name_es": "Filosofía",
        "icon": "📜",
        "is_textbook": False
    },
    {
        "slug": "literature",
        "name_en": "Literature",
        "name_ru": "Художественная литература",
        "name_uz": "Badiiy adabiyot",
        "name_tr": "Edebiyat",
        "name_ar": "الأدب والروايات",
        "name_de": "Literatur",
        "name_fr": "Littérature",
        "name_es": "Literatura",
        "icon": "📖",
        "is_textbook": False
    },
    {
        "slug": "languages",
        "name_en": "Languages & Linguistics",
        "name_ru": "Языки и лингвистика",
        "name_uz": "Tillar va Tilshunoslik",
        "name_tr": "Diller ve Dilbilim",
        "name_ar": "اللغات واللسانيات",
        "name_de": "Sprachen & Linguistik",
        "name_fr": "Langues & Linguistique",
        "name_es": "Idiomas y Lingüística",
        "icon": "🌍",
        "is_textbook": False
    },
    {
        "slug": "engineering",
        "name_en": "Engineering",
        "name_ru": "Инженерия и Технологии",
        "name_uz": "Muhandislik",
        "name_tr": "Mühendislik",
        "name_ar": "الهندسة",
        "name_de": "Ingenieurwesen",
        "name_fr": "Ingénierie",
        "name_es": "Ingeniería",
        "icon": "⚙️",
        "is_textbook": False
    },
    {
        "slug": "school-textbooks",
        "name_en": "School Textbooks",
        "name_ru": "Школьные учебники",
        "name_uz": "Maktab darsliklari",
        "name_tr": "Okul Ders Kitapları",
        "name_ar": "الكتب المدرسية",
        "name_de": "Schulbücher",
        "name_fr": "Manuels scolaires",
        "name_es": "Libros Escolares",
        "icon": "🎒",
        "is_textbook": True
    },
    {
        "slug": "university-textbooks",
        "name_en": "University Textbooks",
        "name_ru": "Университетские учебники",
        "name_uz": "Universitet darsliklari",
        "name_tr": "Üniversite Ders Kitapları",
        "name_ar": "المناهج الجامعية",
        "name_de": "Universitätslehrbücher",
        "name_fr": "Manuels universitaires",
        "name_es": "Libros Universitarios",
        "icon": "🎓",
        "is_textbook": True
    },
    {
        "slug": "exam-preparation",
        "name_en": "Exam Preparation",
        "name_ru": "Подготовка к экзаменам",
        "name_uz": "Imtihonlarga tayyorgarlik",
        "name_tr": "Sınav Hazırlık",
        "name_ar": "التحضير للاختبارات",
        "name_de": "Prüfungsvorbereitung",
        "name_fr": "Préparation aux examens",
        "name_es": "Preparación de Exámenes",
        "icon": "📝",
        "is_textbook": True
    }
]


async def seed_categories(session: AsyncSession) -> None:
    """Seed initial categories if database is empty."""
    repo = CategoryRepository(session)
    existing = await repo.get_all(only_active=False)
    if existing:
        return

    logger.info("Seeding initial book and textbook categories...")
    for cat_data in INITIAL_CATEGORIES:
        await repo.create(**cat_data)
    await session.commit()
    logger.info(f"Successfully seeded {len(INITIAL_CATEGORIES)} categories.")
