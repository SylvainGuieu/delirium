#from __future__ import absolute_import
from . import (io, parameters, delirium, computing, wobblefit, dl, log, rail, carriage, sensors, supports)
from matplotlib.pylab  import plt
import numpy as np
reload(log)
reload(io)

reload(computing)
reload(wobblefit)
reload(delirium)
reload(sensors)
reload(carriage)
reload(supports)
reload(rail)

reload(dl)

from . import plots
reload(plots)


dldir = io.DeliriumDirectory("ftp://utcomm:Bnice2me@odyssey3.pl.eso.org/DELIRIUM")
mdir = io.MonitorDirectory("ftp://vlti:boulder56@vlti.pl.eso.org//diska/web/vlti/monitoring/")
#hdir = mdir.hdir
#wdir = mdir.wdir

files = dldir.deliriumfiles("2016-03-23")

hystdata = mdir.hdir.hysteresisfile(4).read_data()
hd = []
hd2 = []
dts = ['2016-01-27', '2016-02-03', '2016-02-10', '2016-02-17',
       '2016-03-02', '2016-03-09', '2016-03-16', '2016-03-23',
       '2016-03-30', '2016-04-06']
for d in dts:
    fdirect = dldir.deliriumfiles(d)
    freverse = dldir.deliriumfiles(d, "reverse")

    ist = dl.DelayLineHysteresis(fdirect[4][0],freverse[4][0])

    
    history = hystdata[ hystdata['date']==d ] 
    #if len(history):        
    hd.append( history['hysteresis'].mean()-(ist.psi_diff_m / 5e-6 ))
    hd2.append( history['hysteresis'].mean() / (ist.psi_diff_m / 5e-6) )
#fdirect = dldir.deliriumfiles("20160323")
#freverse = dldir.deliriumfiles("20160323", "reverse")

#fdirect = dldir.deliriumfiles("20160323")
#freverse = dldir.deliriumfiles("20160323", "reverse")



#dl1 = dl.DelayLineState(deliriumfile=files[1][0])
#dl6 = dl.DelayLineState(deliriumfile=files[6][0])

#ist.plot.histeresis("theta", figure=1, fclear=True)
#ist.plot.histeresis("psi"  , figure=2, fclear=True)

#files = o.getfiles("20160313", ftp=True, ftype="direct")
#files = o.getfiles("20160310", ftp=False, ftype="direct")
#files2 = o.getfiles("20160311", ftp=True, ftype="direct")
#dl3 = dl.DelayLine(deliriumfile=files[3][0])
#dl1_1 = dl.DelayLineState(deliriumfile=files[1][0])
#dl1_2 = dl.DelayLineState(deliriumfile=files2[1][0])

#dl1 = dl.DelayLine(1, [dl1_1,dl1_2])


# dl1 = dl.DelayLineState(deliriumfile=files[1][0])
# dl2 = dl.DelayLineState(deliriumfile=files[2][0])
# dl3 = dl.DelayLineState(deliriumfile=files[3][0])
# dl4 = dl.DelayLineState(deliriumfile=files[4][0])
# dl5 = dl.DelayLineState(deliriumfile=files[5][0])
# dl6 = dl.DelayLineState(deliriumfile=files[6][0])


# dl1.rail.supports.log_corrections()
# dl2.rail.supports.log_corrections()
# dl3.rail.supports.log_corrections()
# dl4.rail.supports.log_corrections()
# dl5.rail.supports.log_corrections()
# dl6.rail.supports.log_corrections()

# dls = [dl1, dl2, dl3, dl4, dl5, dl6]
#opl = dl.get_opl()


#for dl in dls:
#   dl.sensors.plot.roll_correction("yctr", figure="dl%d roll yctr"%dl.num, fclear=True)
#   dl.sensors.plot.roll_correction("zctr", figure="dl%d roll zctr"%dl.num, fclear=True)

# f = plt.figure(0)

# a = f.add_subplot(211)
# a.clear()
# a.axhline(0.0, color="k")
# a.bar(dl.rail.supports.get("supports"), dl.rail.supports.get("V", removeLowOrder=False), color="blue")
# a.set(ylabel="Vertical corrections")
# a.axhline( 0.007, color="r")
# a.axhline(-0.007, color="r")

# a = f.add_subplot(212)
# a.clear()
# a.axhline(0.0, color="k")
# a.bar(dl.rail.supports.get("supports"), dl.rail.supports.get("H", removeLowOrder=False), color="blue")
# a.set(ylabel="Horizontal corrections")
# a.axhline( 0.007, color="r")
# a.axhline(-0.007, color="r")

# f.show()
# f.canvas.draw()



# f = plt.figure(1)

# a = f.add_subplot(211)
# a.clear()
# a.axhline(0.0, color="k")
# a.plot(dl.rail.get("x"), dl.rail.get("z", removeLowOrder=False), color="blue")
# a.set(ylabel="z")

# a = f.add_subplot(212)
# a.clear()
# a.axhline(0.0, color="k")
# a.plot(dl.rail.get("x"), dl.rail.get("y", removeLowOrder=False), color="blue")
# a.set(ylabel="y")

# f.show()
# f.canvas.draw()







# f = plt.figure(2)
# a = f.add_subplot(211)
# a.clear()
# a.axhline(0.0, color="k")
# a.plot(opl, dl.carriage.get("vertical", removeLowOrder=False), color="blue")
# a.set(ylabel="vertical")

# a = f.add_subplot(212)
# a.clear()
# a.axhline(0.0, color="k")
# a.plot(opl, dl.carriage.get("horizontal", removeLowOrder=False), color="blue")
# a.set(ylabel="horizontal")

# f.show()
# f.canvas.draw()






# f = plt.figure(3)
# a = f.add_subplot(211)
# a.clear()
# a.axhline(0.0, color="k")
# a.plot(opl, dl.carriage.sensors.get("zctr", removeLowOrder=True), color="blue")
# a.plot(opl, dl.carriage.sensors.get("zend", removeLowOrder=True), color="green")
# a.set(ylabel="fog z")


# a = f.add_subplot(212)
# a.clear()
# a.axhline(0.0, color="k")
# a.plot(opl, dl.carriage.sensors.get("yctr", removeLowOrder=True), color="blue")
# a.plot(opl, dl.carriage.sensors.get("yend", removeLowOrder=True), color="green")
# a.set(ylabel="fog y")

# f.show()
# f.canvas.draw()

# f = plt.figure(4)
# a = f.add_subplot(311)
# a.clear()
# a.plot(opl, dl.carriage.sensors.get("incl", removeLowOrder=False), color="blue")
# a.set(ylabel="incl")

# a = f.add_subplot(312)
# a.clear()
# a.plot(opl, dl.carriage.get("theta", removeLowOrder=False), color="blue")
# a.set(ylabel="theta")

# a = f.add_subplot(313)
# a.clear()
# a.plot(opl, dl.carriage.get("psi", removeLowOrder=False), color="blue")

# a.set(ylabel="psi")
# f.show()
# f.canvas.draw()



#files = o.getfiles("20160313", ftp=True, ftype="direct")
#dl1_2 =dl.DelayLine(deliriumfile=files[1][0])
#dl1_2.rail.supports.log_corrections()

# f = plt.figure(1)
# a = f.add_subplot(111)
# a.clear()
# a.plot(d.get("opl"), 
#      d.get("yctr", raw=True), color="blue", label="raw")

# a.plot(d.get("opl"), 
#      d.get("yctr"), color="red", label="corrected")

# a.set_xlabel("opl")
# a.set_ylabel("Y ctr")
# a.legend()
# f.show()
# f.canvas.draw()



# f = plt.figure(2)
# f.clear()
# a = f.add_subplot(211)
# a2 = f.add_subplot(212)

# key = "horizontal"
# key = "vertical"
# d.params.get("vertical").period = 1.5

# wopl = d.get_opl(wrap=d.params.get(key).period)
# opl = d.get_opl()

# a.plot(wopl, d.get(key, removeLowOrder=True), "b+")
# d.get_wobble_fit(key).plot(np.linspace(0,2*np.pi, 50), axis=a)

# a2.plot(opl, d.get(key, removeLowOrder=True), "b-")
# a2.plot(opl, d.get(key, removeLowOrder=True, filterWobble=True), "r-")

# f.show()
# f.canvas.draw()

#from astropy.io import fits
#f = plt.figure(3)
#f.clear()
#a = f.add_subplot(111)
#
#hdus = fits.open("/Users/sylvain/Dropbox/python/delirium/data/ControlMatrix.fits")
#CM_V, CM_H, sup, opl = (hdus[k].data for k in ["CM_V","CM_H","support","opl"])
#i = 30
#
#for i in [0,20,40,60]:
#   a.plot(opl, CM_V[i,:])
#   a.axvline( d.dl.support2opl(sup[i]), color="red" ) 
#f.show()
#f.canvas.draw()


