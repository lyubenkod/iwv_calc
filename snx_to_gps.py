import re
snx = open("tmp/BGR-RT-xxxxx-TEF-FIX-xxxx-IF_240223_1300.snx2",'r')
started_reading = False
for line in snx:
    if line.startswith("+TROP/SOLUTION"):
        started_reading = True
    elif started_reading:
        if line.startswith(" SUZF00BGR"):
            formatted = line.strip().split(' ')[:3]
            formatted[0] = 3467
            # Reading TROTOT
            formatted[2] = float(formatted[2])/1000
            print(formatted)

        
snx.close()