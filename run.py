from .dl import DelayLineState, DelayLineHysteresis
from .log import Log, get_buffer, clear_buffer
from . import io
from .delirium import DataError
from . import plots
import time, datetime
import sys
import os
log = Log(context=("DELIRIUM",))
DEBUG = False
#DEBUG = False
### 
## directory where to found the yyyy-mm/delirium_files
dldir = io.DeliriumDirectory("ftp://utcomm:Bnice2me@odyssey3.pl.eso.org/DELIRIUM")
#dldir = io.DeliriumDirectory("/Users/sylvain/Dropbox/python/delirium/data/examples/DELIRIUM/")

##
# some file needs to be copied from the module to the webpage
moduledir, _ = os.path.split(__file__)
localhtmldir = io.dpath(moduledir+"/html")


####
## directory for the wiki monitoring 
# with the structure 
# delirium | 
#          | data 
#                  | daily       -> daily results
#                  | monitoring  -> monitoring files

webroot = io.dpath("ftp://vlti:boulder56@vlti.pl.eso.org//diska/web/vlti/")
#webroot = io.dpath("/Users/sylvain/tmp")

deliriumdir = webroot.dpath("delirium")
datadir = deliriumdir.dpath("data")
dailydir, monitoringdir = datadir.dbreak("daily", "monitoring")

    
indexfile = deliriumdir.fpath("index.html")
indexfile.header = localhtmldir.fpath("index.html").read

#hist_header = "%% Date  TunnelTemp(deg) Hysteresis(arcsec)\n"
#wobble_header = "%% Date  TunnelTemp(deg) WoobleTheta(arcsec) WooblePsi(arcsec)\n"



def list_all_dates():
    fls = dldir.ls("[0-9][0-9][0-9][0-9]-[0-9][0-9]/DL1*.dat")
    dates = [] 
    for fl in fls:
        d, f = os.path.split(fl)
        date = f[11:19]
        date = date[0:4]+"-"+date[4:6]+"-"+date[6:8]
        if not date in dates:
            dates.append(date)
    return dates

def reprocess_all(dates):
    for date in dates:
        run(date, plot=False, wiki=False)
                
def prepare_web_structure():
    global webroot, mdir, ddir

    ## make the dictionary if they does not exists
    dailydir.prepare()
    monitoringdir.prepare()

    ## copy the index.html file if it does not exists
    indexfile.create()

def putfile(file):
    if hasattr(file, "put"):
        file.put()

def add_product(products, dlnum, name, kind, ptype, *args):
    kkind = "daily_product_names" if kind is 'd' else "monitoring_product_names"
    products.setdefault("data" , {})
    names = products.setdefault(kkind, [])


    products['data'].setdefault(dlnum,{}).update( {name:[ptype]+list(args)})
    if not name in names:
        names.append(name)

def product2js(products):

    text = "daily_product_names = [\n    %s\n];\n"%(",\n    ".join("'%s'"%n for n in products['daily_product_names']))
    text += "monitoring_product_names = [\n    %s\n];\n"%(",\n    ".join("'%s'"%n for n in products['monitoring_product_names']))

    text += "dlsnum = [%s];\n"%(",".join("%d"%n for n in products['data']))

    ind = " "*4
    blocks = []
    for dlnum,subproducts in products['data'].iteritems():
        block = ind+"%d : {\n"%dlnum

        subblocks = []
        for name, args in subproducts.iteritems():
            ptype = args[0]
            args = args[1:]
            subblock = "'%s' : ['%s',"%(name, ptype)

            subblock += ",".join("'%s'"%a for a in args)
            subblock += "]"
            subblocks.append(subblock)
        block += (ind*2)+((",\n"+ind*2).join(subblocks))
        

        block += "\n"+ind+"}" 
        blocks.append(block)   
    
    text += "data = {\n%s\n};"%(",\n".join(blocks))
    return text

def run(date=None, dls=range(1,7), plot=True, wiki=True):
    if date is None:
        date = datetime.date.today().isoformat()

    if webroot:
        prepare_web_structure()
    products = io.Product(dailydir.fpath("data.js"), date)

    ## get a list of direct files
    fdirect  = dldir.deliriumfiles(date, "direct")
    ## get a list of reverse file if any 
    freverse = dldir.deliriumfiles(date, "reverse") 
        
    ## loop over delay lines 
    for num in dls:
        context = ("DELIRIUM", "DL%d"%num)
        clear_buffer(context[1])
        log = Log(context=context)
        fls = fdirect.get(num, [])

        
        if len(fls)>1:
            ## take the last file (they are laready sorted from older to most recent)
            file = fls[-1]
            log.warning("%d files found taking the most recent one"%(len(fls)))
        elif not fls:
            log.error("No delirium file found for dl %d"%num)            
            continue
        else:
            file = fls[-1]  
        
        ###
        # The file to write 
        cor_file        = file.replace_ext('_CORR2.txt') # correction text file              
        wk_cor_file     = dailydir.fpath("DL%d_last_CORR.txt"%num) # correction text file in wiki
           

        if DEBUG:
            dld = DelayLineState(deliriumfile=file)
        else:    
            try:                       
                dld = DelayLineState(deliriumfile=file)
            except:
                log.error("cannot load data of '%s'. Is data corrupted ?"%(file))
                
                write_failure(context, file, ([cor_file, wk_cor_file] if wiki else [cor_file]))                
                continue

        fig = [1]
        def inc(fig):
            fig[0] +=1
            return fig[0]
        
        

        ##
        # log the corrections 
        if DEBUG:
            dld.rail.supports.log_corrections(filename=cor_file) 
        else:    
            try:   
                dld.rail.supports.log_corrections(filename=cor_file) 
            except DataError:                
                write_failure(context, file, ([cor_file, wk_cor_file] if wiki else [cor_file]))              
                continue     
            except:
                log.error("cannot compute corrections. Is data corrupted ?")
                write_failure(context, file, ([cor_file, wk_cor_file] if wiki else [cor_file]))             
                continue    
        # copy them to wiki  
        if wiki:      
            cor_file.copy(wk_cor_file)
            log.notice("Correction file copied to %s"%wk_cor_file)
            products.add( num, "Corrections", "d", "txtfile",  "data/daily/"+wk_cor_file.filename)

        ##
        # some plots

        # Deformation/Corrections plots in both directions
        if plot and wiki:
            for k  in ["H", "V"]:
                wiki_file = dailydir.fpath("DL%d_last_%s_CORR.png"%(num,k))
                with wiki_file.open("wb") as g:  
                    dld.rail.plot.deformations(k, figure=inc(fig), fclear=True, save=g)
                #cor_H_fig_file.copy(wk_cor_H_fig_file) 
                log.notice("Correction figure copied to %s"%wiki_file)       
                products.add(num, "%s corection plot"%k, "d", "img", "data/daily/"+wiki_file.filename)

            for k in ["theta", "psi", "phi"]:
                #archive = file.replace_ext('wobble_%s.png'%k)
                wiki_file = dailydir.fpath("DL%d_last_%s_theta.png"%(num,k))
                with wiki_file.open("wb") as g:  
                    dld.carriage.plot.wobble_fit(k, figure=inc(fig), fclear=True, save=g)
                #archive.copy(wiki_file)
                log.notice("Wobble figure copied to %s"%wiki_file)        
                products.add( num, "Wobble %s plot"%k, "d", "img", "data/daily/"+wiki_file.filename)
            

        ## get the wobble monitoring file 
        wblfile = io.WobbleLog(monitoringdir.fpath("DL%d_wobble.txt"%num)).prepare()
        ## add the wobble amplitude results at the end
        wblfile.add_from_dl(dld)

        ## get the wobble monitoring file 
        correctionfile = io.CorrectionLog(monitoringdir.fpath("DL%d_correction.txt"%num)).prepare()
        ## add the wobble amplitude results at the end
        correctionfile.add_from_dl(dld)

        if wiki and plot:
            wdata = wblfile.read_data()
            for k in ["theta", "psi"]:
                ## wobble monitoring
                wiki_file = monitoringdir.fpath("DL%d_%s_monitoring.png"%(num,k)) 
                with wiki_file.open("wb") as g:
                    plots.plot_history(wdata, k, num, "Wobble", fclear=True,figure=inc(fig), save=g)
                    log.notice("Wobble monitoring updated to  %s"%wiki_file)       
                    products.add( num, "Wobble %s monitoring plot"%k, "m", "img", "data/monitoring/"+wiki_file.filename)
                ## wobble vs temperature
                wiki_file = monitoringdir.fpath("DL%d_%s_temp.png"%(num,k)) 
                with wiki_file.open("wb") as g:
                    plots.plot_temperature(wdata, k, num, "Wobble", fclear=True,figure=inc(fig), save=g)
                    log.notice("Wobble monitoring updated to  %s"%wiki_file)       
                    products.add( num, "Wobble %s temp plot"%k, "m", "img", "data/monitoring/"+wiki_file.filename)

            wdata = correctionfile.read_data()        
            for k in ["Nv", "Nh"]:        
                ## number of correction monitoring    
                wiki_file = monitoringdir.fpath("DL%d_correction_%s_monitoring.png"%(num,k)) 
                with wiki_file.open("wb") as g:
                    plots.plot_history(wdata, k, num, "Corrections", unit="#", fclear=True,figure=inc(fig), save=g)
                    log.notice("Coorection monitoring updated to  %s"%wiki_file)       
                    products.add( num, "Correction %s monitoring plot"%k, "m", "img", "data/monitoring/"+wiki_file.filename)    

                ##  number of correction vs temperature 
                wiki_file = monitoringdir.fpath("DL%d_correction_%s_temp.png"%(num,k)) 
                with wiki_file.open("wb") as g:
                    plots.plot_temperature(wdata, k, num, "Corrections", unit="#", fclear=True,figure=inc(fig), save=g)
                    log.notice("Correction vs temp updated to  %s"%wiki_file)       
                    products.add( num, "Correction %s temp plot"%k, "m", "img", "data/monitoring/"+wiki_file.filename)                    
                
                    

        ## take the reverse files 
        flr = freverse.get(num, [])
        if flr:
            log = Log(context=("DELIRIUM", "DL%d"%num, "REVERSE"))

            if len(flr)>1:
                ## take the last file (already sorted from last to newer)
                file_r = flr[-1]
                log.notice("%d files found taking the last one"%(len(flr)))
            elif not flr:
                log.error("No reverse delirium file found for dl %d"%num)            
                continue
            else:
                file_r = flr[-1]                     
            
            if DEBUG:
                dlr = DelayLineState(deliriumfile=file_r)
            else:    
                try:                       
                    dlr = DelayLineState(deliriumfile=file_r)
                except DataError:
                    log.error("Histeresis cannot be computed")
                    continue                          
                except:
                    log.error("cannot load data of '%s'. Is data corrupted ?"%(file_r))
                    log.error("Histeresis cannot be computed")
                    continue
            
            if DEBUG:
                hyst = DelayLineHysteresis(dld, dlr)
            else:    
                try:
                    hyst = DelayLineHysteresis(dld, dlr)
                except Exception as e:
                    log.error("Cannot compute hysteresis got error: '%s'"%(e))
                    continue    

            ## get the Hysteresis  monitoring file 
            hystfile = io.HysteresisLog(monitoringdir.fpath("DL%d_hysteresis.txt"%num)).prepare()
            ## add the wobble amplitude results 
            hystfile.add_from_hysteresis(hyst)

            if plot and wiki:

                # The daily histeresis plots 
                for k in ["theta", "psi"]:
                    ## histeresis plot
                    wiki_file = dailydir.fpath("DL%d_%s_histeresis.png"%(num,k)) 
                    with wiki_file.open("wb") as g:
                        hyst.plot.histeresis(k,  fclear=True, figure=inc(fig), save=g)
                        
                        log.notice("Histeresis %s plot updated to  %s"%(k,wiki_file))
                        products.add(num, "Hysteresis %s plot"%k, "d",  "img", "data/daily/"+wiki_file.filename)
            

                # monitoring plots        
                wdata = hystfile.read_data()                       
                for k in ["hysteresis"]: 
                    wiki_file = monitoringdir.fpath("DL%d_%s_monitoring.png"%(num,k)) 
                    with wiki_file.open("wb") as g:
                        plots.plot_history(wdata, k, num, "Hysteresis", unit="arcsec", fclear=True,figure=inc(fig), save=g)
                        log.notice("Hysteresis monitoring updated to  %s"%wiki_file)       
                        products.add(num, " %s monitoring plot"%k, "m", "img", "data/monitoring/"+wiki_file.filename)    
                    
                    wiki_file = monitoringdir.fpath("DL%d_%s_temp.png"%(num,k)) 
                    with wiki_file.open("wb") as g:
                        plots.plot_temperature(wdata, k, num, "Hysteresis", unit="arcsec", fclear=True,figure=inc(fig), save=g)
                        log.notice("Hysteresis vs temp updated to  %s"%wiki_file)       
                        products.add(num, "%s temp plot"%k, "m", "img", "data/monitoring/"+wiki_file.filename)                    
                            
                        
        else:
            log.warning("No reverse file, isteresis not computed")
            ### just add the previous histeresis plot in product
            if wiki:
                for k in ["hysteresis"]:
                    wiki_file = monitoringdir.fpath("DL%d_%s_monitoring.png"%(num,k)) 
                    products.add(num, "%s monitoring plot"%k, "m", "img", "data/monitoring/"+wiki_file.filename)                    
                    wiki_file = monitoringdir.fpath("DL%d_%s_temp.png"%(num,k)) 
                    products.add(num, "%s temp plot"%k, "m", "img", "data/monitoring/"+wiki_file.filename)    

        ##
        # add the data.js in the wiki    
        if wiki:  
            products.flushjs()            

def write_failure(context, origfile, files):
    for file in files:
        with file.open("w") as g:
            g.write("!!!! Corection could not be computed. Got the following errors : \n ")
            g.write("script executed at %s\n"%(time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())))
            g.write("on file %s\n"%origfile) 
            g.write("".join(get_buffer(context, "ERROR")))
