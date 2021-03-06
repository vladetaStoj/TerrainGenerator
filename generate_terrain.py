#Basic terrain generator 
#Vladeta Stojanovic (vladeta_stojanovic@yahoo.co.uk)

#TODO:
# Adjust contrast of emboss shadow map
# Add gray color ares to color map
# Add mirroring of edges along all heightmap, so the terrain can be tiled infintately without any seams

import numpy as np
import matplotlib.pyplot as plt
import math
from mpl_toolkits.mplot3d import Axes3D
from random import seed
from random import randint
import scipy.ndimage as ndimage
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from datetime import datetime
from blend_modes import multiply

class Terrain:
  def __init__(self, size):
    self.size = size
    self.terrainData = np.zeros(self.size * self.size) #this is what we plot as the y value on the zyx 3D plot to generate the terrain
    self.heightMap = 0
    self.colorMap = np.zeros(self.size * self.size)
    seed(datetime.now())

  #Debug function
  def FillRandomValues(self):
    self.terrainData = np.random.randint(0, 255, (self.size, self.size))
    self.NormalizeTerrain()
    print(self.terrainData.shape)

  def Debug3DPlot(self):
    ny, nx = self.terrainData.shape
    x = np.linspace(0, 1, nx)
    y = np.linspace(0, 1, ny)
    xv, yv = np.meshgrid(x, y)

    #Plot 3D image
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    dem3d = ax.plot_surface(xv,yv, self.terrainData)
    plt.show()

  #Todo: Add Debug2D plot using contourF function

  #Todo: Add image saving function

class SimplexNoiseTerrain(Terrain):
  def __init__(self, size):
    Terrain.__init__(self, size)

  def Fract(self, x):
    return x - math.floor(x)

  def LinearInterpolate(self, p1, p2, x):
    return p1 * (1.0 - x) + p2 * x
    
  def RandNoise(self, x, y):
    dotProduct = 12.9898 * x +  78.233 * y
    return self.Fract(math.sin(dotProduct) * (4375.5453123 * randint(-10, 10)))

  def Random2DNoise(self, x, y):
    ix = math.floor(x)
    iy = math.floor(y)
    fx = self.Fract(x)
    fy = self.Fract(y)

    a = self.RandNoise(ix, iy)
    b = self.RandNoise(ix + 1.0, iy)
    c = self.RandNoise(ix, iy + 1.0)
    d = self.RandNoise(ix + 1.0, iy + 1.0)

    ux = fx * fx * (3.0 - 2.0 * fx)
    uy = fy * fy * (3.0 - 2.0 * fy)
    
    mix = self.LinearInterpolate(a, b, ux) + (c - a) * uy * (1.0 - ux) + (d - b) * ux * uy

    return mix

  def GenerateTerrain(self, frequency):

    for i in range(self.size):
      for j in range(self.size):
          self.terrainData[i + self.size * j] = terrainTest.Random2DNoise(i, j)
        
    print(self.terrainData)

    x = np.arange(0, self.size, frequency) 
    y = np.arange(0, self.size, frequency)

    xx, yy = np.meshgrid(x, y, sparse=False)

    self.terrainData =  self.terrainData[xx + self.size * yy]

    self.terrainData = ndimage.gaussian_filter(self.terrainData, sigma= 1.0, order=0) #smooth interpolation of contour plot, sigma is the smoothness factor, order is the derivate of current convolution 
    
    #debug 2D plot
    plt.axis('equal')
    plt.gray()
    contourfig = plt.contourf(x,y,self.terrainData)

    self.SaveHeightmap(plt.figure, "terrain_height.png")
    self.MakeColormap("terrain_height.png", "terrain_color.png")

  def SaveHeightmap(self, fig, filename):   
    fig = plt.figure()
    DPI = fig.get_dpi()
    fig.set_size_inches(self.size/float(DPI),self.size/float(DPI))
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    plt.gray()
    plt.imshow(self.terrainData, interpolation='bicubic')
    plt.savefig(filename) 
    plt.close()

  def MakeColormap(self, in_heightmap, out_colormap):

    blue = [65,105,225]
    green = [34,139,34]
    beach = [238, 214, 175]
    white = [250, 250, 250]
    #TODO: Add gray stone color  between green and white color 

    img = Image.open(in_heightmap).convert('L')
    height_map = np.array(img.getdata())

    w, h = self.size, self.size
    color_map = np.zeros((h, w, 3), dtype=np.uint8)

    for i in range(self.size):
      for j in range(self.size):
        if (height_map[i + self.size * j] <= 80):
          color_map[i, j] = blue
        elif (height_map[i + self.size * j] >= 80 and height_map[i + self.size * j] <= 100):
          color_map[i, j] = beach
        elif (height_map[i + self.size * j] >= 100 and height_map[i + self.size * j] <= 200):
          color_map[i, j] = green
        elif (height_map[i + self.size * j] >= 200):
          color_map[i, j] = white
    
    #Rotate and vertically flip the color image
    img = Image.fromarray(color_map, 'RGB')
    transposed  = img.transpose(Image.ROTATE_90)
    transposed  = ImageOps.flip(transposed)

    transposed.save('color_map.png')
    transposed.show() 

  #Add shadow generation using embossing of heightmap and blending with colormap - this should be optional
  def EmbossColor(self, image, outimage):

    elevation = np.pi / 2.2
    azimuth = np.pi / 4.0
    depth = 30.0
    blur_amount = 10

    img = Image.open(image).convert('L')
    a = np.asarray(img).astype('float')
    grad = np.gradient(a)
    grad_x, grad_y = grad

    gd = np.cos(elevation)
    dx = gd*np.cos(azimuth)
    dy = gd*np.sin(azimuth)
    dz = np.sin(elevation)

    grad_x = grad_x*depth / 100.0
    grad_y = grad_y*depth / 100.0
    
    leng = np.sqrt(grad_x**2 + grad_y**2 + 1.0)
    uni_x = grad_x / leng
    uni_y = grad_y / leng
    uni_z = 1.0 / leng

    a2 = 255*(dx*uni_x + dy*uni_y + dz*uni_z)
    a2 = a2.clip(0,255)

    img2 = Image.fromarray(a2.astype('uint8'))

    for i in range(blur_amount): #this tries to mediate the banding artefact 
      img2 = img2.filter(ImageFilter.BLUR)

    #Increase contrast of blurred image
    enhancer = ImageEnhance.Contrast(img2)
    contrast = 3.0 #increase contrast
    img2 = enhancer.enhance(contrast)

    img2.save(outimage)
    img2.show()
      
  #This function blends the color and emboss image results togather 
  def MergeEmbossColor(slef, color_image, emboss_image, out_image):

    #background image
    background_img_raw = Image.open(color_image) 
    background_img_raw_rgba = background_img_raw.convert("RGBA")
    background_img = np.array(background_img_raw_rgba) 
    background_img_float = background_img.astype(float)  

    #foreground image
    foreground_img_raw = Image.open(emboss_image) 
    foreground_img_raw_rgba = foreground_img_raw.convert("RGBA")
    foreground_img = np.array(foreground_img_raw_rgba) 
    foreground_img_float = foreground_img.astype(float)  

    opacity = 1.0  
    blended_img_float = multiply(background_img_float, foreground_img_float, opacity)
    blended_img = np.uint8(blended_img_float)  
    blended_img_raw = Image.fromarray(blended_img)  

    blended_img_raw.save(out_image)
    blended_img_raw.show()

terrainTest = SimplexNoiseTerrain(512)
terrainTest.GenerateTerrain(32)
terrainTest.EmbossColor('terrain_height.png', 'terrain_shadow.png')
terrainTest.MergeEmbossColor('color_map.png', 'terrain_shadow.png', 'terrain_color.png')
#terrainTest.Debug3DPlot() #Change this function call to OpenGL based terrain viewer

#Todo: Write main init method with command line argument passing capability, let user also decide if they want to see all the debug features

