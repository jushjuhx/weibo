__author__ = 'hope'
import io , gzip

#解压gzip
def gzipdecode(data) :
    #python3 The StringIO and cStringIO modules are gone. Instead, import the io module and use io.StringIO or io.BytesIO for text and data respectively.
    #python2 中是StringIO.StringIO(data)
    compressedstream = io.BytesIO(data)
    gziper = gzip.GzipFile(fileobj=compressedstream)
    datadecode = gziper.read()   # 读取解压缩后数据
    return datadecode