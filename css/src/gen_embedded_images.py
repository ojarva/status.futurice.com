import base64
import glob
import os
from PIL import Image

for filename in glob.glob("../../img/*.gif"):
    size = os.path.getsize(filename)
    if size > 2000:
        continue
    fname = os.path.basename(filename).replace(".gif", "-gif")
    im = Image.open(filename)
    (width, height) = im.size

    print """
.%s {
    background-image: url("data:image/gif;base64,%s");
    background-repeat: none;
    display:inline-block;
    height:%spx;
    width:%spx;
}
""" % (fname, base64.b64encode(open(filename).read()), height, width)
#    print im.size, fname, size
