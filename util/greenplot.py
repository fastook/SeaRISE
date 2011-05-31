#!/usr/bin/env python

# Copyright (C) 2009-2011 Andy Aschwanden and Ed Bueler

# script to generate figures: results from Greenland runs
# usage:  if foo.nc is NetCDF file then do
#   $ ./greenplot.py foo1 foo2 ...
# produces figures foo1_X.pdf where X is from a list of variables
# given at command line.


try:
    from netCDF3 import Dataset as NC
except:
    from netCDF4 import Dataset as NC

from mpl_toolkits.basemap import Basemap, cm
import numpy as np
import pylab as plt
from matplotlib import colors
from optparse import OptionParser

# Set up the option parser
parser = OptionParser()
parser.usage = "%prog [options] PISMFILE1 PISMFILE2 ..."
parser.description = "A script to plot PISM Greenland results."
parser.add_option("-b", "--bluemarble",dest="bluemarble",action="store_true",
                  help="draw bluemarble background, requires the Python Imaging Library",default=False)
parser.add_option("--eps",dest="do_eps",action="store_true",
                  help="save additionally as EPS file",default=False)
parser.add_option("-l", "--borehole_locations",dest="boreholes",action="store_true",
                  help="add locations of boreholes (GRIP, NGRIP, CC, Dye3).",default=False)
parser.add_option("-m", "--mask_file",dest="mask_file",
                  help="a file containing a variable 'mask'. Plots will be masked out where entries are set to True.",default=None)
parser.add_option("-p", "--print_size",dest="print_mode",
              help="sets figure size and font size, available options are: \
              'onecol','medium','twocol','presentation'",default="twocol")
parser.add_option("-t", "--thk_min",dest="thk_min",
                  help="minimum ice thickness in meters, this affects ice area extend, and can be used, e.g., \
                  to exclude seasonal snow cover. Default is 10m",default=10)
parser.add_option("-v", "--variable",dest="variables",
                  help="Comma-separated list with variables, default = 'usurf'. Currently supported variables are: bmelt, csurf, liqfrac (at the base), temp_pa (at the base), usurf",default='usuf')

(options, args) = parser.parse_args()

print_mode = options.print_mode
bluemarble = options.bluemarble
do_eps = options.do_eps
boreholes = options.boreholes
varlist = options.variables.split(',')
thk_min = options.thk_min
NCNAMES = args


def bh_lonlat():
    '''
    Return locations of the following four boreholes:
    
    NGRIP: 75.1 N, -42.3 W temperate
    GRIP: 72.58 N, -37.63 W cold
    Dye 3: 65.18 N -43.81 W cold
    CC: 77.18 , -61.13 W cold
    '''
    
    lat = np.array([75.1,72.58,65.18,77.18])
    lon = np.array([-43.2,-37.63,-43.81,-61.13])
    
    return lon,lat

def set_mode(mode):
    '''
    Set the print mode, i.e. document and font size. Options are:
    - onecol: width=85mm, font size=6pt. Default. Appropriate for 1-column figures
    - twocol: width=170mm, font size=8pt. Appropriate for 2-column figures
    - medium: width=85mm, font size=8pt.
    - presentation: width=85mm, font size=9pt. For presentations.
    
    '''

    # Default values
    linestyle = '-'

    def set_onecol():
        '''
        Define parameters for "publish" mode and return value for pad_inches
        '''
        
        fontsize = 6
        lw = 1.5
        markersize = 2
        fig_width = 3.32 # inch
        fig_height = golden_mean*fig_width # inch
        fig_size = [fig_width,fig_height]

        params = {'backend': 'eps',
                  'lines.linewidth': lw,
                  'axes.labelsize': fontsize,
                  'text.fontsize': fontsize,
                  'xtick.labelsize': fontsize,
                  'ytick.labelsize': fontsize,
                  'legend.fontsize': fontsize,
                  'lines.linestyle': linestyle,
                  'lines.markersize': markersize,
                  'font.size': fontsize,
                  'figure.figsize': fig_size}

        plt.rcParams.update(params)

        return 0.35

    
    def set_medium():
        '''
        Define parameters for "medium" mode and return value for pad_inches
        '''
        
        fontsize = 8
        markersize = 3
        lw = 1.5
        fig_width = 3.32 # inch
        fig_height = 0.95*fig_width # inch
        fig_size = [fig_width,fig_height]

        params = {'backend': 'eps',
                  'lines.linewidth': lw,
                  'axes.labelsize': fontsize,
                  'text.fontsize': fontsize,
                  'xtick.labelsize': fontsize,
                  'ytick.labelsize': fontsize,
                  'legend.fontsize': fontsize,
                  'lines.linestyle': linestyle,
                  'lines.markersize': markersize,
                  'font.size': fontsize,
                  'figure.figsize': fig_size}

        plt.rcParams.update(params)

        return 0.35

    def set_presentation():
        '''
        Define parameters for "presentation" mode and return value for pad_inches
        '''
        
        fontsize = 10
        lw = 1.5
        markersize = 3
        fig_width = 6.64 # inch
        fig_height = 0.95*fig_width # inch
        fig_size = [fig_width,fig_height]

        params = {'backend': 'eps',
                  'lines.linewidth': lw,
                  'axes.labelsize': fontsize,
                  'text.fontsize': fontsize,
                  'xtick.labelsize': fontsize,
                  'ytick.labelsize': fontsize,
                  'lines.linestyle': linestyle,
                  'lines.markersize': markersize,
                  'legend.fontsize': fontsize,
                  'font.size': fontsize,
                  'figure.figsize': fig_size}

        plt.rcParams.update(params)

        return 0.35

    def set_twocol():
        '''
        Define parameters for "twocol" mode and return value for pad_inches
        '''
        
        fontsize = 10
        lw = 1.25
        markersize = 3
        fig_width = 6.64 # inch
        fig_height = 0.95*fig_width # inch
        fig_size = [fig_width,fig_height]

        params = {'backend': 'eps',
                  'lines.linewidth': lw,
                  'axes.labelsize': fontsize,
                  'text.fontsize': fontsize,
                  'xtick.labelsize': fontsize,
                  'ytick.labelsize': fontsize,
                  'lines.linestyle': linestyle,
                  'lines.markersize': markersize,
                  'legend.fontsize': fontsize,
                  'font.size': fontsize,
                  'figure.figsize': fig_size}

        plt.rcParams.update(params)

        return 0.35


    if (mode=="onecol"):
        return set_onecol()
    elif (mode=="medium"):
        return set_medium()
    elif (mode=="presentation"):
        return set_presentation()
    elif (mode=="twocol"):
        return set_twocol()
    else:
        print("%s mode not recognized, using onecol instead" % mode)
        return set_onecol()

def permute(variable, output_order = ('t', 'z', 'zb', 'y', 'x')):
    """Permute dimensions of a NetCDF variable to match the output storage order."""
    input_dimensions = variable.dimensions

    # filter out irrelevant dimensions
    dimensions = filter(lambda(x): x in input_dimensions,
                        output_order)

    # create the mapping
    mapping = map(lambda(x): dimensions.index(x),
                  input_dimensions)

    if mapping:
        return np.transpose(variable[:], mapping)
    else:
        return variable[:]              # so that it does not break processing "mapping"


for NCNAME in NCNAMES:
    
    PREFIX,d = NCNAME.split('.')
    print "  opening NetCDF file %s ..." % NCNAME
    try:
        # open netCDF file in 'append' mode
        nc = NC(NCNAME, 'r')
    except:
        print "greenplot.py ERROR:  file '%s' not found or not NetCDF format ... ending ..." % NCNAME
        exit(1)

    # we need to know longitudes and latitudes corresponding to out grid
    lon = np.squeeze(permute(nc.variables['lon']))
    lat = np.squeeze(permute(nc.variables['lat']))
    # need thickness for some masking operations
    thk = np.squeeze(permute(nc.variables['thk']))

    # surface can be drawn as alpha<1 transparent surface for when showing basal fields
    usurf = np.squeeze(permute(nc.variables['usurf']))
    musurf = np.ma.array(usurf, mask = (thk <= thk_min))

    # x and y *from the dataset* are only used to determine the plotting domain
    x = nc.variables['x'][:]
    y = nc.variables['y'][:]
    width = x.max() - x.min()
    height = y.max() - y.min()

    # create basemap: get some params for projection from file and/or command line
    # width: width in projection coordinates, in meters
    # height: height in projection coordinates, in meters
    # resolution: coastline res; 'l'=low, 'h'=high, 'f'=full
    # projection: stereographic projection
    # lat_ts: latitude of true scale
    # lat_0: latitude of the plotting domain center
    # lon_0: longitude of the plotting domain center
    print "  creating Basemap ..."
    m = Basemap(width=1.2*width,
                height=height,
                resolution='l',
                projection='stere',
                lat_ts=nc.variables['mapping'].standard_parallel,
                lat_0=72.0,
                lon_0=-40.0)
    
    # convert longitudes and latitudes to display-able x and y:
    xx,yy = m(lon, lat)

    # set the print mode
    pad_inches = set_mode(print_mode)

    # loop over variables; default behavior is to throw error if variable unknown
    for var in varlist:

        print "  reading variable %s from file ..." % var
        try:
            data = np.squeeze(permute(nc.variables[var]))
        except:
            print "greenplot.py ERROR:  unknown or not-found variable '%s' in file %s ... ending ..." % (var,NCNAME)
            exit(2)

        try:
            inunit = str(nc.variables[var].units)
        except:
            print "greenplot.py ERROR:  unknown or not-found variable '%s' in file %s ... ending ..." % (var,NCNAME)
            exit(2)


        plt.figure()
        # plot csurf using log color scale
        if var == 'csurf' or var == 'magnitude':

            outunit = str("m/yr")

            if not (inunit == outunit):
                try:
                    from udunits import Converter
                    c = Converter(inunit,outunit)
                    data=c(data)
                except:
                    print("  No udunits module found, you're on your own.\n    -> Assuming meters per year.\n    -> Installation of Constantine's awesome python wrapper for udunits is highly recommended.\n  -> Download it from https://code.google.com/p/python-udunits/.")
                    pass
            else:
                pass

            fill  = nc.variables[var]._FillValue
            mdata = np.ma.array(data, mask = ((data == fill) & (thk <= thk_min)))
            m.pcolormesh(xx,yy,mdata,cmap=plt.cm.Accent,
                     norm=colors.LogNorm(vmin=0.5, vmax=5e3)) # use log color scale; omit to use linear color scale
            plt.colorbar(extend='max', drawedges=False,pad=0.1,
                         ticks=[1, 10, 100, 1000, 10000],
                         format="%d")
          #plt.title(r"Modeled ice surface velocity, m/year")
        elif var == 'bmelt':

            outunit = str("m/yr")

            if not (inunit == outunit):
                try:
                    from udunits import Converter
                    c = Converter(inunit,outunit)
                    data=c(data)
                except:
                    print("  No udunits module found, you're on your own.\n    -> Assuming meters per year.\n    -> Installation of Constantine's awesome python wrapper for udunits is highly recommended.\n  -> Download it from https://code.google.com/p/python-udunits/.")
                    pass
            else:
                pass

            mdata = np.ma.array(data, mask = (thk <= thk_min) & (data > 0))
            m.pcolor(xx,yy,mdata,cmap=plt.cm.YlOrRd,
                         norm=colors.LogNorm(vmin=0.009999999, vmax=10))
            plt.colorbar(extend='both', drawedges=False,pad=0.1,
                         ticks=[0, 0.01, 0.1, 1.,10],
                         format="%.3f")
          #plt.title(r"Modeled basal melt rate, m/year")
        elif var == 'liqfrac':
            k = 0
            data = data[k][:][:]
            mdata = np.ma.array(data, mask = (thk <= thk_min))
            z = nc.variables['z'][:]
            print "    [showing liqfrac at level %d, which is %.2f m above bed]" % (k,z[k])
            m.pcolormesh(xx,yy,mdata, vmin=0.0, vmax=0.01)
            plt.colorbar(extend='neither', drawedges=False,pad=0.1,
                       ticks=[0, 0.005, 0.01],mat="%.3f")
        elif var == 'temp_pa':
            k = 0
            data = data[0][:][:]
            mdata = np.ma.array(data, mask = (thk <= thk_min))
            z = nc.variables['z'][:]
            print "    [showing pressure-adjusted temperature at level %d, which is %.2f m above bed]" % (k,z[k])
            m.pcolor(xx,yy,mdata, vmin=-16,vmax=0,
                     cmap=plt.cm.RdYlBu_r)
            plt.colorbar(extend='both', drawedges=False,pad=0.1)
            plt.contour(xx,yy,mdata,[-0.0000001],colors='w')
          #plt.title(r"Modeled liquid water fraction")
        elif var == 'usurf':
            m.fillcontinents(color = 'coral',zorder=0) ## zorder=0 makes overdrawing over map possible
            m.pcolor(xx,yy,musurf,cmap=plt.cm.Blues_r,vmin = 0., vmax = 3000.)
            plt.colorbar(extend='max', drawedges=False,pad=0.1,
                         ticks=[0, 1000, 2000, 3000],
                         format="%d")
            # over-draw contours
            m.contour(xx, yy, musurf, range(500,3500+1,250), 
                      colors="black", linewidths=0.5)
            m.contour(xx, yy, thk, [0,0], 
                      colors="black", linewidths=1,linestyles='dashed')
          #plt.title(r"Modeled surface elevation, m")
        else:
            print "greenplot.py ERROR:  variable '%s', though present in %s," % (var,NCNAME)
            print "                     is not handled by greenplot.py ... printing usage\n."
            parser.print_help()
            exit(3)

        #m.contour(xx, yy, musurf, range(250,3250+1,500), 
        #          colors="black", linestyles='dashed', linewidths=0.2)

        # draw parallels, meridians, coastlines
        # labels argument specifies where to draw ticks: [left, right, top, bottom]
        m.drawparallels(np.arange(55.,90.,5.), labels = [1, 1, 0, 0], linewidth=0.5)
        m.drawmeridians(np.arange(-110.,30.,10.), labels = [0, 0, 0, 1], linewidth=0.5)
        m.drawcoastlines(linewidth=0.5)

        # draw marker at bore hole locations
        if boreholes:
            bh_lon,bh_lat = bh_lonlat()
            x,y = m(bh_lon,bh_lat)
            labels = ['NGRIP','GRIP','Dye3','CC']
            dx = dy = 5e4
            # plot only NGRIP and GRIP
            for k in range(4):
                plt.plot(x[k],y[k],'o',color='w')
                plt.text(x[k]+dx,y[k]+dy,labels[k],bbox=dict(facecolor='w', alpha=0.75))

        # draw the Blue Marble background (requires PIL, the Python Imaging Library)
        if bluemarble:
            m.bluemarble()

        OUTNAME = PREFIX+"_"+var+".pdf"
        print "  writing image %s ..." % OUTNAME
        plt.savefig(OUTNAME,bbox_inches='tight',pad_inches=pad_inches)
        if do_eps:
            OUTNAME = PREFIX+"_"+var+".eps"
            print "  writing image %s ..." % OUTNAME
            plt.savefig(OUTNAME,bbox_inches='tight',pad_inches=pad_inches)

# close file
nc.close()
