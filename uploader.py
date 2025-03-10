''' ==================================================================
    uploader2.py - Micropython program / file loader

    s.case       - 2/21/25
    ------------------------------------------------------------------

    Testing of libraries for esp loader with Raspi Pi (not pico)

    RPI.GPIO no longer supports interrupts/events
             Fine for twiddling bits. lgpio is just a shim
             for RPi.GPIO so it no longer works either
             GPIO.add_event_detect() now throws error in Bullseye
             and Bookworm. (Testing with kernel 5.10.103 Bullseye)
 

    pigpio  Seems to be supporting event callbacks for buttons via
            gpio. Uses special daemon [$ sudo pigpiod &]  in background         

    mpfshell==0.9.1 & works.

    luma working on SSD1306, just need to make screens persistent
    -------------------------------------------------------------------

    v.2     Working. Needs ls, lls to put more that one file on the
            display at a time. Adding com port selection

    
    ===================================================================   

'''


import RPi.GPIO as GPIO
import pigpio
import os
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from time import sleep

rstpin = 4
yItemInc = [14, 23, 32, 41, 50]
offset=6
apin = 17
bpin = 27
cpin = 22
total = 0
aflag = False
bflag = False
cflag = False

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False) 
GPIO.setup(rstpin, GPIO.OUT)
GPIO.output(rstpin, 1)

pi = pigpio.pi() 
pi.set_pull_up_down(apin, pigpio.PUD_UP)
pi.set_pull_up_down(bpin, pigpio.PUD_UP)
pi.set_pull_up_down(cpin, pigpio.PUD_UP)


serial = i2c(port=1, address=0x3D)
device = ssd1306(serial, rotate=0, reset=rstpin)

padding = 2
shape_width = 20
top = padding
bottom = device.height - padding - 1
comlookup = ["ttyUSB0", "ttyACM0", "ttyUSB1", "ttyACM1", "ttyUSB2", "ttyACM2", "ttyUSB3", "ttyACM3", "ttyUSB4", "ttyACM4",]
COMPORT = "ttyUSB0"
MAINMENU = 1
RESETTAR = 2
LOCALDIR = 3
TARGETDIR = 4
LOADMENU = 5

flist = []
print("uPython Little Loader running. v0.2")

def cba(gpio, level, tick):
   global aflag
   aflag = 1
   #print(gpio, level, tick, aflag)

def cbb(gpio, level, tick):
   global bflag
   bflag = 1
   #print(gpio, level, tick, bflag)

def cbc(gpio, level, tick):
   global cflag
   cflag = 1
   #print(gpio, level, tick, bflag)


def flushport(port):
    os.system('stty -F /dev/' + port + ' -hupcl')  # do this the hard way vs changing mfpshell
    #print('stty -F /dev/' + port + ' -hupcl')    

def filelist():
        global flist
        with open("out.txt", "r") as file:
            flist = file.readlines()
        # Remove \n characters from each line
        flist = [line.strip() for line in flist]
        for line in range(0,4) :
            flist.pop(0)  # these messages are not necessary for the file list
        flist.pop(-1)     # cr at the end of the listing, remove it
        file.close()      # be nice!

def mpf_reset(port):
    os.system('mpfshell -n -c ' + '"open ' + port + '; --reset ' + '" > reset.txt')
    #os.system('mpfshell -n -c ' + '"open ' + port + '; --reset ' + '" ')

def mpf_ls(port):
    # mpfshell target ls command ===============================================================
    os.system('mpfshell -n -c ' + '"open ' + port + '; ls ' + '" > out.txt')
    filelist()
    # print("Programs on target: ")
    # print(flist)
    flushport(port)

def mpf_lls(port):
    # mpfshell local lls command ==============================================================
    os.system('mpfshell -n -c ' + '"open ' + port + '; lls ' + '" > out.txt')
    filelist()
    # print("Programs on tool: ")
    # print(flist) 
    flushport(port)

def mpf_rm(port, fname):
    # mpfshell rm command ====================================================================
    # file will come from selecting one of the targets programs
    ### TODO will need ok, cancel

    os.system('mpfshell -n -c ' + '"open ' + port + '; rm ' + fname + '" > rmout.txt')
    print("Programs ", fname, " deleted from target ")
    flushport(port)


def mpf_put(port, fname):
    # mpfshell put command ====================================================================
    ### TODO file check
    # mpfshell ls
    # see if fname file is in resulting list
    #   if so issue warning and get user response, to copy over target?
    os.system('mpfshell -n -c ' + '"open ' + port + '; put ' + fname + '" > putout.txt')    
    print("Programs ", fname, " copied to target ")
    flushport(port)

def disp_ls(dev, xpos, ypos, stext):
    
    with canvas(dev) as draw:
       draw.rectangle(dev.bounding_box, outline="white")
       draw.text((6, 20), "Files = ", fill="white") 
       draw.text((xpos, ypos), stext, fill="grey") 
       dev.show()
    sleep(.1)


cb1 = pi.callback(apin, pigpio.RISING_EDGE, cba)
cb2 = pi.callback(bpin, pigpio.RISING_EDGE, cbb)
cb3 = pi.callback(cpin, pigpio.RISING_EDGE, cbc)

# main()    
#==================================================================
# Splash Screen
with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white")
    draw.text((10,  4), "uPython ", fill="white")  
    draw.text((10, 20), "Little Loader ", fill="white")  
    draw.text((10, 40), "s.case   2/19/25", fill="white")  
    draw.text((10, 50), "ver 0.1   " + COMPORT, fill="white")  
    device.show()
sleep(5)

menuid = 1
while True :
#==================================================================
# Main Menu 
  if menuid == MAINMENU :
    while cflag == False:

        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white")
            draw.text((10,  4), "1. Main Menu: ", fill="white")  
            draw.text((90,  4), "# " + str(menuid), fill="white")  
            draw.text((10, 20), "2. Reset Target", fill="white")  
            draw.text((10, 30), "3. Local Files", fill="white")   ## TODO change to use multiple files per screen (page)
            draw.text((10, 40), "4. Target Files", fill="white")  ## TODO change to use multiple files per screen (page)
            draw.text((10, 50), "5. Load Target", fill="white")  
            device.show()
        #sleep(8)
        p = 0

        if (aflag == True):
            menuid += 1
            if menuid > LOADMENU :
                menuid = MAINMENU
            aflag = False    
            
        if (bflag == True):
            menuid -= 1
            if menuid < MAINMENU :
                menuid = LOADMENU
            bflag = False    

    cflag = False

# execute menu selection

  #--------------------------------------------------------------
  elif menuid == RESETTAR :   # reset target

    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="white")
        draw.text((10, 20), "Resetting Target ", fill="white")  
        device.show()
        flushport(COMPORT)
        mpf_reset(COMPORT)
    sleep(4)
    menuid = MAINMENU

  #--------------------------------------------------------------
  elif menuid == LOCALDIR :  # list files on loader

    with canvas(device) as draw: 
        draw.rectangle(device.bounding_box, outline="white")
        draw.text((6, 1), "Local list", fill="white")    
        device.show()
    sleep(.1)

    mpf_lls(COMPORT)
    fp = 0
    while cflag == False:

        disp_ls(device, 10, 30, flist[fp] ) 
        device.show()
        
        if aflag == True:
            fp += 1
            if fp>len(flist)-1 :
                fp = 0
            aflag = False    
        if bflag == True:
            fp -= 1
            if fp>0 :
                fp = 0
            bflag = False

    
    
    menuid = MAINMENU

  #--------------------------------------------------------------
  elif menuid == TARGETDIR :  # list target files
    
    while cflag == False:
    
      with canvas(device) as draw: 
        draw.rectangle(device.bounding_box, outline="white")
        draw.text((10, 1), "Target Programs: ", fill="white")    
        device.show()     
        sleep(.1)

      mpf_ls(COMPORT)
      fp = 0
      while cflag == False:

        disp_ls(device, 10, 30, flist[fp] ) 
        device.show()
        
        if aflag == True:
            fp += 1
            if fp>len(flist)-1 :
                fp = 0
            aflag = False    
        if bflag == True:
            fp -= 1
            if fp>0 :
                fp = 0
            bflag = False

    menuid = MAINMENU

  #------------------------------------------------------------------ 
  elif menuid == LOADMENU :  # copy a program to target
    with canvas(device) as draw: 
        draw.rectangle(device.bounding_box, outline="white")
        draw.text((6, 1), "Local list", fill="white")    
        device.show()
    sleep(.1)

    mpf_lls(COMPORT)
    fp = 0
    while cflag == False:

        disp_ls(device, 10, 30, flist[fp] ) 
        device.show()
        
        if aflag == True:
            fp += 1
            if fp>len(flist)-1 :
                fp = 0
            aflag = False    
        if bflag == True:
            fp -= 1
            if fp>0 :
                fp = 0
            bflag = False

    selection = flist[fp]
    cflag = False

    with canvas(device) as draw: 
        draw.rectangle(device.bounding_box, outline="white")
        draw.text((10, 20), "Program = ", fill="white")
        draw.text((10, 40), selection, fill="white")
        device.show()
    sleep(.1)
    qry = "No, Cancel"

    while cflag == False:
        
        with canvas(device) as draw: 
            draw.rectangle(device.bounding_box, outline="white")
            draw.text((10, 1), "Load   ?", fill="white")
            draw.text((10, 10), selection, fill="white")
            draw.text((10, 40), qry, fill="white")
            
            if (aflag == True) or (bflag == True):
                if qry == "No, Cancel" :
                    qry = "Yes"
                else:
                    qry = "No, Cancel"   
                aflag = False    
                bflag = False

            device.show()
            sleep(.1)

    if qry == "Yes" :
        with canvas(device) as draw: 
            draw.rectangle(device.bounding_box, outline="white")
            draw.text((10, 20), "Loading = ", fill="white")
            draw.text((10, 40), flist[fp], fill="white")
            device.show()

        menuid = MAINMENU
        mpf_put(COMPORT, selection)
        sleep(3)

    else :
        with canvas(device) as draw: 
            draw.rectangle(device.bounding_box, outline="white")
            draw.text((10, 20), "Load Aborted", fill="white")
            device.show()
        
        sleep(2)
        cflag = False
        menuid = MAINMENU






