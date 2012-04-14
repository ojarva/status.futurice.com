import subprocess
import local_settings
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from multiprocessing import Queue
import urllib2
import json
import time
import multiprocessing

class PrinterStatus:
    def __init__(self, hostname, password):
        self.hostname = hostname
        self.password = password
        self._data = None

    def get(self, key):
        p = subprocess.Popen(["snmpwalk", "-Cc", "-v1", "-On", "-c", self.password, self.hostname, key], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (dataout, errors) = p.communicate()
        if len(errors) > 5:
            print errors
            raise Exception("Error occured during snmpwalk")
        dataout = dataout.split("\n")
        data_final = []
        for item in dataout:
            item = item.split(" = ", 1)
            if len(item) == 2:
                data_final.append(item[1].strip().replace("STRING: ", "").replace("INTEGER: ", "").replace("Counter32: ", ""))
        return data_final



    def status(self):
        status = self.get(".1.3.6.1.2.1.25.3.5.1.1.1")
        if status == False:
            return {"num": -1, "readable": "invalid"}
        status = status[0]            
        status = status.split("(")
        if len(status) == 2:
            return {"num": status[1].replace(")", ""), "readable": status[0]}
        else:
            return {"num": -1, "readable": "invalid"}

    def get_pages(self):
        count = self.get(".1.3.6.1.2.1.43.10.2.1.4.1.1")
        if count == False:
            return None
        count = count[0]
        try:
            count = int(count)
        except ValueError:
            return None
        return count

    def alert_level(self):
        #  unknown(1), running(2), warning(3), testing(4), down(5)
        status = self.get(".1.3.6.1.2.1.25.3.2.1.5.1")
        if status == False:
            return {"num": -1, "readable": "invalid"}
        status = status[0]
        status = status.split("(")
        if len(status) == 2:
            return {"num": status[1].replace(")", ""), "readable": status[0]}
        else:
            return {"num": -1, "readable": "invalid"}

    def alert_text(self):
        status_texts = []
        value = self.get(".1.3.6.1.2.1.43.18.1.1.8.1")
        return value

    def get_papers(self):
        papers = []
        names = self.get(".1.3.6.1.2.1.43.8.2.1.18.1")
        max_values = self.get(".1.3.6.1.2.1.43.8.2.1.9.1")
        current_values = self.get(".1.3.6.1.2.1.43.8.2.1.10.1")

        for item in range(0, len(names)):
            name = names[item].replace("\"", "").split(", ", 1)
            name = name[0]
            max_value = max_values[item]
            current_value = current_values[item]
            if current_value == "-3":
                current_value = max_value
            if max_value > 0:
                percentage = max(0, round(float(current_value) / float(max_value) * 100, 0))
            else:
                percentage = "-"
            paper = {"name": name, "current": current_value, "max": max_value, "percentage": percentage}
            papers.append(paper)
        return papers

    def get_consumables(self):
        consumables = []
        names = self.get(".1.3.6.1.2.1.43.11.1.1.6.1")
        max_values = self.get(".1.3.6.1.2.1.43.11.1.1.8.1")
        current_values = self.get(".1.3.6.1.2.1.43.11.1.1.9.1")

        for item in range(0, len(names)):
            name = names[item].replace("\"", "").split(", ", 1)
            name = name[0]
            max_value = max_values[item]
            current_value = current_values[item]
            if current_value == "-3":
                current_value = max_value
            if max_value > 0:
                percentage = max(0, round(float(current_value) / float(max_value) * 100, 0))
            else:
                percentage = "-"
            consumable = {"name": name, "current": current_value, "max": max_value, "percentage": percentage}
            consumables.append(consumable)
        return consumables

def send(what, filename):
    datagen, headers = multipart_encode({"data": open(filename, "rb"), "password": local_settings.UPLOAD_PASSWORD, "what": what})
    request = urllib2.Request(local_settings.UPLOAD_URL, datagen, headers)
    urllib2.urlopen(request).read()

def clientprog(queue, printer_settings):
    printer = PrinterStatus(printer_settings["hostname"], printer_settings["password"])
    status = {"name": printer_settings["name"], "slug": printer_settings["slug"]}
    try:
        status["status"] = printer.status()
    except:
        return
    status["alert_level"] = printer.alert_level()
    status["alert_text"] = printer.alert_text()
    status["consumables"] = printer.get_consumables()
    status["papers"] = printer.get_papers()
    status["pages"] = printer.get_pages()
    queue.put(status)

def main():
    register_openers()

    printers = local_settings.PRINTERS
    statuses = []
    threads = []
    queue = Queue()
    for item in printers:
        p = multiprocessing.Process(target=clientprog, args=(queue, item))
        p.start()
        threads.append(p)
    for item in threads:
        try:
            item.join()
        except:
            pass
    while not queue.empty():
        statuses.append(queue.get())

    if len(statuses) == 0:
        print "Failed to connect to any printer"
        return
    data = {"printers": statuses, "timestamp": time.time()}
    json.dump(data, open("statuses.json", "w"))
    send(settings.UPLOAD_DESTINATION, "statuses.json")

if __name__ == '__main__':
    main()
