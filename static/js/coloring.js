<script>
    console.log("Скрипт запущен.");
    document.addEventListener('DOMContentLoaded', function() {
     console.log("Скрипт запущен2.");
        const attempts = {{ number_of_attempts|tojson }}; // Словарь с количеством попыток
        const rightAttempts = {{ number_of_right_attempts|tojson }}; // Словарь с успешными попытками
        const columns = document.querySelectorAll('.table tbody tr'); // Получаем все строки таблицы

        // Предположим, что у нас есть некий способ определения количества столбцов
        const numberOfColumns = Object.keys(attempts).length; // Количество столбцов, равное количеству ключей в словаре

        for (let colIndex = 1; colIndex <= numberOfColumns; colIndex++) {
            const totalAttempts = attempts[colIndex] || 0; // Получаем общее количество попыток
            const successfulAttempts = rightAttempts[colIndex] || 0; // Получаем количество успешных попыток

            if (totalAttempts > 0) {
                const successRate = (successfulAttempts / totalAttempts) * 100;
                let columnClass;

                if (successRate >= 85) {
                    columnClass = 'col-green';
                } else if (successRate >= 75) {
                    columnClass = 'col-light-green';
                } else if (successRate >= 65) {
                    columnClass = 'col-yellow';
                } else {
                    columnClass = 'col-red';
                }

                // Применяем класс к каждой ячейке в столбце
                columns.forEach(row => {
                    const cell = row.cells[colIndex]; // Получаем ячейку по индексу столбца
                    if (cell) {
                        cell.classList.add(columnClass); // Добавляем соответствующий класс
                    }
                });
            }
        }
    });
</script>