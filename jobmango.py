#!/usr/local/bin/python3
import time
import os
import datetime
from fish import catch

'''
 执行方式
 (1) python3 jobman.py 00 server --> server mode
 (2) python3 jobman.py 00 client --> client mode
'''

mylogo=r'''
      ___   ______   _______  ___      ___      __     _____  ___   _______    ______    
     |"  | /    " \ |   _  "\|"  \    /"  |    /""\   (\"   \|"  \ /" _   "|  /    " \   
     ||  |// ____  \(. |_)  :)\   \  //   |   /    \  |.\\   \    (: ( \___) // ____  \  
     |:  /  /    ) :):     \/ /\\  \/.    |  /' /\  \ |: \.   \\  |\/ \     /  /    ) :) 
  ___|  (: (____/ //(|  _  \\|: \.        | //  __'  \|.  \    \. |//  \ __(: (____/ //  
 /  :|_/ )        / |: |_)  :).  \    /:  |/   /  \\  \    \    \ (:   _(  _\        /   
(_______/ \"_____/  (_______/|___|\__/|___(___/    \___)___|\____\)\_______) \"_____/    
'''
if __name__ == "__main__":
    scr = catch.screen()
    dot = r"-\|/"
    # 在config.ini中已经设定 INPUT_QUEUE = `pwd`/iqueue, OUTPUT_QUEUE = `pwd`/oqueue
    # 监看的资料夹 ./iqueue/{os.sys.argv[1]}/, default = '00'
    scr.cls()
    print(mylogo)
    try:
        queue_index = os.sys.argv[1]
    except:
        queue_index = '00'
    # 程序执行的模式 default server
    try:
        act = 'client' if os.sys.argv[2] == 'client' else 'server'
    except:
        act = 'server'
    i=0
    while catch.start_momo:     # ctrl_c -> :q 会 exit loop,ctrl_c -> :r 会restart
        scr.reverse("开始监视工作")
        # start_momo, go_momo是控制LOOP使用，当ctrl_c :q :r之后，会false，然后exit loop
        catch.momo, catch.go_momo = catch.FileObserver(queue_index, act), True
        catch.momo.start()
        while catch.go_momo:    # ctrl_c -> :q, ctrl_c -> :r 都会exit this loop
            i=(i+1)%4
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),dot[i],end='\r')
            time.sleep(1)
        del catch.momo
    scr.reverse("结束监视工作")
