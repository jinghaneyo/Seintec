import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import Log

class Scraping:
    m_strSiteName = ''
    m_soup = ''

    def __init__(self):
        pass

    def GetURL(self, strURL, wait_second):
        try:
            res = requests.get(strURL)

            if res:
                #self.m_soup = BeautifulSoup(res.content, 'html.parser')
                self.m_soup = BeautifulSoup(res.content, 'lxml')
                return True
            else:
                return False
        except Exception as e:
            Log.WriteLog('[Exception][GetURL][ERR = %s][URL = %s]' % (e, strURL) )
            # 추출한 데이타는 리턴 , 추후 이 값만큼 디비에 추가
            return False
    
    def FindAll(self, strTag):
        tags = self.m_soup.find_all('title')

        return tags