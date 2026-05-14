import argparse
import csv
import os
from os import mkdir
import datetime
import numpy as np
import xarray as xr


def seawater_density_unesco(salinity, temperature, pressure):
    """
    Расчет плотности морской воды по уравнению UNESCO 1981
    """
    # Константы
    a0 = 999.842594
    a1 = 6.793952e-2
    a2 = -9.095290e-3
    a3 = 1.001685e-4
    a4 = -1.120083e-6
    a5 = 6.536332e-9

    b0 = 8.24493e-1
    b1 = -4.0899e-3
    b2 = 7.6438e-5
    b3 = -8.2467e-7
    b4 = 5.3875e-9

    c0 = -5.72466e-3
    c1 = 1.0227e-4
    c2 = -1.6546e-6

    d0 = 4.8314e-4

    # Плотность чистой воды при атмосферном давлении
    t = temperature
    rho_w = a0 + a1 * t + a2 * t ** 2 + a3 * t ** 3 + a4 * t ** 4 + a5 * t ** 5

    # Поправка на соленость при атмосферном давлении
    s = salinity
    rho_0 = (rho_w +
             (b0 + b1 * t + b2 * t ** 2 + b3 * t ** 3 + b4 * t ** 4) * s +
             (c0 + c1 * t + c2 * t ** 2) * s ** 1.5 +
             d0 * s ** 2)

    # Сжимаемость (поправка на давление)
    p = pressure  # в барах
    k0 = 19652.21 + 148.4206 * t - 2.327105 * t ** 2 + 1.360477e-2 * t ** 3 - 5.155288e-5 * t ** 4
    k1 = 54.6746 - 0.603459 * t + 1.09987e-2 * t ** 2 - 6.1670e-5 * t ** 3
    k2 = 7.944e-2 + 1.6483e-2 * t - 5.3009e-4 * t ** 2

    k = (k0 + k1 * s + k2 * s ** 1.5 +
         (3.239908 + 1.43713e-3 * t + 1.16092e-4 * t ** 2 - 5.77905e-7 * t ** 3) * p +
         (2.2838e-3 - 1.0981e-5 * t - 1.6078e-6 * t ** 2) * p * s +
         (1.91075e-4) * p * s ** 1.5 +
         (8.50935e-5 - 6.12293e-6 * t + 5.2787e-8 * t ** 2) * p ** 2 +
         (-9.9348e-7 + 2.0816e-8 * t + 9.1697e-10 * t ** 2) * p ** 2 * s)

    # Плотность при заданном давлении
    rho = rho_0 / (1 - p / k)

    return rho

def getDepth_iter(pressure, salinity, temperature, last_depth, prev_pressure, latitude):
    # Переделать. Заходить с вертикальными профилями (передавать массив) находим на каждом уровне плотность. Идем по уровням и находим плотности, где все значения присутствуют.
    # Для самой верхней точки находим глубину по имеющейся формуле. Далее мы определяем глубину слоя и суммируем
    """
      Расчет глубины с учетом плотности, зависящей от T, S, P
    """
    lat_rad = np.radians(latitude)
    g = 9.780318 * (1 + 0.0053024 * np.sin(lat_rad) ** 2
                    - 0.0000058 * np.sin(2 * lat_rad) ** 2)
    # Рассчитываем плотность
    rho = seawater_density_unesco(salinity, temperature, pressure)
    delta_depth = (pressure - prev_pressure) * 10000 / (rho * g)

    result = delta_depth + last_depth
    return result

class Record:
    """
        The Record field for final_dict (description of the fields - names of relevant fields from netCDF files)
        Args:
            lat: LONGITUDE.
            lon: LATITUDE.
            depth: calculated by getDepth() function.
            temp: TEMP.
            pres: PRES.
            psal: PSAL.
            date: JULD
            platform_number: PLATFORM_NUMBER.
            cycle_number: CYCLE_NUMBER.
    """
    def __init__(self, lat, lon, depth, temp, pres, psal, dt, platform_number, cycle_number):
        self.lat = lat
        if lon < 0:
            lon += 360
        self.lon = lon
        if np.isnan(depth):
            depth = "None"
        self.depth = depth
        if np.isnan(temp):
            temp = "None"
        self.temp = temp
        if np.isnan(pres):
            pres = "None"
        self.pres = pres
        if np.isnan(psal):
            psal = "None"
        self.psal = psal
        self.dt = dt
        self.platform_number = str(platform_number).strip('b').strip('\'')
        self.cycle_number = cycle_number

def csv_gen(filedir, finish_dict):
    """
        Generate csv file with output data from "finish_dict".

        Args:
            filedir (str): Path to the .nc file.
            finish_dict: Dictionary of finished records.

        Returns:
            Generate CSV-file with output data.
    """
    current_dt = datetime.datetime.now()
    year = current_dt.strftime("%Y")
    month = current_dt.strftime("%m")

    output_dir = os.path.join(filedir, year, month)
    os.makedirs(output_dir, exist_ok=True)

    for dates in finish_dict:
        file_path = os.path.join(output_dir, dates + ".csv")

        file_exists = os.path.exists(file_path)

        with open(file_path, 'a', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')

            if not file_exists:
                writer.writerow([
                    "Platform_number",
                    "Cycle number",
                    "Latitude",
                    "Longitude",
                    "Datetime",
                    "Depth",
                    "Pressure",
                    "Temperature",
                    "Salinity"
                ])

            for item in finish_dict[dates]:
                lat, lon, depth, temp, pres, sal, record_datetime, platform_number = \
                    99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999

                if item.lat != "None":
                    lat = "{0:.3f}".format(item.lat)

                if item.lon != "None":
                    lon = "{0:.3f}".format(item.lon)

                if item.depth != "None":
                    depth = "{0:.3f}".format(item.depth)

                if item.temp != "None":
                    temp = "{0:.3f}".format(item.temp)

                if item.pres != "None":
                    pres = "{0:.3f}".format(item.pres)

                if item.psal != "None":
                    sal = "{0:.3f}".format(item.psal)

                record_datetime = item.dt
                platform_number = item.platform_number
                cycle_number = item.cycle_number

                if temp == 99999 and pres == 99999 and sal == 99999:
                    continue

                writer.writerow([
                    platform_number,
                    cycle_number,
                    lat,
                    lon,
                    record_datetime,
                    depth,
                    pres,
                    temp,
                    sal
                ])

def get_file_datetime(file_path: str) -> datetime.datetime:
    """
    Возвращает дату файла для фильтрации.

    Сначала пытается взять дату из имени Argo-файла формата
    DYYYYMMDD_... или RYYYYMMDD_..., например D20260506_prof_1.nc.
    Это стабильнее для Linux, чем os.path.getctime().

    Если дата из имени не распознана, используется дата последнего
    изменения файла.
    """
    base_name = os.path.basename(file_path)

    if len(base_name) >= 9 and base_name[0] in {"D", "R"}:
        date_part = base_name[1:9]
        try:
            return datetime.datetime.strptime(date_part, "%Y%m%d")
        except ValueError:
            pass

    return datetime.datetime.fromtimestamp(os.path.getmtime(file_path))


def is_file_recent(file_path: str, max_age_days: int = 14) -> bool:
    """
    Проверяет, что дата файла отличается от текущей даты
    не больше чем на max_age_days дней.
    """
    file_dt = get_file_datetime(file_path)
    current_dt = datetime.datetime.now()
    return abs(current_dt - file_dt) <= datetime.timedelta(days=max_age_days)

def get_numeric_values(ds: xr.Dataset, var_name: str, prefer_adjusted: bool = True):
    """
    Возвращает числовой массив переменной.

    Если prefer_adjusted=True и в Argo-файле есть VAR_ADJUSTED, то берём
    скорректированные значения. Там, где они отсутствуют/NaN, подставляем
    исходную переменную VAR.
    """
    raw = ds[var_name].values
    adjusted_name = f"{var_name}_ADJUSTED"

    if prefer_adjusted and adjusted_name in ds:
        adjusted = ds[adjusted_name].values
        if np.issubdtype(adjusted.dtype, np.number):
            return np.where(np.isfinite(adjusted), adjusted, raw)

    return raw

def process_file(input_filename: str, output_path: str, lon_min=-180, lon_max=180, lat_min=-90, lat_max=90, days_ago=360, prefer_adjusted=True):
    """
        Processes the input netCDF file

        Args:
            input_filename (str): Path to the .nc file.
            output_path (str): Path to the output folder.
            lon_min (float): The minimum longitude.
            lon_max (float): The maximum longitude.
            lat_min (float): The minimum latitude.
            lat_max (float): The maximum latitude.
            days_ago (int): The number of days defining the interval from today to the maximum allowed date from the JULD field of the input file

        Returns:
            passes "output_path", "finish_dict" to the "csv_gen" function
            finish_dict (dict): Dictionary of finished records.

        Raises:
            ValueError: If required sections or data are missing in the file.
    """
    finish_dict = dict()

    ds = xr.open_dataset(input_filename)

    lons = ds['LONGITUDE'].values
    lats = ds['LATITUDE'].values
    temp = get_numeric_values(ds, 'TEMP', prefer_adjusted=prefer_adjusted)
    pres = get_numeric_values(ds, 'PRES', prefer_adjusted=prefer_adjusted)
    psal = get_numeric_values(ds, 'PSAL', prefer_adjusted=prefer_adjusted)
    dt_data = ds['JULD'].values
    platform_number = ds['PLATFORM_NUMBER'].values
    cycle_number = ds['CYCLE_NUMBER'].values
    size_lon = len(lons)
    size_lev = len(temp[0,:])
    lastdepth = 0
    for i in range(size_lon):
        for j in range(size_lev):
            date = datetime.datetime.strptime(str(dt_data[i]).split("T")[0], "%Y-%m-%d").date()
            if date > datetime.date.today() - datetime.timedelta(days=days_ago):
                if lats[i] > lat_min and lats[i] < lat_max and lons[i] > lon_min and lons[i] < lon_max:
                    if str(dt_data[i]).split("T")[0] not in finish_dict.keys():
                        finish_dict[str(dt_data[i]).split("T")[0]] = []
                    if j != 0:
                        prev_pressure = pres[i, j-1]
                    else:
                        prev_pressure = 0
                        lastdepth = 0
                    depth = getDepth_iter(pres[i,j], psal[i,j],temp[i,j], lastdepth, prev_pressure, lats[i])
                    lastdepth = depth
                    finish_dict[str(dt_data[i]).split("T")[0]].append(
                        Record(lats[i], lons[i],
                               depth,
                               temp[i,j], pres[i, j], psal[i, j],
                               str(dt_data[i]).split('.')[0], platform_number[i], cycle_number[i]))
    ds.close()
    csv_gen(output_path, finish_dict)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Программа выборки данных из Argo NetCDF")
    parser.add_argument(
        "--input_dir", "-i",
        # required=True,
        default="./data/DR/",
        help="Путь к директории с файлами netcdf."
    )
    parser.add_argument(
        "--output_dir", "-o",
        required=False,
        default="./output/DR",
        help="Путь для сохранения выходных файлов (по умолчанию: ./)."
    )

    parser.add_argument(
        "--max_lon", "-max_l",
        required=False,
        type=float,
        default=180,
        help="Максимальная долгота."
    )

    parser.add_argument(
        "--min_lon", "-min_l",
        required=False,
        type=float,
        default=-180,
        help="Минимальная долгота."
    )

    parser.add_argument(
        "--max_lat", "-max_lat",
        required=False,
        type=float,
        default=90,
        help="Максимальная широта."
    )

    parser.add_argument(
        "--min_lat", "-min_lat",
        required=False,
        type=float,
        default=-90,
        help="Минимальная широта."
    )

    parser.add_argument(
        "--days_ago", "-d",
        required=False,
        type=int,
        default=120,
        help="Количество дней для фильтрации записей внутри netCDF по полю JULD."
    )

    args = parser.parse_args()

    input_path = args.input_dir
    output_path = args.output_dir
    lat_min = args.min_lat
    lat_max = args.max_lat
    lon_min = args.min_lon
    lon_max = args.max_lon
    days_ago = args.days_ago
    # Фильтр по возрасту файла: не старше 14 дней.
    # Дополнительный параметр запуска для этого не нужен.
    file_max_age_days = 14

    # На Linux дата создания файла определяется ненадёжно, поэтому берём дату
    # из имени Argo-файла DYYYYMMDD_... / RYYYYMMDD_..., если она есть.
    # Если дата в имени не распознана, используем дату изменения файла.
    prefer_adjusted = True


    processed_files = dict()
    new_processed_files = dict()
    log_path = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + '/processed_files.log'
    if os.path.exists(log_path):
        with open(log_path, encoding='utf-8-sig') as f:
            lines = f.readlines()
        for line in lines:
            processed_files[line.strip()] = True
    if not output_path.endswith("/"):
        output_path += "/"
    if not input_path.endswith("/"):
        input_path += "/"

    files = [f for f in os.listdir(input_path) if os.path.isfile(os.path.join(input_path, f))]
    for file in files:
        file_full_path = os.path.join(input_path, file)

        if not file.endswith(".nc"):
            continue

        if file in processed_files.keys():
            continue

        if not is_file_recent(file_full_path, file_max_age_days):
            file_dt = get_file_datetime(file_full_path)
            print(f"Пропуск файла по дате файла: {file} ({file_dt:%Y-%m-%d %H:%M:%S})")
            continue

        print("Обработка файла: ", file)
        # try:
        process_file(file_full_path, output_path, lon_min, lon_max, lat_min, lat_max, days_ago, prefer_adjusted=prefer_adjusted)
        new_processed_files[file] = True

    if new_processed_files:
        with open(log_path, 'a', encoding='utf-8-sig') as f:
            for file in new_processed_files:
                f.write(file + "\n")
