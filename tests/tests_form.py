import asyncio
from services.forms import YandexForms
from config import config

from pprint import pprint

survey = config.TEST_FORM_ID

answers = {
    "answer_choices_136023": ["237802"],
    "answer_choices_136025": ["240975"],
    "answer_choices_136028": ["237808"],
    "answer_choices_136031": ["237817"],
    "answer_choices_136032": [
        "237819",
        "237820",
        "237825",
        "237827",
        "237831"
    ],
    "answer_short_text_136037": "Какой-то текст"
}


async def test_get_form_data():
    form_client = YandexForms()
    try:
        data = await form_client.get_form_data(survey)
        pprint(data)
        assert data is not None
        return True
    except Exception as e:
        print(f"Ошибка при получении данных формы: {e}")
        return False


async def test_fill_form():
    form_client = YandexForms()
    try:
        result = await form_client.fill_the_form(survey, answers)
        print("Успешно отправлено:", result)
        assert result is True
        return True
    except Exception as e:
        print(f"Ошибка при отправке ответов: {e}")
        return False


async def test_export_results_detailed():
    """Детальный тест экспорта с отладкой каждого шага"""
    form_client = YandexForms()

    print("🔍 Детальная отладка экспорта:")
    print("=" * 40)

    try:
        print("1. Запуск экспорта...")
        operation_id = await form_client._start_export(survey, 'csv')
        print(f"   Operation ID: {type(operation_id)}")

        if not operation_id:
            print("   ❌ Не удалось получить operation_id")
            return False

        print("2. Ожидание завершения экспорта...")
        finished = False
        attempts = 0
        max_attempts = 10000

        while not finished and attempts < max_attempts:
            attempts += 1
            finished = await form_client._check_finished(operation_id)
            print(f"   Попытка {attempts}: статус {'готово' if finished else 'в процессе'}")

            if not finished:
                await asyncio.sleep(2)

        if not finished:
            print("   ❌ Экспорт не завершился за отведенное время")
            return False

        print("3. Получение результата...")
        result = await form_client._get_result(survey, operation_id)
        print(f"   Размер результата: {len(result) if result else 0} байт")

        if result:
            # with open('export_debug.csv', 'wb') as f:
            #     f.write(result)
            # print("   ✓ Результат сохранен в export_debug.csv")
            try:
                preview = result.decode('utf-8')[:500]
                print(f"   Превью результата:\n{preview}")
            except:
                print("   Не удалось декодировать результат как UTF-8")

            return True
        else:
            print("   ❌ Результат экспорта пустой")
            return False

    except Exception as e:
        print(f"   ❌ Ошибка при экспорте: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_tests():
    print("Запуск тестов...")
    tests = [
        test_get_form_data(),
        # test_fill_form(),
        # test_export_results_detailed()
    ]

    results = await asyncio.gather(*tests)
    if all(results):
        print("Все тесты пройдены успешно!")
    else:
        print("Некоторые тесты не прошли")


asyncio.run(run_tests())
