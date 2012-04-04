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
            return {"num": status[1], "readable": status[0]}
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
            return {"num": status[1], "readable": status[0]}
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
"""
workcentre:
paper capacity:
.1.3.6.1.2.1.43.8.2.1.9.1.1 = INTEGER: 560
.1.3.6.1.2.1.43.8.2.1.9.1.2 = INTEGER: 560
.1.3.6.1.2.1.43.8.2.1.9.1.3 = INTEGER: 980
.1.3.6.1.2.1.43.8.2.1.9.1.4 = INTEGER: 1280
.1.3.6.1.2.1.43.8.2.1.9.1.5 = INTEGER: 100
current amount of paper:
.1.3.6.1.2.1.43.8.2.1.10.1.1 = INTEGER: 140
.1.3.6.1.2.1.43.8.2.1.10.1.2 = INTEGER: 420
.1.3.6.1.2.1.43.8.2.1.10.1.3 = INTEGER: 735
.1.3.6.1.2.1.43.8.2.1.10.1.4 = INTEGER: 1280

names:
.1.3.6.1.2.1.43.8.2.1.18.1.1 = STRING: "Tray 1"
.1.3.6.1.2.1.43.8.2.1.18.1.2 = STRING: "Tray 2"
.1.3.6.1.2.1.43.8.2.1.18.1.3 = STRING: "Tray 3(High Capacity Feeder)"
.1.3.6.1.2.1.43.8.2.1.18.1.4 = STRING: "Tray 4(High Capacity Feeder)"
.1.3.6.1.2.1.43.8.2.1.18.1.5 = STRING: "Tray 5(Bypass)"

consumables:
.1.3.6.1.2.1.43.11.1.1.8.1.1 = INTEGER: 6480
.1.3.6.1.2.1.43.11.1.1.8.1.2 = INTEGER: 3960
.1.3.6.1.2.1.43.11.1.1.8.1.3 = INTEGER: 3960
.1.3.6.1.2.1.43.11.1.1.8.1.4 = INTEGER: 3960
.1.3.6.1.2.1.43.11.1.1.8.1.5 = INTEGER: 35000
.1.3.6.1.2.1.43.11.1.1.8.1.6 = INTEGER: 42000
.1.3.6.1.2.1.43.11.1.1.8.1.7 = INTEGER: 26000
.1.3.6.1.2.1.43.11.1.1.8.1.8 = INTEGER: 26000
.1.3.6.1.2.1.43.11.1.1.8.1.9 = INTEGER: 26000
.1.3.6.1.2.1.43.11.1.1.8.1.10 = INTEGER: 150000
.1.3.6.1.2.1.43.11.1.1.8.1.11 = INTEGER: 600000
.1.3.6.1.2.1.43.11.1.1.8.1.12 = INTEGER: 100000
.1.3.6.1.2.1.43.11.1.1.8.1.13 = INTEGER: 600000
.1.3.6.1.2.1.43.11.1.1.8.1.14 = INTEGER: 600000
.1.3.6.1.2.1.43.11.1.1.8.1.15 = INTEGER: 600000
.1.3.6.1.2.1.43.11.1.1.8.1.16 = INTEGER: 600000
.1.3.6.1.2.1.43.11.1.1.8.1.17 = INTEGER: 100000
.1.3.6.1.2.1.43.11.1.1.8.1.18 = INTEGER: 300000
.1.3.6.1.2.1.43.11.1.1.8.1.19 = INTEGER: 300000
.1.3.6.1.2.1.43.11.1.1.8.1.20 = INTEGER: 300000
.1.3.6.1.2.1.43.11.1.1.8.1.21 = INTEGER: 300000
.1.3.6.1.2.1.43.11.1.1.8.1.22 = INTEGER: 50000
.1.3.6.1.2.1.43.11.1.1.9.1.1 = INTEGER: 712
.1.3.6.1.2.1.43.11.1.1.9.1.2 = INTEGER: 1188
.1.3.6.1.2.1.43.11.1.1.9.1.3 = INTEGER: 2613
.1.3.6.1.2.1.43.11.1.1.9.1.4 = INTEGER: 950
.1.3.6.1.2.1.43.11.1.1.9.1.5 = INTEGER: 35000
.1.3.6.1.2.1.43.11.1.1.9.1.6 = INTEGER: 36960
.1.3.6.1.2.1.43.11.1.1.9.1.7 = INTEGER: 26000
.1.3.6.1.2.1.43.11.1.1.9.1.8 = INTEGER: 24700
.1.3.6.1.2.1.43.11.1.1.9.1.9 = INTEGER: 24960
.1.3.6.1.2.1.43.11.1.1.9.1.10 = INTEGER: 150000
.1.3.6.1.2.1.43.11.1.1.9.1.11 = INTEGER: 600000
.1.3.6.1.2.1.43.11.1.1.9.1.12 = INTEGER: 100000
.1.3.6.1.2.1.43.11.1.1.9.1.13 = INTEGER: 600000
.1.3.6.1.2.1.43.11.1.1.9.1.14 = INTEGER: 600000
.1.3.6.1.2.1.43.11.1.1.9.1.15 = INTEGER: 600000
.1.3.6.1.2.1.43.11.1.1.9.1.16 = INTEGER: 600000
.1.3.6.1.2.1.43.11.1.1.9.1.17 = INTEGER: 100000
.1.3.6.1.2.1.43.11.1.1.9.1.18 = INTEGER: 300000
.1.3.6.1.2.1.43.11.1.1.9.1.19 = INTEGER: 300000
.1.3.6.1.2.1.43.11.1.1.9.1.20 = INTEGER: 300000
.1.3.6.1.2.1.43.11.1.1.9.1.21 = INTEGER: 300000
consumables names:
.1.3.6.1.2.1.43.11.1.1.6.1.1 = STRING: "Black Toner [K] Cartridge"
.1.3.6.1.2.1.43.11.1.1.6.1.2 = STRING: "Yellow Toner [Y] Cartridge"
.1.3.6.1.2.1.43.11.1.1.6.1.3 = STRING: "Magenta Toner [M] Cartridge"
.1.3.6.1.2.1.43.11.1.1.6.1.4 = STRING: "Cyan Toner [C] Cartridge"
.1.3.6.1.2.1.43.11.1.1.6.1.5 = STRING: "Waste Toner Container"
.1.3.6.1.2.1.43.11.1.1.6.1.6 = STRING: "Black Drum Cartridge"
.1.3.6.1.2.1.43.11.1.1.6.1.7 = STRING: "Yellow Drum Cartridge"
.1.3.6.1.2.1.43.11.1.1.6.1.8 = STRING: "Magenta Drum Cartridge"
.1.3.6.1.2.1.43.11.1.1.6.1.9 = STRING: "Cyan Drum Cartridge"
.1.3.6.1.2.1.43.11.1.1.6.1.10 = STRING: "Bias Transfer Roll"
.1.3.6.1.2.1.43.11.1.1.6.1.11 = STRING: "Transfer Belt"
.1.3.6.1.2.1.43.11.1.1.6.1.12 = STRING: "Fuser Assembly"
.1.3.6.1.2.1.43.11.1.1.6.1.13 = STRING: "Black Developer"
.1.3.6.1.2.1.43.11.1.1.6.1.14 = STRING: "Yellow Developer"
.1.3.6.1.2.1.43.11.1.1.6.1.15 = STRING: "Magenta Developer"
.1.3.6.1.2.1.43.11.1.1.6.1.16 = STRING: "Cyan Developer"
.1.3.6.1.2.1.43.11.1.1.6.1.17 = STRING: "Transfer Belt Cleaner"
.1.3.6.1.2.1.43.11.1.1.6.1.18 = STRING: "Tray 1 Feed Roll"
.1.3.6.1.2.1.43.11.1.1.6.1.19 = STRING: "Tray 2 Feed Roll"
.1.3.6.1.2.1.43.11.1.1.6.1.20 = STRING: "Tray 3 Feed Roll"
.1.3.6.1.2.1.43.11.1.1.6.1.21 = STRING: "Tray 4 Feed Roll"
.1.3.6.1.2.1.43.11.1.1.6.1.22 = STRING: "Tray 5 Feed Roll"







snmpwalk -Cc -v1 -c asdf -On -M +/usr/share/snmp/mibs -m all lobby-4th.lan.futurice.org  .1.3.6.1.2.1.25.3.2.1.5.1
# other(1), unknown(2), idle(3), printing(4), warmup(5)
snmpwalk -Cc -v1 -c asdf -On -M +/usr/share/snmp/mibs -m all lobby-4th.lan.futurice.org   .1.3.6.1.2.1.25.3.5.1.1.1
# status text
snmpwalk -Cc -v1 -c asdf -On -M +/usr/share/snmp/mibs -m all lobby-4th.lan.futurice.org  .1.3.6.1.2.1.43.18.1.1.8.1
# This is the number of items that have been marked.  There are other fields
# that tell what the unit values are,  and what this measures.  Almost
# always this is the number of impressions,  not pages, that have
# been made by the printer.
#1.3.6.1.2.1.43.10.2.1.4.1.1 page count
snmpwalk -Cc -v1 -c asdf -On -M +/usr/share/snmp/mibs -m all lobby-4th.lan.futurice.org   .1.3.6.1.2.1.43.10.2.1.4.1.1
# Screen text
snmpwalk -Cc -v1 -c asdf -On -M +/usr/share/snmp/mibs -m all lobby-4th.lan.futurice.org  | grep  .1.3.6.1.2.1.43.16.5.1.2.1

# alert level    other(1), critical(3), warning(4), warningBinaryChangeEvent(5)
snmpwalk -Cc -v1 -c asdf -On -M +/usr/share/snmp/mibs -m all lobby-4th.lan.futurice.org    .1.3.6.1.2.1.43.18.1.1.2.1.1
# alert category  	other(1), hostResourcesMIBStorageTable(3),
# 	hostResourcesMIBDeviceTable(4), generalPrinter(5), cover(6),
# 	localization(7), input(8), output(9), marker(10),
# 	markerSupplies(11), markerColorant(12), mediaPath(13),
# 	channel(14), interpreter(15), consoleDisplayBuffer(16),
# 	consoleLights(17), alert(18), finDevice(30), finSupply(31),
# 	finSupplyMediaInput(32), finAttributeTable(33)
snmpwalk -Cc -v1 -c asdf -On -M +/usr/share/snmp/mibs -m all lobby-4th.lan.futurice.org     .1.3.6.1.2.1.43.18.1.1.4.1.3 

"""
