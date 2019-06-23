from socket import gaierror, gethostbyname
from urllib.parse import urlparse
from time import gmtime, strftime
from threading import Event, Thread
from multiprocessing import Pool
import json

import requests
from flask import Flask, jsonify, render_template

NESSESARY_DATA = 'requested_data.json'
REFRESH_TIME = 5

statuses = {}
returned_content = {}


def update():
    return strftime("%Y-%m-%d %H:%M:%S", gmtime())


def reachable(url):
    try:
        gethostbyname(url)
    except gaierror:
        return False
    else:
        return True


def get_status_code(url):
    try:
        status_code = requests.get(url, timeout=30).status_code
        return status_code
    except requests.ConnectionError:
        return "site_down"


def check_url(url):
    if reachable(urlparse(url).hostname):
        return str(get_status_code(url))
    else:
        return "site_down"


def check_content():
    urls_list = prepare_data()[0]
    content_list = prepare_data()[1]
    for i in range(len(content_list)):
        r = requests.get(urls_list[i]).text
        if content_list[i] in r:
            returned_content[content_list[i]] = True
        else:
            returned_content[content_list[i]] = False


def prepare_data():
    '''
    Function that reads json file with sites to watch, content required
    and returns it in form of lists.
    '''
    with open(NESSESARY_DATA, 'r') as f:
        loaded_data = json.load(f)

    sites_list = loaded_data['sites']
    content_list = loaded_data['content_requested']

    return sites_list, content_list


class MyThread(Thread):
    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event

    def run(self):
        urls_list = prepare_data()[0]
        check_period = REFRESH_TIME
        while not self.stopped.wait(check_period):
            pool = Pool(len(urls_list))
            status_list = pool.map(check_url, urls_list)
            for i in range(len(urls_list)):
                statuses[urls_list[i]] = status_list[i]
            check_content()


app = Flask(__name__)


@app.route("/", methods=["GET"])
def display_returned_statuses():
    return render_template(
        'returned_data.html',
        returned_data=statuses,
        returned_content=returned_content,
        last_updated=update(),
        )


@app.route("/api", methods=["GET"])
def display_returned_api():
    return jsonify(
        statuses, returned_content
        ), 200


if __name__ == '__main__':
    stopFlag = Event()
    thread = MyThread(stopFlag)
    thread.start()
    app.run()
