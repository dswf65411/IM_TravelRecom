
# coding: utf-8
import json
import requests
import lxml
import time
from io import StringIO, BytesIO
import lxml.etree
import sys

#searchTag = "牛肉湯"

def main(searchTag):
    resultList = []
    rs = requests.session()
    parser = lxml.etree.HTMLParser()
    for i in range(20):
        URLhere="https://www.pixnet.net/searcharticle?q=%E5%8F%B0%E5%8D%97%E6%97%85%E9%81%8A%E6%99%AF%E9%BB%9E&page=" + str(i+1)
        result = rs.get(URLhere)
        result.encoding = "utf-8"
        result = result.text
        html = lxml.etree.parse(BytesIO(result.encode('utf-8')), parser)
        for li in html.xpath("/html/body/div[@id='container1']/div/div[@id='container3']/div[@id='main']/div/div[@class='search-article']/div[@class='bin-main-search']/div[@class='inner']/ol[@class='search-result']/li"):
            taga = li.xpath("ul/li[@class='search-title']/a")[0]
            contentURL = taga.get('href')
            result = rs.get(contentURL)
            result.encoding = "utf-8"
            result = result.text
            html1 = lxml.etree.parse(BytesIO(result.encode('utf-8')), parser)
            newtagaURL = html1.xpath("/html/head/meta")[1]
            newtagaURL = newtagaURL.get('content').split('=')[1]
            result = rs.get(newtagaURL)
            result.encoding = "utf-8"
            result = result.text
            html2 = lxml.etree.parse(BytesIO(result.encode('utf-8')), parser)
            finalContent = str("".join(html2.xpath(u"//div[@class='article-content-inner']/descendant::text()")))
            resultText = taga.get('title') + "\n" + finalContent.replace('\n','')
            if searchTag in resultText:
                resultList.append(resultText)

    with open("pixer_%s.txt"%(searchTag),'w') as f1:
        f1.write(str(resultList))

if __name__ == '__main__':
    if len(sys.argv) == 2 :
        main(sys.argv[1])
    else :
        print('usage:\tpixerData.py <search_tag>')
        print('example:pixerData.py 牛肉湯')
        sys.exit(0)
    



