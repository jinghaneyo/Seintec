import sqlite3
import Log

class SQLiteItem:
    m_Conn = None

    def __init__(self):
        pass

    def Open(self, strPath_DB):
        self.m_Conn = sqlite3.connect(strPath_DB)

        if self.m_Conn:
            return True
        else:
            return False

    def Close(self):
        if self.m_Conn:
            self.m_Conn.close()

    def Create_Table(self):
        if None == self.m_Conn:
            return False

        try:
            cur = self.m_Conn.cursor()
            query = '''CREATE TABLE IF NOT EXISTS MENU(
                    SITE TEXT COMMENT '사이트명',
                    MENU TEXT COMMENT '최상단 메뉴',
                    LINK TEXT COMMENT '최상단 메뉴 실제 URL',
                    PRIMARY KEY ( LINK )
                    );'''
            cur.execute(query)

            query = '''CREATE TABLE IF NOT EXISTS ITEM_LINK(
                    ITEM_INDEX INTEGER PRIMARY KEY AUTOINCREMENT,
                    SITE TEXT COMMENT '사이트명',
                    ITEM TEXT COMMENT '아이템 이름',
                    LINK TEXT COMMENT 'MENU 테이블의 LINK 경로의 아이템 URL',
                    JOB_DONE_DT datetime COMMENT '작업 완료 시간'
                    );'''
            cur.execute(query)

            query = '''CREATE TABLE IF NOT EXISTS ITEM_PRICE(
                    ITEM_INDEX INTEGER,
                    ITEM TEXT COMMENT '아이템 이름',
                    SPEC TEXT COMMENT '아이템 SPEC',
                    ITEM_SPEC TEXT COMMENT '아이템 SPEC',
                    PRICE TEXT COMMENT '가격',
                    PRIMARY KEY ( ITEM_INDEX, ITEM, SPEC ) 
                    );'''
            cur.execute(query)
            cur.close()

            return True

        except Exception as e:
            Log.WriteLog('[Exception][Create_Table][ERR = %s]' % e)
            if self.m_Conn:
                self.m_Conn.close()
            return None

    def Select_MenuLink(self, site_name):
        if None == self.m_Conn:
            return None

        menu_map = {}

        try:
            cur = self.m_Conn.cursor()

            query = "SELECT MENU, LINK FROM MENU WHERE SITE = '%s'" % site_name
            cur.execute(query)

            rows = cur.fetchall()
            for row in rows:
                menu_map[row[0]] = row[1]

            cur.close()

            return menu_map

        except Exception as e:
            Log.WriteLog('[Exception][Select_MenuLink][ERR = %s]' % e)
            return None

    def Select_ItemLink(self, site_name):
        if None == self.m_Conn:
            Log.WriteLog("[FAIL][Select_ItemLink] m_Conn is NULL")
            return None

        menu_map = {}

        try:
            cur = self.m_Conn.cursor()

            query = "SELECT LINK, ITEM FROM ITEM_LINK WHERE SITE = '%s'" % site_name
            cur.execute(query)

            rows = cur.fetchall()
            for row in rows:
                menu_map[row[0]] = row[1]

            cur.close()

            Log.WriteLog("[SUCC][Select_ItemLink][COUNT = %d]" % len(menu_map))

            return menu_map

        except Exception as e:
            Log.WriteLog('[Exception][Select_ItemLink][ERR = %s]' % e)
            return None

    def Select_ItemPrice_URL(self, site_name, nStart_Index, nEnd_Index):
        if None == self.m_Conn:
            return None

        try:
            cur = self.m_Conn.cursor()

            if 0 < nEnd_Index:
                query = '''SELECT IL.ITEM_INDEX, IL.LINK, IFNULL(IP.ITEM, ''), IFNULL(IP.SPEC, ''), IFNULL(IP.PRICE,0) FROM ITEM_LINK IL
    LEFT JOIN ITEM_PRICE IP ON IL.ITEM_INDEX = IP.ITEM_INDEX AND IL.SITE = '%s' 
    WHERE IL.ITEM_INDEX > %d AND IL.ITEM_INDEX < %d
    ''' % ( site_name, nStart_Index, nEnd_Index )
            else:
                query = '''SELECT IL.ITEM_INDEX, IL.LINK, IFNULL(IP.ITEM, ''), IFNULL(IP.SPEC, ''), IFNULL(IP.PRICE,0) FROM ITEM_LINK IL
    LEFT JOIN ITEM_PRICE IP ON IL.ITEM_INDEX = IP.ITEM_INDEX AND IL.SITE = '%s' 
    ''' % site_name

            cur.execute(query)

            rows = cur.fetchall()

            cur.close()

            Log.WriteLog( "[SUCC][Select_ItemPrice_URL][COUNT = %d][SITE = %s]" % ( len(rows), site_name) )

            return rows

        except Exception as e:
            Log.WriteLog('[Exception][Select_ItemPrice_URL][ERR = %s]' % e)
            return None

    def Insert_MenuLink(self, site_name, menu_map):
        if None == self.m_Conn:
            return None

        try:
            cur = self.m_Conn.cursor()

            self.m_Conn.execute('BEGIN')

            for data in menu_map:
                query = "INSERT or REPLACE INTO MENU(SITE, MENU, LINK) VALUES ('%s', '%s', '%s');" \
                    % (site_name, data, menu_map[data])
                cur.execute(query)

            self.m_Conn.commit()
            cur.close()

            return True

        except Exception as e:
            self.m_Conn.rollback()
            Log.WriteLog('[Exception][Insert_MenuLink][ERR = %s]' % e)
            return False

    def Insert_ItemLink(self, site_name, href_map):
        try:
            cur = self.m_Conn.cursor()

            self.m_Conn.execute('BEGIN')

            for href in href_map:
                query = "INSERT OR REPLACE INTO ITEM_LINK(SITE, ITEM, LINK) VALUES ('%s', '%s', '%s');" \
                    % (site_name, href_map[href], href)
                cur.execute(query)

            self.m_Conn.commit()
            cur.close()

            return True

        except Exception as e:
            self.m_Conn.rollback()
            Log.WriteLog('[Exception][Insert_ItemLink][ERR = %s]' % e)
            return False
            
    def Insert_ItemPrice(self, df_items, item_index):
        try:
            cur = self.m_Conn.cursor()

            row_max = len(df_items)

            #self.m_Conn.execute('BEGIN')

            for row in range(row_max):
                query = "INSERT OR REPLACE INTO ITEM_PRICE(ITEM_INDEX, ITEM, SPEC, ITEM_SPEC, PRICE) VALUES (%d, '%s', '%s', '%s', '%s');" \
                    % (item_index, df_items.iloc[row]['ITEM'], df_items.iloc[row]['SPEC'], df_items.iloc[row]['ITEM_SPEC'], df_items.iloc[row]['PRICE'])
                cur.execute(query)

            self.m_Conn.commit()
            cur.close()

            return True

        except Exception as e:
            self.m_Conn.rollback()
            Log.WriteLog('[Exception][Insert_ItemPrice][ERR = %s]' % e)
            return False