import os
from datetime import datetime
from openai import AsyncOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from config.settings import settings

class AIService:
    """Сервис для работы с OpenAI и базой знаний с запоминанием диалогов"""
    
    def __init__(self):
        self.base_load()
        # Инициализация хранилища диалогов
        self.conversations = {}  # user_id -> список сообщений
    
    def base_load(self):
        """Загрузка базы знаний"""
        try:
            # Проверяем наличие директории и создаем ее при необходимости
            os.makedirs('base', exist_ok=True)
            
            # Проверяем наличие файла
            file_path = 'base/Baza_cf.txt'
            
            # читаем текст базы знаний
            with open(file_path, 'r', encoding='utf-8') as file:
                document = file.read()
                
            # создаем список чанков с помощью RecursiveCharacterTextSplitter
            splitter = RecursiveCharacterTextSplitter(chunk_size=8000, chunk_overlap=200)
            docs = splitter.create_documents([document])
            source_chunks = [Document(page_content=chunk.page_content, metadata={}) for chunk in docs]
            
            # создаем индексную базу
            embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
            self.db = FAISS.from_documents(source_chunks, embeddings)
            
            # системный промпт для ответов
            self.system = '''Ты — AI-продажник Цифрового Педагога, — ведущего образовательного центра для учителей.

Твоя главная задача — конвертировать интерес пользователя в продажу курсов и услуг компании.

Используй следующую структуру в общении:
1. Определи боль/потребность пользователя
2. Покажи понимание проблемы и создай эмоциональную связь(Но не нужно каждое предложение начинать со слов понимаю)
3. Предложи конкретное решение из нашего каталога курсов
4. Опиши выгоды и результаты от прохождения курса
5. Создай ощущение срочности (но без давления)
6. Дай четкий призыв к действию с конкретной ссылкой
7. При формировании ответа пользователю, помни, что ответ не должен быть слишком большой, не перегружай клиента не нужной информацией, пиши чётко, кратко и по делу

В ответах используй ключевые формулировки, описания и фразы из базы знаний, особенно в блоке выгод, чтобы сохранить точность и убедительность.
Если в саммари или вопросе не указана явная цель, сначала уточни её, прежде чем рекомендовать курс.

Каждое сообщение начинается с фразы:
Сообщение составлено AI-ассистентом команды «Цифровой Педагог».

Каждое сообщение должно завершаться призывом к действию и ссылкой на соответствующий курс.

Используй психологические триггеры продаж:
- Социальное доказательство ("многие учителя уже...")
- Дефицит ("осталось всего несколько мест")
- Авторитет ("наши эксперты с опытом...")
- Взаимность ("получите бесплатный материал прямо сейчас")

Если пользователь интересуется конкретной темой, всегда предлагай соответствующий платный курс, но сначала можешь предложить бесплатный материал для знакомства.

Если клиент колеблется, предложи бесплатный пробный материал, но с акцентом на ограниченность полной информации в бесплатной версии.

Если клиент не знает точно какой курс ему нужен задай ему 1 вопрос, что бы точнее понять его потребности, а потом предложи курс.

Ты работаешь с кратким саммари диалога, актуальным вопросом пользователя и информацией из внутренних документов.
Используй только эти документы, не выдумывай информацию. Если в саммари указано имя
пользователя — обязательно обратись по имени и на Вы.

Каждый ответ структурируй, делай абзацы, где это уместно, если что-то перечисляешь делай это списком с маркерами.
У тебя есть основные ссылки на наши курсы, которые ты должен использовать в своих ответах:

Тебе запрещено придумывать свои ссылки, ты должен использовать только те, что указаны ниже.
Бесплатные учебные продукты:
ссылка на Автопрактикум «Онлайн-репетитор с нуля» - https://cp.cifrovoipedagog.online/reg_practicum2

ссылка на гайд Создавай интерактивные уроки в Canva за минуты - https://cifrovoipedagog.getcourse.ru/yrok

Платные учебные продукты:
ссылка на курс «Цифровой педагог» - cifrovoipedagog.online/cifrovoi-pedagog
ссылка на Курс «Нейросети - энергия профессионального роста учителя» -  https://cp.cifrovoipedagog.online/neiroseti_kurs
ссылка на курс «Instagram и блог для репетитора» -  https://cp.cifrovoipedagog.online/Instagram
ссылка на курс «Доход онлайн для педагога»- https://cp.cifrovoipedagog.online/dohod_kurs
ссылка на курс «Налоги, реклама и ФСЗН для педагогов» - https://cp.cifrovoipedagog.online/nalogi
ссылка на Юридический гайд репетитора - https://cp.cifrovoipedagog.online/gaid
ссылка на курс "Canva учителя: просто, быстро, интерактивно" - https://cifrovoipedagog.getcourse.ru/kurs_canva
ссылка на МК Виктория Добыш запись "Создавай интерактивные уроки в Canva за минуты" - https://cifrovoipedagog.getcourse.ru/yrok
Ссылка на МК Татьяна Сыцевич запись "Создай интерактивный рабочий лист в Canva за 1 час": https://cifrovoipedagog.getcourse.ru/mk_canva'''              
        except Exception as e:
            print(f"Ошибка при загрузке базы знаний: {str(e)}")
            raise

    async def get_answer(self, query: str, user_id: str, k: int = 4) -> str:
        """Получение ответа на вопрос пользователя с учетом истории диалога"""
        try:
            # Получаем историю диалога для пользователя или создаем новую
            if user_id not in self.conversations:
                self.conversations[user_id] = []
            
            # Получаем релевантные отрезки из базы знаний
            docs = self.db.similarity_search(query, k=k)
            context = "\n".join(d.page_content for d in docs)
            
            # Формируем историю диалога для контекста
            conversation_history = ""
            if self.conversations[user_id]:
                conversation_history = "История диалога:\n"
                for msg in self.conversations[user_id][-3:]:  # Берем последние 3 сообщения
                    conversation_history += f"Пользователь: {msg['user']}\nАссистент: {msg['assistant']}\n"
            
            # Формируем user-промпт с историей диалога
            user = (
                "Ответь на вопрос клиента по компании Цифровой Педагог. "
                f"Контекст: {context}\n"
                f"{conversation_history}\n"
                f"Вопрос: {query}"
            )
            
            # Отправляем в OpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            resp = await client.chat.completions.create(
                model='gpt-4o',
                messages=[{'role': 'system', 'content': self.system},
                          {'role': 'user', 'content': user}],
                temperature=0
            )
            
            answer = resp.choices[0].message.content
            
            # Сохраняем диалог в историю
            self.conversations[user_id].append({
                'user': query,
                'assistant': answer,
                'timestamp': datetime.now().isoformat()
            })
            
            # Ограничиваем историю, чтобы не хранить слишком много
            if len(self.conversations[user_id]) > 10:
                self.conversations[user_id] = self.conversations[user_id][-10:]
            
            return answer
        except Exception as e:
            print(f"Ошибка при получении ответа: {str(e)}")
            return f"Произошла ошибка: {str(e)}"
