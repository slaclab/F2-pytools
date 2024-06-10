import os, sys
from os import path
from sys import exit
import numpy as np
from functools import partial
from epics import caget
import time


from matplotlib.pyplot import show, imshow, scatter
from matplotlib import pyplot as plt
from scipy import ndimage
from skimage.feature import peak_local_max
import skimage as sk
from skimage.measure import regionprops

PV_DTOTR = 'CAMR:LI20:107'
PV_DTOTR_IMG = f'{PV_DTOTR}:Image:ArrayData'
IMG_W = caget(f'{PV_DTOTR}:Image:ArraySize0_RBV')
IMG_H = caget(f'{PV_DTOTR}:Image:ArraySize1_RBV')

MASK = np.ones((IMG_W,IMG_H),dtype=int)

def calc_dtotr_centroid():
    """ get the image centroid from DTOTR2 & determine CUD image ROI """
    image = np.reshape(caget(PV_DTOTR_IMG), (IMG_W,IMG_H), order='F')
    mask = (image > sk.filters.threshold_mean(image)).astype(int)
    cy,cx = regionprops(mask, image)[0].centroid
    return cx,cy


if __name__ == '__main__':

    plt.ion()
    plt.show()
    s = plt.scatter(0,0,color='white')

    while True:
        ts = time.time()
        imshow(np.reshape(caget(PV_DTOTR_IMG), (IMG_W,IMG_H), order='F'))
        cx,cy = calc_dtotr_centroid()
        print(f'x0 = {cx:.1f}, y0 = {cy:.1f} \t dt: {time.time()-ts:.4f}s')
        time.sleep(0.05)
        s.remove()
        s = plt.scatter(cx,cy,color='white',marker='+')
        plt.draw()
        plt.pause(0.01)