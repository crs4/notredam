"""
Usage: python notredam.py [options] [args]

Arguments:
    run   run the batch processor and a development server
            Options:
                --runserver: start the django development server. Port and address can be passed with the option --address
            Usage:
                python notredam.py run
                python notredam.py --runserver run (run the development server on 127.0.0.1:8000)
                python notredam.py --runserver --address=10000 run (run the development server on 127.0.0.1:10000)
                python notredam.py --runserver --address=0.0.0.0:10000 run (run the development server on all interface listening on port 10000)
        
    stop    stop the batch processor and the server if running


"""

import os
import sys
import subprocess
import getopt
import shutil

INSTALLATIONPATH = os.path.join(os.getenv('HOME'), ".dam"  )

def check_installed():
    if not os.path.exists(INSTALLATIONPATH):
        os.mkdir(INSTALLATIONPATH)
        os.mkdir(os.path.join(INSTALLATIONPATH,  'log'))
        os.mkdir(os.path.join(INSTALLATIONPATH,  'thumbs'))
        shutil.copyfile('/opt/notredam/dam/config.py',  os.path.join(INSTALLATIONPATH,  'config.py'))        

check_installed()

def _run(cmdline,  file_name,  stdout = None):
    if stdout is None:
        stdout = open(os.devnull, "w")
    
    p = subprocess.Popen(cmdline, stdout = stdout,  stderr=subprocess.STDOUT, env= {'PYTHONPATH':'/opt/mediadart/:/opt/notredam/', 'HOME':os.getenv('HOME')})
#    p = subprocess.Popen(cmdline,  stdout=stdout, )
    path = os.path.join(INSTALLATIONPATH,  file_name  + '.pid',  )
    kill_proc(file_name)
    
    f = open(path, 'w')
    f.write(str(p.pid))
    f.close()
    

def check_db_created():
    installed = os.path.join(INSTALLATIONPATH,  'installed')
    if not os.path.exists(installed):
        sys.path.append(INSTALLATIONPATH)
        import config
        if config.DATABASE_ENGINE== 'mysql':
            print 'INSERT MYSQL ROOT PASSWORD'
            subprocess.call(['mysql',  '-uroot',  '-p', '-e', "create user %s identified by '%s'; GRANT ALL on *.* to '%s'"%(config.DATABASE_USER, config.DATABASE_PASSWORD, config.DATABASE_USER)])
            #subprocess.call(['mysqladmin',  '-u%s'%config.DATABASE_USER,  'create', config.DATABASE_NAME , '-p%s'%config.DATABASE_PASSWORD, '--default-character-set=utf8'])
            subprocess.call(['mysql',  '-u%s'%config.DATABASE_USER, '-p%s'%config.DATABASE_PASSWORD,  '-e', 'create database %s character set utf8;'%config.DATABASE_NAME])
            
        subprocess.call(['/usr/bin/python',  '/opt/notredam/dam/manage.py',  'syncdb',  '--noinput'])
        subprocess.call(['/usr/bin/python',  '/opt/notredam/dam/manage.py',  'loaddata',  '/opt/notredam/dam/initial_data.json'])
        f = open(installed,  'w')
        f.close()


        

def run(runserver,  address):
    check_db_created()    
    if runserver:
        stdout = open(os.path.join(INSTALLATIONPATH,  'log/dam.log'),  'w')
        if address:
            _run(['/usr/bin/python',  '/opt/notredam/dam/manage.py',  'runserver',    '--noreload',  address],  'server',  stdout)             
        else:
            _run(['/usr/bin/python',  '/opt/notredam/dam/manage.py',  'runserver', '--noreload'],  'server', stdout )        
            
        print 'running server'
    _run(['/usr/bin/python',  '/opt/notredam/dam/start_mediadart.py'],  'mediadart_processor')  
    print 'running batch processor'
    
    
def kill_proc(name):    
    
    file_path = os.path.join(INSTALLATIONPATH,  name + '.pid')
    if os.path.exists(file_path):
        try:
            f = open(file_path, 'r')
            pid = f.read()
            f.close()
            os.kill(int(pid),  12)
            os.remove(file_path)
        except Exception,  ex:       
            print ex
            return False
        return True
    return False

def stop():
    
    server_stopped = kill_proc('server')
    if server_stopped:
        print 'server stopped'
    bp_stopped = kill_proc('mediadart_processor')
    if bp_stopped:
        print 'batch processor stopped'
    
    
def main():
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "runserver",  "address="])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
        
    if len(args) < 1: 
        print 'no args passed'
        print "for help use --help"
        sys.exit(2)
    
    if args[0] == 'run':
        run_server = False
        address = None
        for o, a in opts:
            if o == '--address':
                address = a
            
            if o =='--runserver':        
                run_server = True
            
        run(run_server,  address)
            
                
    elif args[0] == 'stop':
        stop()
    else:
        print 'unknown args'
        print "for help use --help"
        sys.exit(2)
    
if __name__ == "__main__":
    main()
