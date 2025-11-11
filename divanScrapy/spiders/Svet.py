# Импортируем необходимые библиотеки для работы паука
import scrapy
import re


class SvetSpider(scrapy.Sider):
    """
    Наш паук для сбора информации об источниках освещения с сайта divan.ru
    Паук - это программа, которая автоматически посещает веб-страницы и собирает с них информацию
    """

    # Имя паука - как мы будем его вызывать в командах
    name = "Svet"

    # Разрешенные домены - сайты, которые паук может посещать
    allowed_domains = ["divan.ru"]

    # Стартовые URL - страницы, с которых паук начнет работу
    start_urls = ["https://www.divan.ru/category/svet"]

    def parse(self, response, **kwargs):
        """
        Главная функция паука, которая обрабатывает страницу и извлекает данные
        Эта функция вызывается автоматически, когда паук загружает страницу
        """

        # Ищем все карточки товаров на странице по специальному атрибуту data-testid
        # CSS-селектор - это способ указать программе, какие элементы на странице нас интересуют
        product_cards = response.css('div[data-testid="product-card"]')

        # Записываем в лог сколько товаров нашли
        # Логгер - это специальный инструмент для записи информации о работе программы
        self.logger.info(f"Найдено карточек товаров: {len(product_cards)}")

        # Проходим по каждой карточке товара в цикле
        # Цикл - это повторение одних и тех же действий для каждого элемента
        for card in product_cards:
            # Извлекаем данные из карточки
            item_data = self.extract_item_data(card)

            # Если получили данные - возвращаем их
            # yield - это специальная команда, которая возвращает данные по одному
            if item_data:
                yield item_data

    def extract_item_data(self, card):
        """
        Извлекает информацию о товаре из одной карточки
        Карточка товара - это блок на странице с информацией об одном товаре
        """
        # Извлекаем цену товара
        # Ищем элемент с атрибутом data-testid="price" и берем его текст
        price_element = card.css('[data-testid="price"]::text')
        price = price_element.get() if price_element else None

        # Извлекаем ссылку на товар
        # Ищем тег <a> и берем значение атрибута href (ссылка)
        url_element = card.css('a::attr(href)')
        url = url_element.get() if url_element else None

        # Если ссылка относительная (не начинается с http), делаем ее полной
        # Относительная ссылка выглядит как "/product/torsher", а полная как "https://divan.ru/product/torsher"
        if url and not url.startswith('http'):
            url = 'https://www.divan.ru' + url

        # Извлекаем название товара
        # Сначала пытаемся извлечь из URL, если не получается - из текста карточки
        name = "Неизвестно"
        if url:
            name_from_url = self.extract_name_from_url(url)
            if name_from_url != "Неизвестно":
                name = name_from_url

        # Если из URL не получилось, ищем название в тексте карточки
        if name == "Неизвестно":
            name_from_card = self.extract_name_from_card(card)
            if name_from_card != "Неизвестно":
                name = name_from_card

        # Создаем словарь с данными о товаре
        # Словарь - это структура данных, которая хранит информацию в виде пар "ключ-значение"
        item_dict = {
            'name': name.strip() if name and name != "Неизвестно" else "Неизвестно",
            'price': price.strip() if price else "Цена не указана",
            'url': url if url else 'Ссылка не найдена'
        }

        return item_dict

    def extract_name_from_url(self, url):
        """
        Извлекает название товара из его URL-адреса
        URL часто содержит название товара в закодированном виде
        """
        try:
            # Ищем в URL часть после "/product/" и до конца или до знака "?"
            # Регулярные выражения - это мощный инструмент для поиска текста по шаблону
            match = re.search(r'/product/([^/?]+)', url)

            if match:
                # Берем найденную часть (slug товара)
                product_slug = match.group(1)

                # Заменяем дефисы на пробелы и делаем каждое слово с заглавной буквы
                # "torsher-ralf-beige" -> "Torsher Ralf Beige"
                name = product_slug.replace('-', ' ').title()

                return name

        except Exception as error:
            # Если произошла ошибка - записываем в лог и продолжаем работу
            self.logger.warning(f"Ошибка при извлечении названия из URL: {error}")

        # Возвращаем "Неизвестно" если ничего не нашли или была ошибка
        return "Неизвестно"

    def extract_name_from_card(self, card):
        """
        Извлекает название товара из текста карточки
        Это запасной способ, если не удалось извлечь название из URL
        """
        try:
            # Получаем весь текст из карточки товара
            all_text_elements = card.css('::text')

            # Создаем пустой список для хранения текстов
            all_texts = []

            # Проходим по всем текстовым элементам и извлекаем текст
            for text_element in all_text_elements:
                text = text_element.get()
                # Проверяем что текст не пустой и не состоит только из пробелов
                if text and text.strip():
                    # Добавляем очищенный текст в список
                    all_texts.append(text.strip())

            # Список текстов, которые не являются названиями (служебная информация)
            excluded_texts = [
                'Купить', 'NEW', 'В наличии',
                'Размеры (ДхШхВ)', 'Размеры (ДхШхВ), см'
            ]

            # Создаем список для хранения осмысленных текстов
            meaningful_texts = []

            # Фильтруем текст: убираем служебную информацию
            for text in all_texts:
                # Пропускаем если текст содержит "руб" (это цена)
                if 'руб' in text.lower():
                    continue

                # Пропускаем если текст в списке исключенных
                if text in excluded_texts:
                    continue

                # Пропускаем если текст содержит размеры (цифры x цифры x цифры)
                if re.search(r'\d+x\d+x\d+', text):
                    continue

                # Пропускаем слишком короткие тексты (менее 10 символов)
                if len(text) < 10:
                    continue

                # Если текст прошел все проверки - добавляем в список
                meaningful_texts.append(text)

            # Если нашли подходящие тексты - находим самый длинный
            if meaningful_texts:
                # Инициализируем переменную для хранения самого длинного текста
                best_name = ""

                # Проходим по всем осмысленным текстам
                for text in meaningful_texts:
                    # Если текущий текст длиннее лучшего - обновляем лучший
                    if len(text) > len(best_name):
                        best_name = text

                return best_name
            else:
                return "Неизвестно"

        except Exception as error:
            # Если произошла ошибка - записываем в лог
            self.logger.warning(f"Ошибка при извлечении названия из карточки: {error}")
            return "Неизвестно"