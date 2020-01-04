from datetime import datetime
import os

def mkdir_p(path):
    try:
        os.makedirs(path, exist_ok=True) #python >= 3.2
    except OSError as exc: #Python > 2.5
        raise #기존 디렉토리에 접근이 불가능 한 경우

def WriteLog(strLog):
    time = datetime.now().strftime('%Y-%m-%d')
    hour = datetime.now().strftime('%H')

    mkdir_p("./Log/%s" % time)

    filename='./Log/%s/[%s]seintec.log' % (time, hour)
    f = open(filename,'a')
    if f:
        date = datetime.now().strftime('%H:%M:%S')

        f.write("[%s %s]" % (time, date) )
        f.write(strLog)
        f.write("\n")
        f.close()