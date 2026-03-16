import matplotlib.pyplot as plt
import re
from collections import defaultdict


def parse_and_plot(filename):
    # Словарь для хранения списков времен для каждого масштаба
    # { 40.0: [678.03, 656.27, ...], 42.0: [...], ... }
    raw_data = defaultdict(list)

    # Регулярное выражение для парсинга твоей строки
    # Ищет число после "Масштаб:" и число после "Время генерации кадра:"
    pattern = re.compile(r"Масштаб:\s*([0-9\.]+).*Время генерации кадра:\s*([0-9\.]+)")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    scale = float(match.group(1))
                    time_ms = float(match.group(2))
                    raw_data[scale].append(time_ms)
    except FileNotFoundError:
        print(f"Ошибка: Файл {filename} не найден! Создайте его и вставьте туда логи.")
        return

    if not raw_data:
        print("Данные не найдены. Проверьте формат строк в файле.")
        return

    # Усредняем данные и сортируем по масштабу
    sorted_scales = sorted(raw_data.keys())
    avg_times = []

    for scale in sorted_scales:
        times = raw_data[scale]
        avg_time = sum(times) / len(times)
        avg_times.append(avg_time)

    # --- ПОСТРОЕНИЕ ГРАФИКА ---
    plt.figure(figsize=(10, 6))

    # Основная линия
    plt.plot(sorted_scales, avg_times, marker='o', linestyle='-', color='#2b579a', linewidth=2, markersize=5,
             label='Среднее время генерации адра')

    # Сетка
    plt.grid(True, which='both', linestyle='--', alpha=0.7)

    # Подписи
    plt.title('Зависимость времени генерации кадра от коэффициента масштабирования', fontsize=14, pad=15)
    plt.xlabel('Коэффициент масштабирования', fontsize=12)
    plt.ylabel('Время генерации кадра (мс)', fontsize=12)

    # Находим пик для аннотации
    max_time = max(avg_times)
    max_scale_index = avg_times.index(max_time)
    max_scale = sorted_scales[max_scale_index]

    plt.legend(loc='lower right')

    # Сохранение
    output_filename = 'research_graph.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"График успешно построен и сохранен в {output_filename}")
    plt.show()


if __name__ == "__main__":
    # Имя файла с логами
    parse_and_plot('measurements.txt')