import psutil
import subprocess
import configparser
import time

def find_procs_by_name(proc_name):
    proc_list = []
    for p in psutil.process_iter(attrs=['name']):
        if p.info['name'] == proc_name:
                proc_list.append(p)

    return proc_list

if __name__ == '__main__':

        config = configparser.ConfigParser()
        config.read('conf.ini')
        exe_path = config['COMMON']['EXE_PATH']
        check_interval = int(config['COMMON']['CHECK_PROC_INTERVAL'])
        if 1 > check_interval:
                check_interval = 60

        check_py = exe_path + '/main.py'

        while True:
                try:
                        bFound_Proc = False
                        bZombie = False
                        ps_zombie = None
                        ps_list = find_procs_by_name('Python')
                        for ps in ps_list:
                                if exe_path != ps.cwd():
                                        continue

                                if 1 < len(ps.cmdline()):
                                        if check_py == ps.cmdline()[1]:
                                                bFound_Proc = True

                                                if psutil.STATUS_ZOMBIE == ps.status():
                                                        bZombie = True
                                                        ps_zombie = ps

                        if True == bFound_Proc:
                                if True == bZombie:
                                        # 좀비가 됐다면, 죽이고 다시 살리자 
                                        ps_zombie.terminate()

                                        time.sleep(5)
                                        subprocess.call('python3 %s/main.py &' % exe_path, shell=True)
                                else:
                                        print('Running')
                        else:
                                print('Not Runing')
                                subprocess.call('python3 %s/main.py &' % exe_path, shell=True)

                        ps_list = None

                except Exception as e:
                        print('[Exception][Err = %s]' % e)

                time.sleep(check_interval)
                