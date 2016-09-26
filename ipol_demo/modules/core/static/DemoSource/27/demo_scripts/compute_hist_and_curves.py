#! /usr/bin/python

import os, sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)

from image import image
import PIL.Image


#-------------------------------------------------------------------------------
def drawtransformImages(imname0, imname1, channel, scale, fname=None):
    """
    Compute transform that converts values of image 0 to values of image 1, for the specified channel
    Images must be of the same size
    """
            
    #load images
    im0 = PIL.Image.open(imname0)
    im1 = PIL.Image.open(imname1)

    #check image size
    if im0.size != im1.size:
        raise ValueError("Images must be of the same size")
    
    # check image mode
    if im0.mode not in ("L", "RGB"):
        raise ValueError("Unsuported image mode for histogram equalization")
    if im1.mode not in ("L", "RGB"):
        raise ValueError("Unsuported image mode for histogram equalization")

    #load image values
    rgb2I = (0.333333, 0.333333, 0.333333, 0,
              0, 0, 0, 0,
              0, 0, 0, 0 )
    rgb2r = (1, 0, 0, 0,
              0, 0, 0, 0,
              0, 0, 0, 0 )
    rgb2g = (0, 1, 0, 0,
              0, 0, 0, 0,
              0, 0, 0, 0 )
    rgb2b = (0, 0, 1, 0,
              0, 0, 0, 0,
              0, 0, 0, 0 )

    if im0.mode == "RGB":
        if channel == "I":
            # compute gray level image: I = (R + G + B) / 3
            im0L = im0.convert("L", rgb2I)
        elif channel == "R":
            im0L = im0.convert("L", rgb2r)
        elif channel == "G":
            im0L = im0.convert("L", rgb2g)
        else:
            im0L = im0.convert("L", rgb2b)
        h0 = im0L.histogram()
    else: 
        #im0.mode == "L":
        h0 = im0.histogram()

    if im1.mode == "RGB":
        if channel == "I":
            # compute gray level image: I = (R + G + B) / 3
            im1L = im1.convert("L", rgb2I)
        elif channel == "R":
            im1L = im1.convert("L", rgb2r)
        elif channel == "G":
            im1L = im1.convert("L", rgb2g)
        else:
            im1L = im1.convert("L", rgb2b)
        h1 = im1L.histogram()
    else:
        #im1.mode == "L":
        h1 = im1.histogram()

    #compute correspondences between image values 
    T = [i for i in range(256)]
    hacum0 = [0 for i in range(256)]
    hacum1 = [0 for i in range(256)]
    hacum0[0] = h0[0]
    hacum1[0] = h1[0]
    for i in range(1, 256):
        hacum0[i] = h0[i]+hacum0[i-1]
        hacum1[i] = h1[i]+hacum1[i-1]

    jprev = 0
    for i in range(0, 256):
        href = hacum0[i]
        j = jprev
        #while (j < 256) and (hacum1[j] <= href):
        while (j < 256) and (hacum1[j] < href):
            j += 1
        #if j > 0:
            #j-=1
        T[i] = j
        jprev = j

    #draw correspondences
    size = (256/scale, 256/scale)
    imout = PIL.Image.new('RGB', size, (255, 255, 255))
    draw = PIL.ImageDraw.Draw(imout)

    x1 = 0
    y1 = 0
    for k in range(256):
        if (h0[k] != 0):
            x2 = k
            y2 = T[k]
            draw.line([(x1/scale, 255/scale-y1/scale), 
                        (x2/scale, 255/scale-y2/scale)], fill=(0, 255, 0))
            x1 = x2
            y1 = y2
    draw.line([(x1/scale, 255/scale-y1/scale), (255/scale, 0)], 
              fill=(0, 255, 0))

    #draw reference (red line)
    draw.line([(0, 255/scale), (255/scale, 0)], fill=(255, 0, 0))

    if fname != None:
        #draw stored transformation
        data = open(fname)
        lines = [line.strip() for line in data]
        N = int(lines[0])
    
        offset = {"I":0, "R":N+3, "G":2*(N+3), "B":3*(N+3)}
    
        for k in range (1+offset[channel], N+2+offset[channel]):
            line = lines[k].split()
            x1 = int(float(line[0]))/scale
            y1 = 255/scale-int(float(line[2]))/scale
            #if y1 < 0:
                #y1 = 0
            x2 = int(float(line[1]))/scale
            y2 = 255/scale-int(float(line[3]))/scale
            #if y2 < 0:
                #y2 = 0
            draw.ellipse((x1-3, y1-3, x1+3, y1+3), fill=(0, 0, 255))
            draw.ellipse((x2-3, y2-3, x2+3, y2+3), fill=(0, 0, 255))
            draw.line([(x1, y1), (x2, y2)], fill=(0, 0, 255))
            if k == 1+offset[channel]:
                draw.line([(0, 255/scale), (x1, y1)], fill=(0, 0, 255))
            if k == N+1+offset[channel]:
                draw.line([(x2, y2), (255/scale, 0)], fill=(0, 0, 255))
        data.close()

    #return result
    return imout

#-------------------------------------------------------------------------------
def drawtransform(imname0, imname1, fname, scale, hmargin, type):
    if type == 'I':
        imR = drawtransformImages(imname0, imname1, 'R', scale)
        imG = drawtransformImages(imname0, imname1, 'G', scale)
        imB = drawtransformImages(imname0, imname1, 'B', scale)
        imI = drawtransformImages(imname0, imname1, 'I', scale, fname)
    else:
        #type='RGB'
        imR = drawtransformImages(imname0, imname1, 'R', scale, fname)
        imG = drawtransformImages(imname0, imname1, 'G', scale, fname)
        imB = drawtransformImages(imname0, imname1, 'B', scale, fname)
        imI = drawtransformImages(imname0, imname1, 'I', scale)    

    im = PIL.Image.new('RGB', (imR.size[0], 4*imR.size[1]+3*hmargin), (255, 255, 255))
    im.paste(imR, (0, 0, imR.size[0], imR.size[1]))
    im.paste(imG, (0, hmargin+imR.size[1],     imR.size[0], hmargin+2*imR.size[1]))
    im.paste(imB, (0, 2*hmargin+2*imR.size[1], imR.size[0], 2*hmargin+3*imR.size[1]))
    im.paste(imI, (0, 3*hmargin+3*imR.size[1], imR.size[0], 3*hmargin+4*imR.size[1]))

    return im


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    #Compute histograms of images
    # create list of all images to process
    imlist = ['input_0.sel']
    for out in ['1','2']:
      for N in ['N2', 'N3','N4','N5','N10', 'HE']:
        imlist.append('output_{0}_{1}'.format(out,N))
    

    #compute value transforms
    scale = 2
    hmargin = 10

    for imname in imlist:
      im = image(imname+'.png')
      if (imname=='input_0.sel'):
        #compute maximum of histogram values
        maxH = im.max_histogram(option="all")
      #draw all the histograms using the same reference maximum
      im.histogram(option="all", maxRef=maxH)
      im.save(imname+'_hist.png')

    
    imG0 = drawtransform('input_0.sel.png', 'input_0.sel.png', 
                              None, scale, hmargin, 'I')
    imG0.save('identity.png')
    
    for N in ['N2', 'N3','N4','N5','N10']:
      imG = drawtransform('input_0.sel.png', 'output_1_'+N+'.png', 
                          'points'+N+'.txt',  scale, hmargin, 'I')
      imG.save('points'+N+'.png')

      imRGB = drawtransform('input_0.sel.png', 'output_2_'+N+'.png',
                            'points'+N+'.txt', scale, hmargin, 'RGB')
      imRGB.save('points'+N+'RGB.png')

    # no output curve for global equalization
    imG = drawtransform('input_0.sel.png', 'output_1_HE.png', 
                        None,  scale, hmargin, 'I')
    imG.save('pointsHE.png')

    imRGB = drawtransform('input_0.sel.png', 'output_2_HE.png',
                          None, scale, hmargin, 'RGB')
    imRGB.save('pointsHERGB.png')

