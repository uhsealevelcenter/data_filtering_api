import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi import FastAPI, Request, Form, Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import numpy as np
import pandas as pd

from uhslc_station_tools.extractor import load_station_data
from uhslc_station_tools.utils import datenum2
from uhslc_station_tools.filtering import matlab2datetime, hr_process
import uvicorn
from uhslc_station_tools.sensor import Station

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root(request: Request):
    station = load_station_data(['static/t1052202.dat'])

    return templates.TemplateResponse("basic-form.html", {"request": request})


@app.post('/', response_class=HTMLResponse)
async def post_basic_form(request: Request, username: str = Form(...), password: str = Form(...),
                          file: UploadFile = File(...)):
    print(f'username: {username}')
    print(f'password: {password}')
    data_obj = csv_to_obj(file.filename)
    time_start = matlab2datetime(data_obj["test"]["time"][0])
    time_end = matlab2datetime(data_obj["test"]["time"][-1])
    data_hr = hr_process(data_obj, time_start, time_end)
    csv_filename = "first_test.csv"
    convert_to_csv(data_hr["test"]["time"].flatten(), data_hr["test"]["sealevel"].flatten(), csv_filename)
    if os.path.exists(csv_filename):
        return FileResponse(csv_filename, media_type="text/csv", filename=csv_filename)
    return {"error": "File not found"}

    # return templates.TemplateResponse("basic-form.html", {"request": request})


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


def csv_to_obj(csv_file):
    """Given a path to a csv file, return an object that can be used for data filtering"""
    df = pd.read_csv(csv_file, sep=',', header=None)
    time = df.values.transpose()[0]
    sl = df.values.transpose()[1]
    sensor = "test"
    obj = {sensor: {"time": time,
                    "sealevel": sl,
                    "station": '014'
                    }
           }
    print ("RADI", obj)
    return obj


def convert_ts_to_csv(station: Station):
    """This function is hardcoded so it only works for the station in the example (t1052202.dat
        This is just a helper function to convert the station data to a csv file so I can test on it
    """
    data = station.combine_months()
    time = datenum2(data['time']['ENB'])
    sl = data['data']['ENB']
    combined = np.vstack((time, sl)).T
    a = np.asarray(combined)
    np.savetxt("t1052202.csv", a, delimiter=",")


def convert_to_csv(time, sl, filename="first_test.csv"):
    combined = np.vstack((time, sl)).T
    a = np.asarray(combined)
    np.savetxt(filename, a, delimiter=",")


if __name__ == "__main__":
    uvicorn.run(app)
