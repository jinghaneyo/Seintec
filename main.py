# -*- coding: utf-8 -*-

import pandas as pd
from openpyxl import load_workbook
from datetime import datetime
import configparser
import schedule
import time
import sch
import sys
import re

import SQLite_Item
import Myungin
import Log

class Task:
    m_sch = ''
    m_start  = 0
    m_end = 40000

class Config:
    m_log_sch = ''
    m_log_keep_day = 30

    m_complete_sch = ''

    m_Task = []
    m_TaskNow = None

def SaveExcel(df, path, sheet_nm):
    writer = pd.ExcelWriter(path, engine='xlsxwriter')
    #writer = pd.ExcelWriter(path, engine='openpyxl')
    df.to_excel(writer, sheet_name=sheet_nm)
    writer.save()
    #writer.close()

def WriteContents(menu_map, menu, href_map, href, Item):
    strContents = "[Menu = " + menu_map[menu][0]
    strContents += "] [Menu Items = " + menu_map[menu][1]
    strContents += "] [Product = " + href_map[href]
    strContents += "] [상품 = " + Item
    strContents += "]\n"

    Log.WriteLog(strContents)

def Get_MenuLink(site, db):
    # sqlite 에 저장되어 있는 링크를 얻어온다 
    menu_map = db.Select_MenuLink(site.m_strSiteName)

    # sqlite 에 링크 데이타가 없으면 직접 URL 해서 얻어온다 
    if (None == menu_map) or (0 == len(menu_map)):
        menu_map = site.GetRootLink()

        # 정상적으로 URL 을 얻어왔으면, sqlite 에 넣어서, 다음에는 sqlite에서 얻어온 링크를 사용하도록 하자
        if menu_map:
            if False == db.Insert_MenuLink(site.m_strSiteName, menu_map):
                Log.WriteLog("[FAIL] SQLite_Insert_Menu")
        else:
            Log.WriteLog("[FAIL] GetRootLink")

    return menu_map

def Get_ItemLink_and_InsertDB(site, db, menu_map):
    bComplete = True

    # DB에서 상세 URL 리스트를 얻는다 
    href_map = db.Select_ItemLink(site.m_strSiteName)

    # 없으면 직접 얻오자 
    if (None == href_map) or (0 == len(href_map)):
        bRet, href_map = site.GetItemLink_All(menu_map)

        # DB 에 넣어서 다음에는 DB로부터 읽어들이도록 한다 
        if True == db.Insert_ItemLink(site.m_strSiteName, href_map):
            if True == bRet:
                # 완료 태그 넣기
                href_map = None
                href_map = {}
                href_map['-- COMPLETE --'] = '-- COMPLETE --'
                db.Insert_ItemLink(site.m_strSiteName, href_map)
            else:
                bComplete = False
        else:
            bComplete = False
    else:
        if '-- COMPLETE --' in href_map:
            # 정상적으로 다 로딩이 완료 됐다  
            pass
        else:
            # URL 얻는 도중 에러(타임아웃 등)인해 중지될수도 있으니, Db값과 비교하여 없는게 있으면 다시 얻오온다
            for menu in menu_map:
                href_map_temp = site.GetItemLink(menu[1])

                # 없으면 추가 
                for href in href_map_temp:
                    if href in href_map:
                        pass
                    else:
                        href_map[href] = href_map_temp[href]

                        # DB 에 넣어서 다음에는 DB로부터 읽어들이도록 한다 
                        if False == db.Insert_ItemLink(site.m_strSiteName, href_map):
                            bComplete = False

            if True == bComplete:
                # 완료 태그 넣기
                href_map = None
                href_map = {}
                href_map['-- COMPLETE --'] = '-- COMPLETE --'
                db.Insert_ItemLink(site.m_strSiteName, href_map)

    return bComplete

def Get_ItemPrice_and_InsertDB(site, db, Task_Start, Task_End):
    #df = pd.DataFrame(columns=['URL','ITEM', 'PRICE'])

    # db 에 있는 아이템 가격 리스트를 얻는다.
    db_price_url = db.Select_ItemPrice_URL(site.m_strSiteName, Task_Start, Task_End)

    if None == db_price_url:
        Log.WriteLog("[Select_ItemPrice_URL is None][site = %s][Start = %d][End = %d]" % \
            ( site.m_strSiteName, Task_Start, Task_End) )
        #return df
        return

    #nRow_Index = 1
    # 가격이 없는 URL만 다시 진행한다 
    # (이전 실행 시 진행 하다 중지가 됐을 경우다)
    for price in db_price_url:
        # 없으면 이전 작업 시 실패니 다시 시도
        if price[4] == 0:
            df_items = site.Get_ItemPrice(price[1])

            if df_items.empty:
                pass
            else:
                db.Insert_ItemPrice(df_items, price[0])

                # df.loc[nRow_Index] = df_items
                # nRow_Index = nRow_Index + 1
        # else:
        #     # 가격이 있는 경우는 그대로 데이타프레임에 넣어서 완료 시 엑셀로 저장한다
        #     row_list = []
        #     row_list.append(price[1])
        #     row_list.append(price[2])
        #     row_list.append(price[3])
        #     df_items = pd.DataFrame(row_list)

        #     df.loc[nRow_Index] = row_list
        #     nRow_Index = nRow_Index + 1

    #return df

def SelectDB_Price(db, site_name, nStart, nEnd):
    df = pd.DataFrame(columns=['URL','ITEM', 'SPEC', 'PRICE'])

    # db 에 있는 아이템 가격 리스트를 얻는다.
    db_price_url = db.Select_ItemPrice_URL(site_name, nStart, nEnd)

    if None == db_price_url:
        Log.WriteLog("[SelectDB_Price is None][site = %s]" % site_name)
        return df

    nRow_Index = 1
    for price in db_price_url:
        row_list = []
        row_list.append(price[1])
        row_list.append(price[2])
        row_list.append(price[3])
        row_list.append(price[4])

        df.loc[nRow_Index] = row_list
        nRow_Index = nRow_Index + 1

    return df

def Export_DB_Excel(db, site_name, nStart, nEnd):
    df = pd.DataFrame(columns=['URL','ITEM', 'SPEC', 'PRICE'])

    df = SelectDB_Price(db, site_name, nStart, nEnd)

    if 1 < len(df):
        Log.WriteLog("Save Excel")
        SaveExcel(df, 'item.xlsx', site_name)

def Scraping(task_start, task_end):
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "------------------- start ------------------- "
    Log.WriteLog(time)

    db = SQLite_Item.SQLiteItem()
    db.Open("./menu.db")
    db.Create_Table()

    arr_site = [ ]
    arr_site.append( Myungin.Myungin() )

    for site in arr_site:
        bComplete = False

        # 메뉴 링크 얻기 
        menu_map = Get_MenuLink(site, db)
        if (None != menu_map) and (0 < len(menu_map)):
            # 아이템별 URL 리스트를 얻는다 
            # 바로 sqlite 로 넣는다
            Get_ItemLink_and_InsertDB(site, db, menu_map)

            # 가격 얻기 
            Get_ItemPrice_and_InsertDB(site, db, task_start, task_end )
        else:
            Log.WriteLog("[FAIL] Get_MenuLink is NULL")

        if True == bComplete:
            Log.WriteLog("[SUCC] 작업 완료")
        else:
            Log.WriteLog("[FAIL] 작업 실패 [site = %s]" % site.m_strSiteName)

    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "------------------- end  -------------------" 
    Log.WriteLog(time)

def Log_Delete( keep_day ):
    pass

def Load_SCH():
    conf = Config()

    # conf.ini 설정 로드 
    config = configparser.ConfigParser()
    config.read("conf.ini")
    conf.m_log_sch = config['COMMON']['LOG_SCH']
    conf.m_log_keep_day = int(config['COMMON']['LOG_KEEP_DAY'])

    # conf.m_TaskNow = Task()
    # conf.m_TaskNow.m_sch = config['SCH']['TASK_NO']
    # conf.m_TaskNow.m_start = int(config['SCH']['TASK_START']) 
    # conf.m_TaskNow.m_end = int(config['SCH']['TASK_END']) 

    count = int(config['SCH']['COUNT'])

    for cnt in range(1, count):
        task = Task()
        task.m_sch = config['SCH']['TASK_SCH_%d' % cnt]
        task.m_start = int(config['SCH']['TASK_START_%d' % cnt])
        task.m_end = int(config['SCH']['TASK_END_%d' % cnt])
        conf.m_Task.append(task)

    conf.m_complete_sch = config['COMPLETE']['TASK_SCH']

    return conf

def Collect_Price():
    Scraping(0, 2000000)

    #conf = Load_SCH()

    # TASK_NOW = YES 인지 확인
    #if 'YES' == conf.m_TaskNow.m_sch:
    #Scraping(conf.m_TaskNow.task_start, conf.m_TaskNow.task_end)
    # else:
    #     # 로그를 일단 지우고 시작한다.
    #     Log_Delete( int(conf.m_log_keep_day) )

    #     # 스케줄 작업 등록 및 시작 
    #     cron = sch.Cron()
    #     cron.add(conf.m_log_sch, Log_Delete( int(conf.m_log_keep_day) )) 
    #     for task in conf.m_Task:
    #         cron.add(task.m_sch, Scraping, args=(task.m_start, task.m_end) ) 
    #     cron.add(conf.m_complete_sch, Save_Excel) 
    #     cron.run()

def Save_Excel():
    db = SQLite_Item.SQLiteItem()
    db.Open("./menu.db")

    arr_site = [ ]
    arr_site.append( Myungin.Myungin() )

    for site in arr_site:
        Export_DB_Excel(db, site.m_strSiteName, 0, 20000)


def Extract_Item_Price(item_Text):
    nPos_End = int( item_Text.rfind(')') )
    nPos_Start = int( item_Text.rfind('(') )

    # 가격을 제거하고 넣자
    price = item_Text[nPos_Start:nPos_End+1]

    # 가격 뽑아 내기 
    price = item_Text[nPos_Start+1:nPos_End]
    price = price.replace('원','')
    price = price.replace(',','')

    return price

def Test_Price():
    price_array = ['1111 쎄니.스트레너2페럴(SUS304)1S (118840원)', \
                   '(1858701) 탱크커버 MK-M5001-SUS304 Ø200', \
                   '(2222) 매직보온테이프(MK)청4*13M*60롤/난연 (118840원)', \
                   '스텐멀티볼밸브20K/FULL(MK)100A(4)-청색 (118840원)', \
                   '철편장니플(MK)50A (118840원)', \
                   '흑중니플(MK).20A(65L) (118840원)', \
                   '흑나사후렌지(인테리어용)15A(125) (118840원)', \
                   '안전형정망치-다가네(MK)SD-220 (118840원)', \
                   '스페이스플랫치즐-다가네(MK)W-50(마끼다0810,계양38전용) (118840 원)', \
                   '파워에어호스8*100M (118840원)', \
                   '분무용고압호스8.5*100M(니플포함) (118840원)', \
                   '칼라플렉스호스6*100M(적,청,흑,녹,백) (118840원)', \
                   '쎄니.체크밸브2메일(SUS304)-SMS 1S (118840원)', \
                   '스텐멀티볼밸브20K/FULL(MK)8A(180)-적색 (118840원)', \
                   'GUN세트(118840원)', \
                   'GUN세트', \
                   '자동에어호스(폴리우레탄편조호스)8*12*15m (118840 원)' ]

    row_index = 0

    for strPrice in price_array:

        print('------------------------------------------------')
        # 양쪽 공백 제거
        item_Text = strPrice.strip()

        price=''

        # 자재이름과 스펙을 분리
        # 앞에서 부터 숫자를 기준으로 왼쪽은 자재 이름 오른쪽은 스펙
        #p = re.compile('([a-zA-Z가-힝\.-]+)(.*)(\([0-9\s]+원\))')
        #p = re.compile('([a-zA-Z가-힝\.-]+)(\({1}[a-zA-Z가-힝]+\){1})*(.*)(\([0-9\s]+원\))*')
        p = re.compile('(\([0-9]+\)\s)*([a-zA-Z가-힝\.-]+)(\({1}[a-zA-Z가-힝]+\){1})*(.*)(\([0-9\s]+원\))*')
        m = p.match(item_Text)

        if None != m:
            item1 = m.group(1)
            item2 = m.group(2)
            spec = m.group(3)
            price = m.group(4)

            print('[ITEM1 = %s][ITEM2 = %s][SPEC = %s][PRICE = %s]' % (item1, item2, spec, price))
        else:
            print('m is None')
            continue

    row_index = row_index + 1

if __name__ == '__main__':

    # nCount = 1
    # while True:
    #     time.sleep(1)
    #     print('sleep %d' % nCount)
    #     nCount = nCount + 1

    #Save_Excel()

    if 1 < len(sys.argv):
        if 'export' == sys.argv[1] and 'excel' == sys.argv[2]:
            Save_Excel()
        else:
            print('Invalid args')
            print('Help :')
            print('         export [excel]')
    else:
        #Test_Price()
        Collect_Price()