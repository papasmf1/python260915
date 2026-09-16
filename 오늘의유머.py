# web2.py 
#크롤링을 위한 선언
from bs4 import BeautifulSoup
import urllib.request 
#정규표현식
import re

#파일에 저장
f = open("todayHumor.txt", "wt", encoding="utf-8")

hdr = {'User-Agent': 'Mozilla/5.0'}

#페이징처리
for i in range(1,11):
    url = f"https://www.todayhumor.co.kr/board/list.php?table=bestofbest&page={i}"
    print(url)
    #요청객체
    req = urllib.request.Request(url, headers=hdr)
    data = urllib.request.urlopen(req).read()
    soup = BeautifulSoup(data, "html.parser")

    for tag in soup.find_all("td", attrs={"class":"subject"}):
        title = tag.text.strip()
        title = title.replace("\n", "")
        if re.search("미국", title):
            print(title)
            f.write(title + "\n")

f.close()

#<td class="subject">
# <a href="/board/view.php">국립박물관 굿즈 몇개 </a><span class="list_memo_count_span"> [9]</span>  <span style="margin-left:4px;"><img src="//www.todayhumor.co.kr/board/images/list_icon_photo.gif" style="vertical-align:middle; margin-bottom:1px;"> </span> <span style="color:#999">3일</span></td>
