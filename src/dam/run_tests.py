#! /usr/bin/env python
def get_classes_and_methods(myfile, classname = None):
    import re
    f = open(myfile, 'r+')
    lines = f.readlines()
    mytests = []
    for l in lines:
        m = re.match(r"class (\w+)", l)
        n = re.match(r"    (def) (test_\w+)",l) 
        if m:
            class_name = m.group(1)
        elif n:
            complete_name = class_name + '.' + n.group(2)
            if classname == None:
                mytests.append(complete_name)
            else:
                if class_name == classname:
                    mytests.append(complete_name)
    f.close()
    print 'mytests: ', mytests
    return mytests



if __name__ == "__main__":

    import sys
    import os
    print 'sys.argv[0]: ', sys.argv[0]
    if len(sys.argv) < 2: # run all the tests 
        print 'Run all the tests!'
        os.system('python manage.py test api')
        mytests = get_classes_and_methods('api/uploading_testcases.py')
        for t in mytests:
            os.system('python api/uploading_testcases.py %s' % t)
            print 'single test: ', t
    elif len(sys.argv) == 2:
        print 'sys.argv[1]: ', sys.argv[1]
        if sys.argv[1].find('MultiPurpose') == -1:
            print 'Run all the tests in a class or one test only!'
            os.system('python manage.py test %s' % sys.argv[1][4:])
        else:
            howmany = sys.argv[1].split('.')
            if len(howmany) > 2: # api.classname.methodname, 1 test only
                print 'Run one test only!'
                os.system('python api/uploading_testcases.py %s' % sys.argv[1][4:])
            elif len(howmany) == 2: # api.classname, all tests in the class
                print 'Run all the tests in a class!'
                mytests = get_classes_and_methods('api/uploading_testcases.py', sys.argv[1][4:])
                for t in mytests:
                    os.system('python api/uploading_testcases.py %s' % t)
            
