# -*- coding: utf-8 -*-
import requests
from scrapy.selector import Selector  # 可以直接应用scrapy中的 selector ，而不是应用 lxml库
import MySQLdb

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

conn = MySQLdb.Connect(host='localhost', user='root', passwd='root', db='scrapyspider', charset='utf8')
cur = conn.cursor()


def crawl_ips():
    # 爬取xici上的免费代理ip；用requests库完成

    header = {
        'User-Agent': 'User-Agent: Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE) '
    }

    # url = 'http://www.xicidaili.com/nn/'

    for i in range(0, 500):
        # url = url+str(i)
        #
        # re = requests.get(url, headers=header)
        re = requests.get('http://www.xicidaili.com/nn/{0}'.format(i), headers=header)

        selector = Selector(text=re.text)

        all_trs = selector.css('#ip_list tr')

        ip_list=[]
        for tr in all_trs[1:]:
            speed_str = tr.css('.bar::attr(title)').extract()[0]
            if speed_str:
                speed = float(speed_str.split(u'秒')[0])
            all_text = tr.css('td::text').extract()
            ip = all_text[0]
            port = all_text[1]
            gaoni = all_text[4]
            proxy_type = all_text[5]
            time = all_text[-1]

            print all_text

            ip_list.append((ip,port,gaoni,proxy_type,speed,time))




            # cur.execute(
            #     "insert into ip_pool(ip,port,gaoni,type,speed,time) VALUES('{0}','{0}','{0}','{0}',{0},'{0}');".format
            #     (ip, port, gaoni, proxy_type, speed, time)
            # )
            # conn.commit()


        for i in ip_list:
            cur.execute(
                "insert into ip_pool(ip,port,gaoni,type,speed,time) VALUES('{0}','{1}','{2}','{3}',{4},'{5}');".format
                (i[0], i[1], i[2], i[3], i[4], i[5])
            )
            conn.commit()


class GetIP(object):

    def delete_ip(self, ip):
        delete_sql = '''
            DELETE FROM ip_pool WHERE ip='{0}'
        '''.format(ip)
        cur.execute(delete_sql)
        conn.commit()
        return True

    def judge_ip(self, ip, port):
        # 判断 ip 是否可用
        http_url = 'https://www.baidu.com'
        # proxy_url = 'http://'+ str(ip) +':'+ str(port)
        proxy_url = 'http://{0}:{1}'.format(ip, port)
        try:
            proxy_dict={
                'http': proxy_url
            }
            re = requests.get(http_url, proxies=proxy_dict)
            return True
        except Exception as e:
            print ('invalid ip and port')
            self.delete_ip(ip)
            return False
        else:
            code = re.status_code
            if code >= 200 and code< 300:
                print ('effective ip')
                return True
            else:
                print ('invalid ip and port')
                self.delete_ip(ip)
                return False

    def get_random_ip(self):
        # 从数据库随机获取一个ip
        random_sql = '''
             SELECT ip,port FROM ip_pool
             ORDER BY RAND()
             LIMIT 1
        '''
        result = cur.execute(random_sql)
        for ip_info in cur.fetchall(): # 取出来的 ip_info 是一个 tuple 类型
            ip = ip_info[0]
            port = ip_info[1]
            judge_re = self.judge_ip(ip, port)
            if judge_re:
                return 'http://{0}:{1}'.format(ip, port)
            else:
                return self.get_random_ip()


if __name__=='__main__':
    get_ip = GetIP()
    get_ip.get_random_ip()

crawl_ips()
