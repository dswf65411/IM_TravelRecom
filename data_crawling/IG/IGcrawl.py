# coding: utf-8


import requests
import lxml
from io import BytesIO
import lxml.etree
import re
import sys

def parse_content(htmlin):
    '''
        input : str, raw html code
        output: dict() , post_dictionary of posts' content and their link
    '''
    parser = lxml.etree.HTMLParser()
    html = lxml.etree.parse(BytesIO(htmlin.encode('utf-8')), parser) 
    pdict_tmp = html.xpath("/html/body/script[@type='text/javascript']")[0].text[21:-1]
    pdict_tmp = re.sub(r"\bfalse\b","False",pdict_tmp)  #is equal to '\\bfalse\\b'
    pdict_tmp = re.sub(r"\btrue\b","True",pdict_tmp)
    pdict_tmp = re.sub(r"\bnull\b","None",pdict_tmp)
    pdict_tmp = eval(pdict_tmp)
    return pdict_tmp

def get_html_text(URL,rs=requests.session()):
    '''
        input : str, URL wanted to crawl
        output: str, text of html code
    '''
    html1 = rs.get(URL)
    html1.encoding = 'utf-8'
    return html1.text

def get_usrName_and_cmtList(tmp_code):
    '''
        input:  str, post_id's code, ex:"BE3l0CKOvTr".
        output: tuple, (str,list), (this user's name,[comments on this posts]).
    '''
    getURL = "https://www.instagram.com/p/%s/"%(tmp_code)
    result = get_html_text(getURL)
    
    usr_name = re.findall("See this Instagram photo by @([a-zA-Z0-9_\.]*)",result)
    if len(usr_name) == 0:
        usr_name = re.findall("See this Instagram video by @([a-zA-Z0-9_\.]*)",result)
    else:
        usr_name = usr_name[0]
        
    page_content = parse_content(result)
    cmt_list = []
    for cmt in  page_content['entry_data']['PostPage'][0]['media']['comments']['nodes']:
        cmt_list.append(cmt['text'])
    return (usr_name,cmt_list)

def add_recent_posts(post_time,person,days=3):
    '''
        input : (float,dict,int), (posting timestamp, this tag_post's dict, near_days).
        output: dict, this tag_post's dict + it's recent posts.
    '''
    getURL = "https://www.instagram.com/%s/"%(person['username'])
    pdict_tmp = parse_content(get_html_text(getURL))
    page_tmp = pdict_tmp['entry_data']['ProfilePage'][0]['user']['media']['page_info']
    over_7_days = False

    for post in pdict_tmp['entry_data']['ProfilePage'][0]['user']['media']['nodes']:
        if abs(post_time-post['date']) < 86400*days:  #7 days
            (usrName,cmtList) = get_usrName_and_cmtList(post['code'])
            post['comments']['contents'] = cmtList
            post['username'] = usrName
            if 'recent_posts' not in person:
                person['recent_posts'] = [post]
            else:
                person['recent_posts'].append(post)

    while page_tmp['has_next_page'] == True:
        getURL = "https://www.instagram.com/%s/?max_id=%s"%(person['username'],page_tmp['end_cursor'])
        pdict_tmp = parse_content(get_html_text(getURL))
        page_tmp = pdict_tmp['entry_data']['ProfilePage'][0]['user']['media']['page_info']
        over_7_days = False
        for post in pdict_tmp['entry_data']['ProfilePage'][0]['user']['media']['nodes']:
            if abs(post_time-post['date']) < 86400*days:  #7 days
                (usrName,cmtList) = get_usrName_and_cmtList(post['code'])
                post['comments']['contents'] = cmtList
                post['username'] = usrName
                if 'recent_posts' not in person:
                    person['recent_posts'] = [post]
                else:
                    person['recent_posts'].append(post)
            if post_time-post['date'] > 86400*days:
                over_7_days = True
                break
        if over_7_days==True:
            break
    return person


def main(searchTag,days):
    getURL = "https://www.instagram.com/explore/tags/%s/"%(searchTag)
    rs = requests.session()
    result = get_html_text(getURL,rs)

    p_list = []   #all the post list
    pdict_tmp = parse_content(result)
    p_list.extend(pdict_tmp['entry_data']['TagPage'][0]['tag']['media']['nodes'])
    page_tmp = pdict_tmp['entry_data']['TagPage'][0]['tag']['media']['page_info']
    print("posts has crawl :")
    while page_tmp['has_next_page'] == True:
    #     time.sleep(0.1)
        getURL = "https://www.instagram.com/explore/tags/%s/?max_id=%s"%(searchTag,page_tmp['end_cursor'])
        pdict_tmp = parse_content(get_html_text(getURL,rs))
        p_list.extend(pdict_tmp['entry_data']['TagPage'][0]['tag']['media']['nodes'])
        page_tmp = pdict_tmp['entry_data']['TagPage'][0]['tag']['media']['page_info']
        sys.stdout.write("%d,"%(len(p_list)))

    if days==-1:
        p_final = []
        for i in range(len(p_list)):
            tag_post_id = p_list[i]['code']
            (usrName,cmtList) = get_usrName_and_cmtList(tag_post_id) #BE5QcuKNI9P
            p_list[i]['comments']['contents'] = cmtList
            p_list[i]['username'] = usrName
            post_time = p_list[i]['date']

        for post in p_list:
            p_tmp = {'main_post':{}}
            p_tmp['main_post']['content'] = post['caption']
            p_tmp['main_post']['comments'] = post['comments']['contents']
            p_tmp['main_post']['date'] = post['date']
            p_final.append(p_tmp)

    else:
        print("add near_posts for %d posts:"%(len(p_list)))
        for i in range(len(p_list)):
            tag_post_id = p_list[i]['code']
            (usrName,cmtList) = get_usrName_and_cmtList(tag_post_id) #BE5QcuKNI9P
            p_list[i]['comments']['contents'] = cmtList
            p_list[i]['username'] = usrName
            post_time = p_list[i]['date']
            p_list[i] = add_recent_posts(post_time,p_list[i],days)
            if i %10 == 0 :
                sys.stdout.write("%d,"%(i))
        print('')
        p_final = []
        for post in p_list:
            p_tmp = {'main_post':{},'near_posts':[]}
            p_tmp['main_post']['content'] = post['caption']
            p_tmp['main_post']['comments'] = post['comments']['contents']
            p_tmp['main_post']['date'] = post['date']
            for npost in post['recent_posts']:
                npost_dic = {}
                if npost['date'] != p_tmp['main_post']['date'] :
                    try:
                        npost_dic['content'] = npost['caption']
                    except:
                        npost_dic['content'] = []
                    npost_dic['date'] = npost['date']
                    npost_dic['comments'] = npost['comments']['contents']
                    p_tmp['near_posts'].append(npost_dic)
            p_final.append(p_tmp)


    with open("IG_%s.txt"%(searchTag),'w') as f1:
        f1.write(str(p_final))

    # read usage:
    # with open("IG_%s.txt"%(searchTag),'r') as f1:
    #     list_input = eval(f1.read())





if __name__ == '__main__':
    if len(sys.argv) == 3 :
        main(sys.argv[1],float(sys.argv[2]))
    else :
        print('usage:\tIGcrawl.py <search_tag> <near_days>')
        print('example:IGcrawl.py 牛肉湯 3')
        print('near_days > 0 : get this user\'s posts in near_days days')
        print('near_days = -1 : don\'t get this user\'s another posts')
        sys.exit(0)
