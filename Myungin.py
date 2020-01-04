import Scraping
import re
import pandas as pd
import Log

class Myungin(Scraping.Scraping):
    m_url='http://www.myoung119.com'

    def __init__(self):
        self.m_strSiteName = '명인코리아'

    def GetRootLink(self):
        try:
            menu_map = {}

            vec_except_menu = ['신상품', '★★프로모션★★', '여름상품모음', '겨울상품모음', '★명인코리아 상품관★', '★인테리어 자재★', '임의결제(배송비결제)', '베스트상품', '49.위생1-수전류', '50.위생2-액세서리외', '51.위생3-사우나자재/도기류', '초경/측정/절삭', '공작', '79.냉난방용품', '80.포장', '81.기타']
            self.GetURL(self.m_url, 3)

            tables = self.m_soup.find_all('td', {'class':'catebar1'})

            for table in tables:
                if 0 == vec_except_menu.count(table.text):
                    a = table.find('a')
                    if a:
                        #Log.WriteLog("[URL = %s][text = %s]\n" % (a.text, a.get('href')))
                        menu_map[a.text] = self.m_url + a.get('href')

            return menu_map

        except Exception as e:
            Log.WriteLog('[Exception][GetRootLink][ERR = %s]' % e)
            return None

    def GetItemLink_All(self, menu_map):
        href_map = {}
        url = 'http://www.myoung119.com/shop/goods/'
        item_url = ''

        try:
            for menu in menu_map:
                item_url = menu_map[menu]
                #Log.WriteLog("[URL = %s]\n" % item_url)
                if True == self.GetURL(menu_map[menu], 2):
                    divs_list = self.m_soup.select('div > a.large_t')
                    if divs_list:
                        for div in divs_list:
                            Log.WriteLog("[text = %s][URL = %s]\n" % (div.text, div.get('href')))
                            href_map[url + div.get('href')] = div.text
        except Exception as e:
            Log.WriteLog('[Exception][GetRootLink][ERR = %s][URL = %s]' % (e, item_url) )
            # 추출한 데이타는 리턴 , 추후 이 값만큼 디비에 추가
            return False, href_map

        return True, href_map

    def GetBasePrice(self):
        forms = self.m_soup.find_all('form', {'name':'frmView'})
        if None == forms or 0 == len(forms):
            return None

        # list 로 넘어오나 실제로는 1개 밖에 없다  
        for frm in forms:
            items = frm.find_all('tr')
            for itm in items:
                price = itm.find('th')
                if None != price and '판매가격 :' == price.text:
                    price = itm.find('b')
                    price = price.text.replace('원','')
                    BasePrice = price.replace(',','')
                    # 가격을 찾았으니 리턴
                    return BasePrice

        return None

    def Extract_Item_Price(self, item_Text):
        nPos_End = int( item_Text.rfind(')') )
        nPos_Start = int( item_Text.rfind('(') )

        # 가격을 제거하고 넣자
        price = item_Text[nPos_Start:nPos_End+1]

        # 가격 뽑아 내기 
        price = item_Text[nPos_Start+1:nPos_End]
        price = price.replace('원','')
        price = price.replace(',','')

        return price

    def GetItemLink(self, item_url):
        href_map = {}

        if True == self.GetURL(item_url, 2):
            item_tables = self.m_soup.find_all('span', {'id':'price'})
            for item in item_tables:
                #href_map[item.text] = self.m_url + item.get('href')
                href_map[self.m_url + item.get('href')] = item.text

        return href_map

    def Find_Price(self, top, item_url, BasePrice, item_base):
        df = pd.DataFrame(columns=['URL','ITEM', 'SPEC', 'ITEM_SPEC', 'PRICE'])
        row_index = 0
        item_Text = ''

        try:
            items_option = top.find_all('option')
            for item in items_option:
                if None == item.text:
                    continue
                if -1 < item.text.find('== 옵션선택 =='):
                    continue
                if -1 < item.text.find('()ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ (0원)'):
                    continue

                row_list = []
                row_list.append(item_url)

                # 양쪽 공백 제거
                item_Text = item.text.strip()
                item_Text = item_Text.replace('(견적)','')
                item_Text = item_Text.replace('[견적]','')

                price=''

                # 자재이름과 스펙을 분리
                # 앞에서 부터 숫자를 기준으로 왼쪽은 자재 이름 오른쪽은 스펙
                #p = re.compile('([a-zA-Z가-힝\.-]+)(.*)(\([0-9\s]+원\))')
                #p = re.compile('([a-zA-Z가-힝\.-]+)(\({1}[a-zA-Z가-힝]+\){1})*(.*)(\([0-9\s]+원\))*')
                p = re.compile('(\([0-9]+\)\s)*([a-zA-Z가-힝\.-]+)(\({1}[a-zA-Z가-힝]+\){1})*(.*)(\([0-9\s]+원\))*')
                m = p.match(item_Text)

                if None != m:
                    item_base = m.group(2)
                    if None != m.group(3):
                        item_base = item_base + m.group(3)
                    item_spec = m.group(4)
                    if None != m.group(5):
                        price = m.group(5)
                        price = item_spec.replace('(','')
                        price = item_spec.replace(')','')
                        price = item_spec.replace('원','')
                    else:
                        price = BasePrice

                    # item_base = item_spec.replace('(견적)','')
                    # item_base = item_spec.replace('[견적]','')
                    # item_spec = item_spec.replace('(견적)','')
                    # item_spec = item_spec.replace('[견적]','')

                    item_base = item_base.strip()
                    item_spec = item_spec.strip()
                    price = price.strip()

                    row_list.append(item_base)
                    row_list.append(item_spec)
                    row_list.append(item_Text)
                    row_list.append(price)

                    #print('[ITEM1 = %s][ITEM2 = %s][SPEC = %s][PRICE = %s]' % (item1, item2, spec, price))
                else:
                    #print('m is None')
                    continue

                # # 스펙 뽑아 내기
                # # 스펙 앞에 (숫자) 형태가 있으면 제거 한다
                # nStart = item_Text.find('(')
                # nEnd = item_Text.find(')')
                # if (-1 != nStart) and (-1 != nEnd) and 0 == nStart:
                #     item_Text = item_Text[nEnd+1:len(item_Text)]

                # base_array = item_Text.split()

                # if '원)' in item_Text:
                #     price = base_array[len(base_array) - 1]
                #     item_spec = base_array[len(base_array) - 2]
                #     price = self.Extract_Item_Price( price )

                #     item_Text = ''
                #     total = len(base_array) - 1 
                #     for i in range(total):
                #         item_Text += base_array[i]
                #         item_Text += ' '

                #     item_base = ''
                #     total = total - 1
                #     for i in range(total):
                #         item_base += base_array[i]
                #         item_base += ' '

                #     item_Text = item_Text.strip()
                #     item_base = item_base.strip()

                #     item_spec = item_spec.replace('(견적)','')
                #     item_spec = item_spec.replace('[견적]','')

                #     row_list.append(item_base)
                #     row_list.append(item_spec)
                #     row_list.append(item_Text)
                #     row_list.append(price)
                # else:
                #     item_spec = base_array[len(base_array) - 1]

                #     item_base = ''
                #     total = len(base_array) - 1
                #     for i in range(total):
                #         item_base += base_array[i]
                #         item_base += ' '

                #     item_base = item_base.strip()

                #     item_spec = item_spec.replace('(견적)','')
                #     item_spec = item_spec.replace('[견적]','')

                #     row_list.append(item_base)
                #     row_list.append(item_spec)
                #     row_list.append(item_Text)
                #     row_list.append(BasePrice)

                df.loc[row_index] = row_list
                row_index = row_index + 1

                Log.WriteLog('[Find_Price][ITEM = %s][SPEC = %s][ITEM_SPEC = %s][PRICE = %s][URL = %s]' %\
                    (row_list[1], row_list[2], row_list[3], row_list[4], item_url) )

            return df
        except Exception as e:
            Log.WriteLog('[Exception][Find_Price][ERR = %s][TEXT = %s][URL = %s]' % (e, item_Text, item_url) )
            # 추출한 데이타는 리턴 , 추후 이 값만큼 디비에 추가
            return df

    def Get_ItemPrice(self, item_url):
        #df = pd.DataFrame(columns=['URL','ITEM', 'PRICE'])
        df = pd.DataFrame()
        try:
            if True == self.GetURL(item_url, 10):
                # 기본 가격 얻기 
                BasePrice = self.GetBasePrice()
                if None == BasePrice:
                    Log.WriteLog('[Get_ItemPrice][Not Exist price][URL = %s]' % item_url)
                    return df

                # 아이템 이름 가져오기 
                item_base = self.m_soup.select_one('#goods_spec > form > div:nth-child(6) > b')
                item_base = item_base.text
                item_base = item_base.replace("\r\n", "")
                item_base = item_base.strip()   # 양쪽 공백 제거 

                # 제일 뒤에 (숫자xxx) 형태는 자른다
                index_left = item_base.find('(')
                if -1 != index_left:
                    index_right = item_base.find(')', index_left)
                    if -1 != index_right:
                        item_base = item_base[0:index_left]
                        item_base = item_base.strip()   # 양쪽 공백 제거 

                # 기본 가격이 0이고 베이스 이름에서 '견적'이 있으면, 기본 가격을 견적이라고 넣자 
                if '0' == BasePrice:
                    if -1 != item_base.find('견적'):
                        BasePrice = '견적'

                tops = self.m_soup.find_all('table', {'class':'top'} )
                for top in tops:
                    th_list = top.find_all('th', {'valign':'top'})
                    if None == th_list:
                        continue
                    
                    if 1 == len(th_list):
                        # 1개만 있을 경우는 무조건 가격이다
                        df_price = self.Find_Price(top, item_url, BasePrice, item_base)
                        if False == df_price.empty:
                            df = df.append(df_price)
                    else:
                        for th in th_list:
                            if '관경별선택 :' == th.text or '관경별가격 :' == th.text or '용량별가격 :' == th.text or '모델명/규격 :' == th.text:
                                df_price = self.Find_Price(top, item_url, BasePrice, item_base)

                                if False == df_price.empty:
                                    df = df.append(df_price)

                return df
            
        except Exception as e:
            Log.WriteLog('[Exception][Get_ItemPrice][ERR = %s][URL = %s]' % (e, item_url) )
            # 추출한 데이타는 리턴 , 추후 이 값만큼 디비에 추가
            return df

        return df