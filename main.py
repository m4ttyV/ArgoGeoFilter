import argparse
import csv
import os

import numpy as np
import xarray as xr

def getDepth(pres, temp, salt):
    return 99999

def checkTheory(list_to_check, i_max, j_max):
    i = 690
    j = 690
    outlist = list()
    while i < i_max:
        while j < j_max:
            if not np.isnan(list_to_check[i,j]):
                outlist.append(f"{i}, {j}, {list_to_check[i,j]} \n")
            j += 1
        j = 690
        i += 1
    return outlist
def write_result_to_file(name, result):
    filename = "./" + name + ".txt"
    with open(filename, "w") as f:
        f.writelines(result)
    print(f"Данные успешно записаны в файл {filename}")


class Field:
    def __init__(self, id, lat, lon, depth, temp, pres, psal):
        self.id = id
        self.lat = lat
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
class CSVRow(Field):
    def dec(self):
        pass

def csv_gen(filename, csv_row): #id, datetime, lat, lon, depth !изменить формат на 3 знака после запятой
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["id", "lat", "lon", "depth", "temperature", "pressure", "salinity"])
        id = 0
        for row in csv_row:
            id += 1
            if row.lat != "None":
                lat = "{0:.3f}".format(row.lat)
            if row.lon != "None":
                lon = "{0:.3f}".format(row.lon)
            # if row.depth != "None":
            #     depth = "{0:.3f}".format(row.depth)
            depth = row.depth
            if row.temp != "None":
                temp = "{0:.3f}".format(row.temp)
            if row.pres != "None":
                pres = "{0:.3f}".format(row.pres)
            writer.writerow([
                str(id), lat, lon, depth, temp, pres
            ])



def process_file(input_filename, output_path):
    lon_min = -180
    lon_max = 180
    lat_min = -90
    lat_max = 90
    depth = 99999

    ds = xr.open_dataset(input_filename)

    lons = ds['LONGITUDE'].values
    lats = ds['LATITUDE'].values
    temp = ds['TEMP'].values
    pres = ds['PRES'].values
    psal = ds['PSAL'].values
    csv_rows = list()
    field = list()
    i, j = 0, 0
    size_lon = len(lons)
    size_lev = len(temp[0,:])
    for i in range(size_lon):
        for j in range(size_lev):
            field.append(Field(len(field), lats[i], lons[i], getDepth(pres[i, j], temp[i,j],  psal[i, j]), temp[i,j], pres[i, j], psal[i, j]))

    for row in field:
        if row.lat > lat_min and row.lat < lat_max and row.lon > lon_min and row.lon < lon_max:
            csv_rows.append(row)
    csv_filename = output_path + os.path.basename(f"{input_filename}.csv")
    csv_gen(csv_filename, csv_rows)



if __name__ == "__main__":
    # process_file("./data/D20250317_prof_3.nc", "./data/D20250317_prof_3.csv")

    parser = argparse.ArgumentParser(description="Программа выборки данных из Argo NetCDF")
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Путь к входному NetCDF-файлу."
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        default="./",
        help="Путь для сохранения выходного файла (по умолчанию: ./)."
    )

    # Парсим аргументы
    args = parser.parse_args()

    # Запускаем обработку данных
    # process_file(args.input, args.output)

