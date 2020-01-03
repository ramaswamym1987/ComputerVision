"""

CHASSIS NUMBER IDENTIFICATION

python chassisOCR.py --imgpath D:/OCR/Images_Original/2019-10-23_11-36-39_FullGrey.bmp

"""

try:
    import cv2
    import os
    import sys
    import glob
    import argparse
    import subprocess
    import numpy as np
    import pandas as pd
    from PIL import Image
    import string
    import re
    import shutil
    from PIL import Image
    from PIL import ImageFont
    from PIL import ImageDraw
    import imutils
    from imutils.perspective import four_point_transform
    import regexpattern  
    global regexlist
    regexlist = regexpattern.regexlist
    regexlist =  set (regexpattern.regexlist)    
except Exception as exception:    
    print (type(exception).__name__)
    sys.exit()
    
    
#Arguments parser
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--imgpath", type=str, help="Enter the input image path")
args = vars(ap.parse_args())


#Temp directory automated cleaning
def tempClean():
    try:
        shutil.rmtree(os.path.abspath(os.getcwd()+'/temp/'))
    except Exception:
        pass


#Creating temp directory for image manipulations
def dirCreate():
    try:
        tempClean()
        import random
        random = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
        #random = str(os.path.split(os.path.abspath(img_Path))[1].split('_')[2])
        if (os.path.exists(os.path.abspath(os.getcwd()+'/temp'))):
            os.makedirs(os.path.abspath(os.getcwd()+'/temp/'+random))
            dirPath = (os.path.abspath(os.getcwd()+'/temp/'+random))
            return dirPath
        if not os.path.exists(os.path.abspath(os.getcwd()+'/temp')):
            os.makedirs(os.path.abspath(os.getcwd()+'/temp/'+random))
            dirPath = (os.path.abspath(os.getcwd()+'/temp/'+random))
            return dirPath
    except Exception:
        pass    


#<------------------------------STEP-1------------------------------>
#Convert '.tiff' image to 300 dpi, auto gamma, auto level, auto normalize

def BMP2_TIFF_ENHAN(img_Path,outPath = dirCreate()):
    try:
        new_imgName = (os.path.split(outPath)[1])+'_1.tif'
        step_1_imgPath = os.path.abspath(os.path.join(outPath,new_imgName))   
        command = "convert -density 300 -units pixelsperinch -auto-gamma -auto-level -normalize "+os.path.abspath(img_Path)+" "+os.path.abspath(step_1_imgPath)
        ps1 = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        ps1.wait()
        ps1.terminate
        ps1.kill
        return step_1_imgPath
    except Exception:
        pass    
    
    
#<------------------------------STEP-2------------------------------>
#Convert Step-1 image to auto sharpen

def autoSharpStep1(step_1_imgPath):
    try:
        step_2_imgPath = os.path.join(os.path.split(step_1_imgPath)[0],os.path.split(step_1_imgPath)[1].split('_')[0]+'_2.tif')           
        command = "convert -sharpen  0x4 "+os.path.abspath(step_1_imgPath)+" "+os.path.abspath(step_2_imgPath)
        ps2 = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        ps2.wait()
        ps2.terminate
        ps2.kill
        return step_2_imgPath
    except Exception:
        pass  


#<------------------------------STEP-3 (A)------------------------------>
#Tesseract 

def chassisno_extract(img_path):
    try:
        command = "tesseract "+os.path.abspath(img_path)+" stdout -l eng --oem 1 --psm 3 quiet"
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)      
        txt = p.communicate()[0].decode('utf-8').replace('\r\n',' ')#.rstrip()       

        for r in regexlist:
            try:
                result = re.search(r, txt)
                if (result.group()) is not None:
                    return (result.group())
                    break
            except Exception:
                continue        
        
        
        (output, err) = p.communicate() 
        p.wait()
        p.terminate
        p.kill
    except Exception:
        pass


#<------------------------------SKEW_CORRECTION------------------------------>
def skew_correction(img_Path,outPath):
    try:
        image = cv2.imread(img_Path)
        image1 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edged = cv2.Canny(image1, 75, 200)       
        #--------------------------------------------------------------------------
        kernel = np.ones((5,5), np.uint8) 
        edged = cv2.dilate(edged, kernel, iterations=1) 
        #--------------------------------------------------------------------------       
        cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:5]
        # loop over the contours
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                screenCnt = approx
                break
        warped = four_point_transform(image, screenCnt.reshape(4, 2))
        new_imgName = (os.path.split(outPath)[1])+'_0.bmp'
        cropped_imgPath = os.path.abspath(os.path.join(outPath,new_imgName))  
        cv2.imwrite(cropped_imgPath,warped)        
        return cropped_imgPath
    except Exception:
        pass 


#<------------------------------CHASSIS_IMAGE_PROCESSING------------------------------>
def chassisImgProcess(outPath,filename):
    img_OriPath = os.path.abspath(filename)    
    img_Path = skew_correction(img_OriPath,outPath)
    step1_imgPath = BMP2_TIFF_ENHAN(img_Path,outPath)# = dirCreate()) 
    step2_imgPath = autoSharpStep1(step1_imgPath)

    try:
        chNo = chassisno_extract(step1_imgPath)
        if chNo is None:
            chNo = chassisno_extract(step2_imgPath)             
            if chNo is None: #----> Certain images are able to extract txt without pre-processing, so used finally
                chNo = chassisno_extract(img_Path)
                if chNo is None:
                    chNo = chassisno_extract(img_OriPath)
    except Exception:
        pass

    if chNo is None:
        return (0)
    else:
        return chNo


#<------------------------------INVERTING IMAGE TO 180 DEGREE------------------------------>
'''
Inverting images to 180 degree if chassisImgProcess is zero or 
                                                       [0-9]{4}            or 
                                                       [0-9]{5}            or 
                                                       [0-9]{2}[0-9A-Z]{2} or
                                                       [0-9]{2}[0-9A-Z]{3} or 
                                                       [0-9]{2}[0-9\w]{2}  or
                                                       [0-9]{2}[0-9\w]{3}  or
'''
def image_deInvert(outPath,img_OriPath):
    try:
        img = cv2.imread(img_OriPath)
        # Rotating to 180 degree and save with the original resolution
        I = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = I.shape
        M = cv2.getRotationMatrix2D((w/2,h/2),180,1)
        dst = cv2.warpAffine(img,M,(w,h))
        invertImg_filename = os.path.split(outPath)[1]+'INVERT'+os.path.splitext(os.path.split(img_OriPath)[1])[1]
        invertImg_filePath = os.path.join(outPath,invertImg_filename)
        cv2.imwrite(invertImg_filePath, dst)
        return (invertImg_filePath)
    except Exception:
        pass


#Chassis extraction function
def main(imPath):
    try:
        img_OriPath = os.path.abspath(imPath)
        outPath = dirCreate()  
        #----------------------------------------------------------------------------
        chNo = chassisImgProcess(outPath,filename = img_OriPath)
        if chNo==0  or re.search('[0-9]{4}',chNo[0:4]) or re.search('[0-9]{5}',chNo[0:5]) or re.search('[0-9]{2}[0-9A-Z]{2}',chNo[0:4]) or re.search('[0-9]{2}[0-9A-Z]{3}',chNo[0:5]) or re.search('[0-9]{2}[0-9\w]{2}',chNo[0:4]) or re.search('[0-9]{2}[0-9\w]{3}',chNo[0:5]):
            img_OriPath_New = image_deInvert(outPath,img_OriPath)
            chNo = chassisImgProcess(outPath,filename = img_OriPath_New)
            if chNo == 0:
                chNo = None
        #----------------------------------------------------------------------------
        #Post processing
        if chNo is not None:
            if 'O' in chNo :
                chNo = chNo.replace('O', '0')    
            if 'I' in chNo :
                chNo = chNo.replace('I', '1')              
            if '.' in chNo:# and len(chass_no)==18:
                tmptxt = chNo.split('.')
                chNo = tmptxt[0]+tmptxt[1]
            if ' ' in chNo :
                chNo = chNo.replace(' ', '')   
            if '|' in chNo :
                chNo = chNo.replace('|', '1')
            if ']' in chNo :
                chNo = chNo.replace(']', '1')      
        if chNo is None:
            chNo = ('Cant find Chassis Number')
        print (chNo)
    except Exception:
        pass


#Calling the main chassis extraction function
if __name__ == "__main__":
    main(args["imgpath"])    
    
    
    
    
    
    
    
    
    
    
    
    
    
