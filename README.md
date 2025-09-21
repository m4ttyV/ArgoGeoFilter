# ArgoGeoFilter — конвертация Argo NetCDF → CSV с расчётом глубины

Скрипт обрабатывает **Argo NetCDF**-файлы и формирует CSV-выгрузки по датам измерений.
Глубина каждой точки рассчитывается из **давления и широты** по стандарту **TEOS-10** (`gsw.z_from_p`).

## Что делает скрипт

* Открывает `.nc` файл (Argo профиль) с помощью **xarray**
* Фильтрует пункты по:

  * временного окна (`--days_ago`)
  * географическим границам (`--min_lon/--max_lon/--min_lat/--max_lat`)
* Для каждой точки рассчитывает **глубину** `getDepth(pres, lat)`
  (используется `gsw.z_from_p`, возвращаем положительную глубину в метрах)
* Преобразует долготу к диапазону **\[0, 360)** (если входное `lon < 0`)
* Формирует CSV-файлы **по датам наблюдений** (`YYYY-MM-DD.csv`)
* Ведёт журнал уже обработанных файлов `processed_files.log`, чтобы не повторяться

## Зависимости

* Python 3.9+
* `numpy`
* `xarray`
* `gsw` (GSW-Oceanographic Toolbox, реализация TEOS-10)
* (рекомендуется) `netCDF4` или `h5netcdf` как backend для xarray

Установка:

```bash
pip install numpy xarray gsw netCDF4
```

## Входные данные

Скрипт ожидает, что в NetCDF присутствуют переменные:

* `LONGITUDE`, `LATITUDE`
* `TEMP`, `PRES`, `PSAL`
* `JULD` (дата/время)
* `PLATFORM_NUMBER`, `CYCLE_NUMBER`

## Выходные данные

В каталоге `output_dir` создаются файлы вида:

```
YYYY-MM-DD.csv
```

Разделитель `;`, кодировка `utf-8-sig`. Заголовок:

```
Platform_number;Cycle number;Latitude;Longitude;Datetime;Depth;Pressure;Temperature;Salinity
```

Поля:

* **Platform\_number** — из `PLATFORM_NUMBER`
* **Cycle number** — из `CYCLE_NUMBER`
* **Latitude / Longitude** — из `LATITUDE`/`LONGITUDE` (долгота приведена к \[0,360))
* **Datetime** — из `JULD` (строка `YYYY-MM-DDThh:mm:ss`)
* **Depth** — расчёт `gsw.z_from_p(pres, lat)` (м, положительное вниз)
* **Pressure / Temperature / Salinity** — из `PRES`/`TEMP`/`PSAL`
  (числа форматируются с точностью 0.001; если значение отсутствует — пропускается запись)

## Как это работает (коротко о методе глубины)

Глубина переводится из давления с учётом широты по **TEOS-10**:

* уравнение гидростатики $dp/dz = \rho g$
* в стандарте есть готовая функция **`gsw.z_from_p(pressure_dbar, latitude_deg)`**,
  которая учитывает изменение $g$ с широтой и сжимаемость водной массы.
* Функция возвращает отрицательную глубину (ниже поверхности) — скрипт меняет знак.

> Источники: TEOS-10 Manual; GSW-Python (`gsw.z_from_p`).

## Использование

### CLI (аргументы)

```bash
python main.py \
  --input_dir "PATH/TO/NETCDF_DIR" \
  --output_dir "./output" \
  --min_lon -180 --max_lon 180 \
  --min_lat -90  --max_lat 90 \
  --days_ago 120
```

Параметры:

* `--input_dir, -i` — директория с `.nc` файлами
* `--output_dir, -o` — директория для CSV (по умолчанию `./`)
* `--min_lon, -min_l` / `--max_lon, -max_l` — диапазон долгот (по умолчанию `-180..180`)
* `--min_lat, -min_lat` / `--max_lat, -max_lat` — диапазон широт (по умолчанию `-90..90`)
* `--days_ago, -d` — включать только записи с `JULD >= today - days_ago` (по умолчанию `120`)

### Логирование обработанных файлов

Список уже обработанных `.nc` хранится в `processed_files.log` рядом со скриптом.
При повторном запуске файлы из этого списка пропускаются.

## Структура основных функций

* `getDepth(pres, lat)` → `float`
  Возвращает глубину (м) из давления `pres` (дбар) и широты `lat` (°) через `gsw.z_from_p`.

* `Record(...)`
  Контейнер для одной строки результата с нормализацией значений.

* `csv_gen(output_dir, finish_dict)`
  Создаёт/дополняет CSV-файлы по датам, записывает строки.

* `process_file(input_filename, output_path, ..., days_ago=60)`
  Читает NetCDF, фильтрует, считает глубины, собирает `finish_dict`, вызывает `csv_gen`.

## Примеры

Обработка всех `.nc` в каталоге:

```bash
python main.py -i ./data/DR -o ./output/DR -d 90
```

Только Северная Атлантика:

```bash
python main.py -i ./data -o ./out --min_lat 0 --max_lat 70 --min_lon -80 --max_lon 20
```

## Частые вопросы / проблемы

* **`gsw` не ставится / ImportError**
  Установите билд-инструменты (Linux: `build-essential`; Windows: Microsoft C++ Build Tools)
  и попробуйте:

  ```bash
  pip install --upgrade pip setuptools wheel
  pip install gsw
  ```

* **`xarray` не открывает NetCDF**
  Установите один из backend-драйверов:

  ```bash
  pip install netCDF4
  # или
  pip install h5netcdf
  ```

* **Координаты некорректны (долгота > 180)**
  Скрипт намеренно переводит долготу к \[0, 360). Если нужен диапазон \[-180, 180], уберите/измените логику:

  ```python
  if lon < 0: lon += 360
  ```

## Точность и оговорки

* Расчёт глубины опирается на TEOS-10; ошибок порядка **0.1–0.3%** в верхнем километре обычно достаточно для задач разметки данных.
* Глубина рассчитывается **по точке** (p,lat) без использования профиля T/S (что соответствует стандартному `p→z` в потоках ARGO/CTD).
* Поля `TEMP/PSAL/PRES` могут содержать NaN; такие строки отбрасываются (если все три NaN).


## Благодарности

* **TEOS-10 / GSW-Python** за реализацию океанографических формул.
* Проект **Argo** за открытые океанографические данные.

