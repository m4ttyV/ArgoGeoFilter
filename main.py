import argparse
import csv
import os
from os import mkdir
import datetime
import numpy as np
import xarray as xr
from dateutil.relativedelta import relativedelta

def getDepth(pres, temp, salt):
    return 99999

class Record:
    def __init__(self, lat, lon, depth, temp, pres, psal, datetime, platform_number, cycle_number  ):
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
        self.datetime = datetime
        self.platform_number = str(platform_number).strip('b').strip('\'')
        self.cycle_number = cycle_number



def csv_gen(filedir, finish_dict):
    # Проверяем наличие директории
    if not os.path.exists(filedir):
        mkdir(filedir)
    # Проверяем наличие файлов с необходимой датой
    for dates in finish_dict.keys():
        newfilename = filedir + dates + ".csv"
        if not os.path.exists(newfilename):
            with open(newfilename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow(
                    ["Platform_number", "Cycle number", "Latitude", "Longitude",
                     "Datetime", "Depth", "Pressure", "Temperature", "Salinity"])

    for dates in finish_dict:
        file = filedir + dates + ".csv"
        with open(file, 'a', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            for item in finish_dict[dates]:
                lat, lon, depth, temp, pres, sal, datetime, platform_number = \
                    99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999
                if item.lat != "None":
                    lat = "{0:.3f}".format(item.lat)
                if item.lon != "None":
                    lon = "{0:.3f}".format(item.lon)
                depth = item.depth
                if item.temp != "None":
                    temp = "{0:.3f}".format(item.temp)
                if item.pres != "None":
                    pres = "{0:.3f}".format(item.pres)
                if item.psal != "None":
                    sal = "{0:.3f}".format(item.psal)
                datetime = item.datetime
                platform_number = item.platform_number
                cycle_number = item.cycle_number
                if temp == 99999 and pres == 99999 and sal == 99999:
                    continue
                writer.writerow([
                    platform_number, cycle_number, lat, lon, datetime, depth, pres, temp, sal
                ])

def process_file(input_filename, output_path, lon_min = -180, lon_max = 180, lat_min = -90, lat_max = 90, monthes_ago = 2):

    finish_dict = dict()

    ds = xr.open_dataset(input_filename)

    lons = ds['LONGITUDE'].values
    lats = ds['LATITUDE'].values
    temp = ds['TEMP'].values
    pres = ds['PRES'].values
    psal = ds['PSAL'].values
    dt_data = ds['JULD'].values
    platform_number = ds['PLATFORM_NUMBER'].values
    cycle_number = ds['CYCLE_NUMBER'].values
    size_lon = len(lons)
    size_lev = len(temp[0,:])
    for i in range(size_lon):
        for j in range(size_lev):
            date = datetime.datetime.strptime(str(dt_data[i]).split("T")[0], "%Y-%m-%d").date()
            if date > datetime.date.today() - relativedelta(month=monthes_ago):
                if lats[i] > lat_min and lats[i] < lat_max and lons[i] > lon_min and lons[i] < lon_max:
                    if str(dt_data[i]).split("T")[0] not in finish_dict.keys():
                        finish_dict[str(dt_data[i]).split("T")[0]] = []
                    finish_dict[str(dt_data[i]).split("T")[0]].append(
                        Record(lats[i], lons[i],
                               getDepth(pres[i, j], temp[i,j],  psal[i, j]),
                               temp[i,j], pres[i, j], psal[i, j],
                               str(dt_data[i]).split('.')[0], platform_number[i], cycle_number[i]))
    ds.close()
    csv_gen(output_path, finish_dict)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Программа выборки данных из Argo NetCDF")
    parser.add_argument(
        "--input_dir", "-i",
        required=True,
        help="Путь к директории с файлами netcdf."
    )
    parser.add_argument(
        "--output_dir", "-o",
        required=False,
        default="./",
        help="Путь для сохранения выходных файлов (по умолчанию: ./)."
    )
    parser.add_argument(
        "--max_lon", "-max_l",
        required=False,
        default=180,
        help="Путь к директории с файлами netcdf."
    )
    parser.add_argument(
        "--min_lon", "-min_l",
        required=False,
        default=-180,
        help="Путь для сохранения выходных файлов (по умолчанию: ./)."
    )
    parser.add_argument(
        "--max_lat", "-max_lat",
        required=False,
        default=90,
        help="Путь к директории с файлами netcdf."
    )
    parser.add_argument(
        "--min_lat", "-min_lat",
        required=False,
        default=-90,
        help="Путь для сохранения выходных файлов (по умолчанию: ./)."
    )
    parser.add_argument(
        "--monthes_ago", "-m",
        required=False,
        default=2,
        help="Путь к директории с файлами netcdf."
    )
    input_path = parser.parse_args().input
    output_path = parser.parse_args().output
    lat_min = parser.parse_args().min_lat
    lat_max = parser.parse_args().max_lat
    lon_min = parser.parse_args().min_lon
    lon_max = parser.parse_args().max_lon
    monthes_ago = parser.parse_args().monthes_ago


    # input_path = "C:/Users/glebm/PyCharmProjects/ArgoGeoFilter/data/check2"
    # output_path = "./output/DR"

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
        if file.endswith(".nc") and file not in processed_files.keys():
            print("Обработка файла: ", file)
            # try:
            process_file(input_path + file, output_path, lon_min, lon_max, lat_min, lat_max, monthes_ago)
            new_processed_files[file] = True

    with open(log_path, 'a', newline='', encoding='utf-8-sig') as f:
        for file in new_processed_files.keys():
            f.write(file + "\n")


