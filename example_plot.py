#!/usr/bin/env python
#############################################
# Original Matlab Author: Joseph Schoonover #
# Adaptation to Python:   Adam Kubaryk      #
#############################################

import matplotlib
matplotlib.use('agg') # cannot plt.show() with this, but pyplot fails on the compute nodes without an X Server
import matplotlib.pyplot as plt
from matplotlib import ticker
from mpl_toolkits.basemap import Basemap
import numpy as np
from netCDF4 import Dataset
from os import listdir, path
import re
from multiprocessing import Pool
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

def get_matching_files(directory,r):
	# takes in string: directory and re.compile(search_pattern): r
	return sorted(filter(r.match,listdir(directory)))

def get_timestamp(input_file):
	regex = re.compile(r'\.(.*?)\.nc$')
	return regex.search(input_file).groups()[0]

def fmt(x, pos):
	# used by make_plot in the colorbar section to put scientific notation on labels
	a, b = '{:.2e}'.format(x).split('e')
	b = int(b)
	return r'${} \times 10^{{{}}}$'.format(a, b)

def make_plot(data,title,cbartitle,lon,lat,mymin,mymax,myticks,ncolors,ncontours,mycolormap,timestamp,savename,ufield=None,vfield=None):
	fontfam='serif'
	plt.figure()
	# basemap
	m = Basemap(llcrnrlon=lon[0],llcrnrlat=lat[0],urcrnrlon=lon[-1],urcrnrlat=lat[-1],projection='cyl')
	lon,lat = np.meshgrid(lon,lat)
	x,y = m(lon,lat)
	m.drawcoastlines()
	m.drawstates()
	m.drawcountries()
	# contouring
	cmap = m.contourf(x,y, data, np.linspace(mymin, mymax, ncolors), cmap=mycolormap)
	m.contour(x,y, data, np.linspace(mymin, mymax, ncontours), colors='black', linewidths=1)	
	# colorbar
	cbar = m.colorbar(cmap, ticks=np.linspace(mymin,mymax,myticks))#, format=ticker.FuncFormatter(fmt))
	cbar.ax.yaxis.label.set_font_properties(matplotlib.font_manager.FontProperties(family=fontfam,size=16))
	cbar.ax.set_title(cbartitle,y=1.04)
	# neutral wind vectors if supplied
	if ufield is not None and vfield is not None:
		speed = np.sqrt(ufield*ufield+vfield*vfield)
		m.quiver(x,y,ufield,vfield,speed,latlon=True)
	# standard labeling
	#plt.xlabel('Geographic Longitude ($^o$E)', fontsize=18, fontname=fontfam)
	#plt.ylabel('Geographic Latitude ($^o$N)',  fontsize=18, fontname=fontfam)
        plt.xticks([0, 90, 180, 270, 360],['$0^o E$', '$90^o E$', '$180^o E$', '$270^o E$', '$360^o E$'])
        plt.yticks([-90, -45, 0, 45, 90],['$90^o S$', '$45^o S$', '$0^o$', '$45^o N$', '$90^o N$'])
        plt.grid()
	plt.title(title+timestamp, fontsize=20, fontname=fontfam)
	# output
	plt.savefig(path.join(args.output_directory,savename+'.'+timestamp+'.eps'))
	plt.close()

def make_plots(i):
	input_file = ipeFiles[i]
	print input_file
	## read in netcdf data
	timestamp = get_timestamp(input_file)
	dataset = Dataset(input_file)
	lon = dataset.variables['longitude'][:]
	lat = dataset.variables['latitude'][:]
	## make plots
	for j,type in enumerate(types):
		print type
		if heights[j]:
			data = dataset.variables[type][0,42,:,:]
		else:
			data = dataset.variables[type][0,:,:]
		max = np.abs(data).max() # make sure the colorbar is symmetric about 0
		make_plot(data,type+' difference at ','',lon,lat,-1*max,max,nContours,nColors,nContours,'bwr',timestamp,type)
	
def writetex():
	# file name definitions to search for
	with open(path.join(args.output_directory,'Report.tex'),'w') as f:
		# start
		f.write('\\documentclass[12pt,a4paper]{article}\n')
		f.write('\\usepackage[utf8]{inputenc}\n')
		f.write('\\usepackage{amsmath}\n')
		f.write('\\usepackage{amsfonts}\n')
		f.write('\\usepackage{amssymb}\n')
		f.write('\\usepackage{graphicx}\n')
		f.write('\\usepackage[margin=1in]{geometry}\n')
		f.write('\\begin{document}\n')
		# figures
		figcount=0
		for type in types:
			f.write('\\begin{figure}[!htb]\n') 
			figures = get_matching_files(args.output_directory,re.compile(re.escape(type)+r'.*?'))
			for i,figure in enumerate(figures):
				figcount+=1
				f.write('\\minipage{0.33\\textwidth}\n')
				f.write('\\includegraphics[width=\\linewidth]{'+figure+'}\n')
				f.write('\\endminipage')
				if ( (i+1) % 3 == 0 ):
					f.write('\n')
					f.write('\\end{figure}\n\n')
					if ( figcount % 12 == 0 ):
						f.write('\\clearpage\n\n')
					f.write('\\begin{figure}[!htb]\n')
				else:
					f.write('\\hfill\n')
			if( (len(figures)+1) % 3 != 0 ):
				f.write('\\end{figure}\n')
		# finalize
		f.write('\\end{document}\n')

def main():
	## plotting
	num_i = len(ipeFiles)
	p = Pool(num_i)
	p.map(make_plots,range(num_i))
#	for i in range(len(ipeFiles)):
#		make_plots(i)
	## LaTeXing
	writetex()	

## set some constants
# plotting stuff
nColors = 200
nContours = 7

## parsing options
parser = ArgumentParser(description='Make plots from height-gridded NetCDF IPE output', formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--output_directory', help='directory where plots are stored', type=str, required=True)
args = parser.parse_args()

## get our list of files
ipeFiles = ['IPE_State.201303160103.nc','IPE_State.201303160106.nc','IPE_State.201303160109.nc']
types =   ['H+','He+','N+','N2','N2+','NO+','O','O+','O2','O2+','TEC','e','hmf2','nmf2','tn','vn_meridional','vn_vertical','vn_zonal']
heights = [True,True, True,True,True, True, True,True,True,True,False,True,False,False,True, True,           True,         True]
print heights
## run the program
main()
