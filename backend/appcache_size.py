import urllib2

class Appcache:
    def __init__(self, cachefilename):
        self.cachefilename = cachefilename
        self.appcache_content = open(self.cachefilename).read()

    def run(self):
        content = self.appcache_content.split("\n")
        size = 0
        for line in content:
            line = line.strip()
            if len(line) < 2:
                continue
            if line[0] != "/":
                continue
            if " " in line:
                line = line.split()
                line = line[1]
            u = urllib2.urlopen("http://localhost%s" % line)
            meta = u.info()
            size += int(meta.getheaders("Content-Length")[0])
        return size

def main():
    appcache = Appcache("cache.manifest")
    print appcache.run()

if __name__ == '__main__':
    main()
