import scrapy
import re


class SvetSpider(scrapy.Spider):
    name = "Svet"
    allowed_domains = ["divan.ru"]
    start_urls = ["https://www.divan.ru/category/svet"]

    def parse(self, response):
        product_cards = response.css('div[data-testid="product-card"]')

        print(f"Найдено карточек товаров: {len(product_cards)}")

        for card in product_cards:
            # Извлекаем цену
            price = card.css('[data-testid="price"]::text').get()

            # Извлекаем ссылку
            url = card.css('a::attr(href)').get()
            if url and not url.startswith('http'):
                url = 'https://www.divan.ru' + url

            # Улучшенное извлечение названия из URL
            name = "Неизвестно"
            if url:
                # Из URL типа /product/torsher-ralf-beige извлекаем название
                match = re.search(r'/product/(.+)', url)
                if match:
                    product_slug = match.group(1)
                    # Преобразуем slug в читаемое название
                    name = product_slug.replace('-', ' ').title()
                    # Исправляем возможные ошибки в транслитерации
                    name = re.sub(r'\b(\w+)', lambda m: m.group(1).capitalize(), name)

            # Дополнительная проверка - если название слишком короткое, ищем в тексте
            if len(name) < 10:
                all_texts = card.css('::text').getall()
                clean_texts = [text.strip() for text in all_texts if text.strip()]

                # Ищем осмысленные длинные тексты (это не цены и не кнопки)
                meaningful_texts = [
                    text for text in clean_texts
                    if 'руб' not in text.lower()
                       and text not in ['Купить', 'NEW', 'В наличии', 'Размеры (ДхШхВ)', 'Размеры (ДхШхВ), см']
                       and not re.search(r'\d+x\d+x\d+', text)  # Убираем размеры
                       and len(text) > 10  # Название обычно длинное
                ]

                if meaningful_texts:
                    name = meaningful_texts[0]

            yield {
                'name': name,
                'price': price.strip() if price else "Цена не указана",
                'url': url if url else 'Ссылка не найдена'
            }