import json
import rrdtool
import os
import hashlib
import unicodedata
import redis

class UpdateGraphs:
    def __init__(self, filename):
        self.filename = filename
        self._data = None
        self._settings = None
        self.redis = redis.Redis()
        self.settings_key = "graphs:"+hashlib.md5(self.filename).hexdigest()+".settings.json"

    @property
    def data(self):
        if not self._data:
            data = self.redis.get(self.filename)
            if data:
                 self._data = json.loads(data)

        return self._data

    @property
    def settings(self):
        if not self._settings:
            settings = self.redis.get(self.settings_key)
            if not settings:
                self._settings = {"timestamp": -1}
            else:
                 self._settings = json.loads(settings)
        return self._settings
     
    def save(self, data):
        self.redis.set(self.settings_key, json.dumps(data))

    def getpagesgraph(self, graphname):
        graphs = []
        def gengraph(fullpath, step, heartbeat):
            fullpath = unicodedata.normalize("NFKD", fullpath).encode("ascii", "ignore")
            if not os.path.exists(fullpath):
                rrdtool.create(fullpath,
                       '--step', str(step),
                       'DS:value1:GAUGE:%s:0:U' % heartbeat,
                       'DS:value2:DERIVE:%s:0:U' % heartbeat,
                       'RRA:AVERAGE:0.5:1:1000',
                       'RRA:AVERAGE:0.5:6:4320',
                       'RRA:AVERAGE:0.5:12:4320',
                       'RRA:AVERAGE:0.5:60:8760',
                       'RRA:AVERAGE:0.5:1440:1825',

                       'RRA:MIN:0.5:1:1000',
                       'RRA:MIN:0.5:6:4320',
                       'RRA:MIN:0.5:12:4320',
                       'RRA:MIN:0.5:60:8760',
                       'RRA:MIN:0.5:1440:1825',

                       'RRA:LAST:0.5:1:1000',
                       'RRA:LAST:0.5:6:4320',
                       'RRA:LAST:0.5:12:4320',
                       'RRA:LAST:0.5:60:8760',
                       'RRA:LAST:0.5:1440:1825',

                       'RRA:MAX:0.5:1:1000',
                       'RRA:MAX:0.5:6:4320',
                       'RRA:MAX:0.5:12:4320',
                       'RRA:MAX:0.5:60:8760',
                       'RRA:MAX:0.5:1440:1825'
                )
            return fullpath

        graphs.append(gengraph("../data/printer_graphs/%s.rrd" % graphname, 60, 1200))
        graphs.append(gengraph("../data/printer_graphs/%s-hourly.rrd" % graphname, 60*60, 1200*5))
        graphs.append(gengraph("../data/printer_graphs/%s-hourly.rrd" % graphname, 60*60, 1200*5))
        graphs.append(gengraph("../data/printer_graphs/%s-daily.rrd" % graphname, 60*60*24, 1200*5*24))

        return graphs

    def getgraph(self, graphname):
        fullpath = "../data/printer_graphs/%s.rrd" % graphname
        fullpath = unicodedata.normalize("NFKD", fullpath).encode("ascii", "ignore")
        
        if not os.path.exists(fullpath):
            rrdtool.create(fullpath,
                       '--step', '60',
                       'DS:value:GAUGE:1200:0:100',
                       'RRA:AVERAGE:0.5:1:1000',
                       'RRA:AVERAGE:0.5:6:4320',
                       'RRA:AVERAGE:0.5:12:4320',
                       'RRA:AVERAGE:0.5:60:8760',
                       'RRA:AVERAGE:0.5:1440:1825',

                       'RRA:MIN:0.5:1:1000',
                       'RRA:MIN:0.5:6:4320',
                       'RRA:MIN:0.5:12:4320',
                       'RRA:MIN:0.5:60:8760',
                       'RRA:MIN:0.5:1440:1825',

                       'RRA:LAST:0.5:1:1000',
                       'RRA:LAST:0.5:6:4320',
                       'RRA:LAST:0.5:12:4320',
                       'RRA:LAST:0.5:60:8760',
                       'RRA:LAST:0.5:1440:1825',

                       'RRA:MAX:0.5:1:1000',
                       'RRA:MAX:0.5:6:4320',
                       'RRA:MAX:0.5:12:4320',
                       'RRA:MAX:0.5:60:8760',
                       'RRA:MAX:0.5:1440:1825'
            )
        return fullpath

    def updategraph(self, graphfull, timestamp, data):
        try:
            rrdtool.update(graphfull, '%s:%s' % (timestamp, data))
            return True
        except rrdtool.error:
            return False

    def updatepagesgraph(self, graphfull, timestamp, data):
        try:
            rrdtool.update(graphfull, '%s:%s:%s' % (timestamp, data, data))
            return True
        except rrdtool.error, e:
            print "Updating pages failed", e
            return False

    def run(self, force=False):
        if self.data.get("timestamp", 0) == self.settings["timestamp"] and not force:
            return False
        for printer in self.data.get("printers", []):
            for consumable in printer.get("consumables", []):
                graphname = "consumable-" + printer["slug"] + "-" + hashlib.md5(consumable["name"]).hexdigest()
                graphfull = self.getgraph(graphname)
                self.updategraph(graphfull, self.data.get("timestamp"), consumable["percentage"])

            for paper in printer.get("papers", []):
                graphname = "paper-" + printer["slug"] + "-" + hashlib.md5(paper["name"]).hexdigest()
                graphfull = self.getgraph(graphname)
                self.updategraph(graphfull, self.data.get("timestamp"), paper["percentage"])

            if printer.get("pages"):
                graphname = "pages-" + printer["slug"]
                graphfull = self.getpagesgraph(graphname)
                for graph in graphfull:
                    self.updatepagesgraph(graph, self.data.get("timestamp"), printer.get("pages"))

        settings = {"timestamp": self.data["timestamp"]}
        self.save(settings)

def main():
    update = UpdateGraphs("data:printers.json")
    update.run(True)

if __name__ == '__main__':
    main()
