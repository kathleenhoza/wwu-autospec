#Plotter takes a Tk root object and uses it as a base to spawn Tk Toplevel plot windows.

import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from tkinter import *
from tkinter import filedialog
import colorutils
from matplotlib import cm
import matplotlib.tri as mtri


import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from verticalscrolledframe import VerticalScrolledFrame

#These are related to the region of spectra that are sensitive to polarization artifacts. This is at high phase angles between 1000 and 1400 nm.
global MIN_WAVELENGTH_ARTIFACT_FREE
MIN_WAVELENGTH_ARTIFACT_FREE=1000
global MAX_WAVELENGTH_ARTIFACT_FREE
MAX_WAVELENGTH_ARTIFACT_FREE=1400
global MIN_G_ARTIFACT_FREE
MIN_G_ARTIFACT_FREE=-20
global MAX_G_ARTIFACT_FREE
MAX_G_ARTIFACT_FREE=40

class Plotter():
    def __init__(self, controller,dpi, style):
        
        self.num=0
        self.controller=controller
        self.notebook=self.controller.view_notebook
        self.dpi=dpi
        self.titles=[]
        self.style=style
        plt.style.use(style)
        
        self.tabs=[]
        self.samples={}
        self.sample_objects=[]
        
        self.notebook.bind('<Button-1>',lambda event: self.notebook_click(event))
        self.notebook.bind('<Motion>',lambda event: self.mouseover_tab(event))
        self.menus=[]
        
        self.save_dir=None #This will get set if the user saves a plot so that the next time they click save plot, the save dialog opens into the same directory where they just saved.
    
    def get_index(self, array, val):
        index = (np.abs(array - val)).argmin()
        return index
        
    def notebook_click(self, event):
        self.close_right_click_menus(event)
        self.maybe_close_tab(event)
    
    def update_tab_names(self):
        pass
        
    def new_tab(self):
        tab=Tab(self, 'New tab',[], title_override=True)
        tab.ask_which_samples()
        
        
    def set_height(self, height):
        pass
        for tab in self.tabs:
            tab.top.configure(height=height)

    def plot_spectra(self, title, file, caption, exclude_wr=True):
        if title=='':
            title='Plot '+str(self.num+1)
            self.num+=1
        elif title in self.titles:
            j=1
            new=title+' ('+str(j)+')'
            while new in self.titles:
                j+=1
                new=title+' ('+str(j)+')'
            title=new
        self.titles.append(title)
                

        try:
            wavelengths, reflectance, labels=self.load_data(file)
        except:
            raise(Exception('Error loading data!'))
            return
            

        for i, spectrum_label in enumerate(labels):
            sample_label=spectrum_label.split(' (i')[0]
            
            #If we don't have any data from this file yet, add it to the samples dictionary, and place the first sample inside.
            if file not in self.samples:
                self.samples[file]={}
                new=Sample(sample_label, file,title)
                self.samples[file][sample_label]=new
                self.sample_objects.append(new)
            #If there is already data associated with this file, check if we've already got the sample in question there. If it doesn't exist, make it. If it does, just add this spectrum and label into its data dictionary.
            else:
                sample_exists=False 
                for sample in self.samples[file]:
                    if self.samples[file][sample].name==sample_label:
                        sample_exists=True

                if sample_exists==False:
                    new=Sample(sample_label, file,title)
                    self.samples[file][sample_label]=new
                    self.sample_objects.append(new)
                    
            #if spectrum_label not in self.samples[file][sample_label].spectrum_labels: #This should do better and actually check that all the data is an exact duplicate, but that seems hard. Just don't label things exactly the same and save them in the same file with the same viewing geometry.
               # self.samples[file][sample_label].add_spectrum(spectrum_label, reflectance[i], wavelengths)
            self.samples[file][sample_label].add_spectrum(spectrum_label, reflectance[i], wavelengths)


        new_samples=[]
        for sample in self.samples[file]:
            new_samples.append(self.samples[file][sample])
            #tab=Tab(self, title,[self.samples[file][sample]])
        
        tab=Tab(self,title,[new_samples[0]])

    # def savefig(self,title, sample=None):
    #     self.draw_plot(title, 'v2.0')
    #     self.plots[title].savefig(title)
    #     self.draw_plot(self.style)
        
        
    def load_data(self, file, format='spectral_database_csv'):
        labels=[]
        #This is the format I was initially using. It is a simple .tsv file with a single row of headers e.g. Wavelengths     Sample_1 (i=0 e=30)     Sample_2 (i=0 e=30).
        if format=='simple_tsv':
            data = np.genfromtxt(file, names=True, dtype=float,encoding=None,delimiter='\t',deletechars='')
            labels=list(data.dtype.names)[1:] #the first label is wavelengths
            for i in range(len(labels)):
                labels[i]=labels[i].replace('_(i=',' (i=').replace('_e=',' e=')
        #This is the current format, which is compatible with the WWU spectral library format.
        elif format=='spectral_database_csv':
            skip_header=1
            
            labels_found=False #We want to use the Sample Name field for labels, but if we haven't found that yet we may use Data ID, Sample ID, or mineral name instead.
            with open(file,'r') as file2:
                line=file2.readline()
                i=0
                while line.split(',')[0].lower()!='wavelength' and line !='' and line.lower()!='wavelength\n': #Formatting can change slightly if you edit your .csv in libreoffice or some other editor, this captures different options. line will be '' only at the end of the file (it is \n for empty lines)
                    i+=1
                    if line[0:11]=='Sample Name':
                        labels=line.split(',')[1:]
                        labels[-1]=labels[-1].strip('\n')
                        labels_found=True #
                    elif line[0:16]=='Viewing Geometry':
                        for i, geom in enumerate(line.split(',')[1:]):
                            geom=geom.strip('\n')
                            labels[i]+=' ('+geom+')'
                    elif line[0:7]=='Data ID':
                        if labels_found==False: #Only use Data ID for labels if we haven't found the Sample Name field.
                            labels=line.split(',')[1:]
                            labels[-1]=labels[-1].strip('\n')
                    elif line[0:9]=='Sample ID':
                        if labels_found==False: #Only use Sample ID for labels if we haven't found the Sample Name field.
                            labels=line.split(',')[1:]
                            labels[-1]=labels[-1].strip('\n')
                    elif line[0:12]=='Mineral Name':
                        if labels_found==False: #Only use Data ID for labels if we haven't found the Sample Name field.
                            labels=line.split(',')[1:]
                            labels[-1]=labels[-1].strip('\n')
                    skip_header+=1
                    line=file2.readline()

            data = np.genfromtxt(file, skip_header=skip_header, dtype=float,delimiter=',',encoding=None,deletechars='')

        data=zip(*data)
        wavelengths=[]
        reflectance=[]
        for i, d in enumerate(data):
            if i==0: wavelengths=d[60:] #the first column in my .csv (now first row) was wavelength in nm. Exclude the first 100 values because they are typically very noisy.
            else: #the other columns are all reflectance values
                d=np.array(d)
                reflectance.append(d[60:])
                #d2=d/np.max(d) #d2 is normalized reflectance
                #reflectance[0].append(d)
                #reflectance[1].append(d2)
        return wavelengths, reflectance, labels
        
    def maybe_close_tab(self,event):
        dist_to_edge=self.dist_to_edge(event)
        if dist_to_edge==None: #not on a tab
            return
        
        if dist_to_edge<18:
            index = self.notebook.index("@%d,%d" % (event.x, event.y))
            if index!=0:
                self.notebook.forget(index)
                self.notebook.event_generate("<<NotebookTabClosed>>")
                
    #This capitalizes Xs for closing tabs when you hover over them.
    def mouseover_tab(self,event):
        dist_to_edge=self.dist_to_edge(event)
        if dist_to_edge==None or dist_to_edge>17: #not on an X, or not on a tab at all.
            for i, tab in enumerate(self.notebook.tabs()):
                if i==0:
                    continue #Don't change text on Goniometer view tab
                text=self.notebook.tab(tab, option='text')
                self.notebook.tab(tab, text=text[0:-1]+'x')

        else:
            tab=self.notebook.tab("@%d,%d" % (event.x, event.y))
            text=tab['text'][:-1]

            if 'Goniometer' in text:
                return
            else:
                self.notebook.tab("@%d,%d" % (event.x, event.y),text=text+'X')
                
    def close_right_click_menus(self,event):
        for menu in self.menus:
            menu.unpost()
            
    def dist_to_edge(self,event):
        id_str='@'+str(event.x)+','+str(event.y) #This is the id for the tab that was just clicked on.
        try:
            tab0=self.notebook.tab(id_str)
            tab=self.notebook.tab(id_str)
        #There might not actually be any tab here at all.
        except:
            return None
        dist_to_edge=0
        while tab==tab0: #While not leaving the current tab, walk pixel by pixel toward the tab edge to count how far it is.
            dist_to_edge+=1
            id_str='@'+str(event.x+dist_to_edge)+','+str(event.y)
            try:
                tab=self.notebook.tab(id_str)
            except: #If this didn't work, we were off the right edge of any tabs.
                break
            
        return(dist_to_edge)
        
    def get_e_i_g(self, label): #Extract e, i, and g from a label.
        i=int(label.split('i=')[1].split(' ')[0])
        e=int(label.split('e=')[1].strip(')'))
        if i<=0:
            g=e-i
        else:
            g=-1*(e-i)
        return e, i, g
        
    def artifact_danger(self, g, left=0, right=100000000000000000000):
        if g<MIN_G_ARTIFACT_FREE or g>MAX_G_ARTIFACT_FREE: #If the phase angle is outside the safe region, we might have potential artifacts, but only at specific wavelengths.
            if left>MIN_WAVELENGTH_ARTIFACT_FREE and left<MAX_WAVELENGTH_ARTIFACT_FREE: #if the left wavelength is in the artifact zone
                return True
            elif right>MIN_WAVELENGTH_ARTIFACT_FREE and right<MAX_WAVELENGTH_ARTIFACT_FREE: #if the right wavelength is in the artifact zone
                return True
            elif left<MIN_WAVELENGTH_ARTIFACT_FREE and right>MAX_WAVELENGTH_ARTIFACT_FREE: #If the region spans the artifact zone
                return True
            else:
                return False
        else: #If we're at a safe phase angle
            return False
class Sample():
    def __init__(self, name, file, title):#colors):
        #self.colors=colors
        # self.index=-1
        # self.__next_color=self.colors[0]
        self.title=title
        self.name=name
        self.file=file
        self.data={}
        self.spectrum_labels=[]
    
    def add_spectrum(self,spectrum_label, reflectance, wavelengths):
        self.spectrum_labels.append(spectrum_label)
        self.data[spectrum_label]={'reflectance':[],'wavelength':[]}
        self.data[spectrum_label]['reflectance']=reflectance
        self.data[spectrum_label]['wavelength']=wavelengths
    
    def add_offset(self, offset):
        print(offset)
        try:
            offset=float(offset)
        except:
            print('invalid offset')
            return
        
        for spec_label in self.data:
            if 'reflectance' in self.data[spec_label]:
                old=np.array(self.data[spec_label]['reflectance'])
                self.data[spec_label]['reflectance']=old+offset
    #generate a list of hex colors that are evenly distributed from dark to light across a single hue. 
    def set_colors(self, hue):
        N=len(self.spectrum_labels)/2
        if len(self.spectrum_labels)%2!=0:
            N+=1
        N=int(N)+2
        
        hsv_tuples = [(hue, 1, x*1.0/N) for x in range(4,N)]
        hsv_tuples=hsv_tuples+[(hue, (N-x)*1.0/N,1) for x in range(N)]
        self.colors=[]
        for tuple in hsv_tuples:
            self.colors.append(colorutils.hsv_to_hex(tuple))
            
        self.index=-1
        #self.__next_color=self.colors[0]
        
    def next_color(self):
        self.index+=1
        self.index=self.index%len(self.colors)
        return self.colors[self.index]
        
class Tab():
    #Title override is true if the title of this individual tab is set manually by user.
    #If it is False, then the tab and plot title will be a combo of the file title plus the sample that is plotted.
    def __init__(self, plotter, title, samples,tab_index=None,title_override=False, geoms={'i':[],'e':[]}, scrollable=True,original=None,x_axis='wavelength',y_axis='reflectance',xlim=None,ylim=None, exclude_artifacts=False, exclude_specular=False, specularity_tolerance=None):
        self.plotter=plotter
        if original==None: #This is true if we're not normalizing anything. holding on to the original data lets us reset.
            self.original_samples=list(samples)

        else:
            self.original_samples=original
        self.samples=samples
        self.geoms=geoms
        if False:#title_override==False:
            self.title=title+ ': '+samples[0].name
            #self.title=samples[0].name
        else:
            self.title=title
    
            
        self.x_axis=x_axis
        self.y_axis=y_axis
        self.xlim=xlim
        self.ylim=ylim
        self.exclude_artifacts=exclude_artifacts
        self.exclude_specular=exclude_specular
        self.specularity_tolerance=specularity_tolerance
        
        self.width=self.plotter.notebook.winfo_width()
        self.height=self.plotter.notebook.winfo_height()
        
        #If we need a bigger frame to hold a giant long legend, expand.
        self.legend_len=0
        for sample in self.samples:
            self.legend_len+=len(sample.spectrum_labels)
        self.legend_height=self.legend_len*21+100 #21 px per legend entry.
        self.plot_scale=(self.height-130)/21
        self.plot_width=self.width/9#very vague character approximation of plot width
        self.oversize_legend=False
        if self.height>self.legend_height:scrollable=False
        else:
            self.oversize_legend=True

        if scrollable: #User can specify this in edit_plot#self.legend_len>7:
            self.top=VerticalScrolledFrame(self.plotter.controller, self.plotter.notebook)

        else:
            self.top=NotScrolledFrame(self.plotter.notebook)
            
        self.top.min_height=np.max([self.legend_height, self.height-50])
        #self.top.bind("<Visibility>", self.on_visibility)
        self.top.pack()
        
        #If this is being created from the File -> Plot option, or from right click -> new tab, just put the tab at the end.
        if tab_index==None:
            self.plotter.notebook.add(self.top,text=self.title+' x')
            self.plotter.notebook.select(self.plotter.notebook.tabs()[-1])
            self.index=self.plotter.notebook.index(self.plotter.notebook.select())
        #If this is being called after the user did Right click -> choose samples to plot, put it at the same index as before.
        else:
            self.plotter.notebook.add(self.top,text=self.title+' x')
            self.plotter.notebook.insert(tab_index, self.plotter.notebook.tabs()[-1])
            self.plotter.notebook.select(self.plotter.notebook.tabs()[tab_index])
            self.index=tab_index
            
        
        #self.fig = mpl.figure.Figure(figsize=(width/self.plotter.dpi, height/self.plotter.dpi), dpi=self.plotter.dpi) 
        self.fig = mpl.figure.Figure(figsize=(self.width/self.plotter.dpi, self.height/self.plotter.dpi),dpi=self.plotter.dpi) 
 
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.top.interior)
        self.canvas.get_tk_widget().bind('<Button-3>',lambda event: self.open_right_click_menu(event))
        self.canvas.get_tk_widget().bind('<Button-1>',lambda event: self.close_right_click_menu(event))


            
        def resize_fig(event):
            return
            current_index=self.plotter.notebook.index(self.plotter.notebook.select())
            if self.index!=current_index: return #Only do all the figure resizing stuff for the visible figure. This helps with speed.
            #might be smart to make all this stuff happen only for visible plot.
            if self.legend_height>event.height and self.oversize_legend==False: #We only need to do most of this once, but we'll still adjust the size of the figure at each resize.
                self.top.min_height=self.legend_height
                #Find height of legend
                #Find height of event
                #fig height needs to be related to ratio of event/legend.

                self.oversize_legend=True
            if self.legend_height>event.height:
                pos1 = self.plot.plot.get_position() # get the original position 

                diff=event.height-self.height
                if np.abs(diff)<5:return
                self.height=event.height

                
                ratio=event.height/self.legend_height

                inv=self.legend_height/event.height
                y0=y0+self.legend_height/130000
                if y0>0.88:
                    y0=0.88
                #When legend is big, it starts out too far down.
                #So add a component that depends on legend height and will make y0 bigger when the legend is bigger
                #It is also too small when the legend is big. The height needs to depend on both the ratio, and also the absolute legend size. Just do +legend_size/1000?
                pos2 = [pos1.x0, y0,  pos1.width, ratio/1.3-0.04+self.legend_height/130000] 
                self.plot.plot.set_position(pos2) # set a new position, slightly adjusted so it doesn't go off the edges of the screen.

            else:
                self.top.min_height=0
                if self.oversize_legend==True:
                    pos1 = self.plot.plot.get_position() # get the original position 
                    pos2 = [pos1.x0-0.01, pos1.y0-0.2,  pos1.width, pos1.height] 
                    self.plot.plot.set_position(pos2) # set a new position, slightly adjusted so it doesn't go off the edges of the screen.
                    self.oversize_legend=False
                self.top.scrollbar.pack_forget() #Shouldn't be needed, but for some reason we get a little strip beneath top.interior that doesn't go away and requires a scrollbar to see otherwise.
            
        #self.canvas.get_tk_widget().config(width=300,height=300)
        self.canvas.get_tk_widget().pack(expand=True,fill=BOTH)
        self.top.bind('<Configure>',resize_fig)

        
        self.plot=Plot(self.plotter, self.fig, self.samples,self.title, self.oversize_legend,self.plot_scale,self.plot_width,x_axis=self.x_axis,y_axis=self.y_axis,xlim=self.xlim,ylim=self.ylim, exclude_artifacts=self.exclude_artifacts)



        self.canvas.draw()
        

        self.popup_menu = Menu(self.top.interior, tearoff=0)
        if self.x_axis=='wavelength' and self.y_axis=='reflectance':
            self.popup_menu.add_command(label="Edit plot",
                                        command=self.ask_which_samples)
            self.popup_menu.add_command(label="Open analysis tools",
                                        command=self.open_analysis_tools)
        else:
            self.popup_menu.add_command(label="Options",
                                        command=self.open_options)
        self.popup_menu.add_command(label="Save plot",
                                    command=self.save)

        self.popup_menu.add_command(label="New tab",
                                    command=self.new)
        self.popup_menu.add_command(label="Close tab",
                                    command=self.close)

        self.plotter.menus.append(self.popup_menu)
    def freeze(self):
        self.frozen=True
    def unfreeze(self):
        self.frozen=False
    def save(self):
        self.plot.save()
    
    def new(self):
        self.plotter.new_tab()
    
    def open_options(self):
        print('Options!')
        self.plotter.controller.open_options(self, self.title)
    def set_title(self,title):
        print(title)
        self.title=title
        self.plotter.notebook.tab(self.top, text = title+' x')
        self.plot.set_title(title)
        
    #This is needed so that this can be one of the parts of a dict for buttons: self.view_notebook.select:[lambda:tab.get_top()],.
    #That way when the top gets recreated in refresh, the reset button will get the new one instead of creating errors by getting the old one.
    def get_top(self):
        return self.top
    

        
    def set_exclude_artifacts(self, bool):
        print(bool)
        for i, sample in enumerate(self.plot.samples):
            sample.set_colors(self.plot.hues[i%len(self.plot.hues)])
        self.exclude_artifacts=bool
        i=len(self.plot.plot.lines)
        j=0
        #Delete all of the lines except annotations e.g. vertical lines showing where slopes are being calculated.
        for x in range(i):
            if self.plot.plot.lines[j] not in self.plot.annotations:
                self.plot.plot.lines[j].remove()
            else:
                j+=1
        self.plot.exclude_artifacts=bool
        self.plot.draw()
        self.canvas.draw()

    def on_visibility(self, event):
        self.close_right_click_menu(event)

    #find reflectance at a given wavelength.
    #if we're on the edges, average out a few values.
    def get_vals(self, wavelengths, reflectance, nm):
        index = (np.abs(wavelengths - nm)).argmin() #find index of wavelength 

        
        r=reflectance[index]
        w=wavelengths[index]
        
        if wavelengths[index]<600 or wavelengths[index]>2200: #If we're on the edges, spectra are noisy. Calculate slopes based on an average.
            if index<len(reflectance)-3 and index>2:
                r=np.mean(reflectance[index-3:index+3])
                w=wavelengths[index]
            elif index>2:
                r=np.mean(reflectance[-7:-1])
                w=wavelengths[-4]
            elif index<len(reflectance)-3:
                r=np.mean(reflectance[0:6]) #Take the first 6 values if you are at the beginning
                w=wavelengths[3]
        

        return w, r
    def get_index(self, array, val):
        index = (np.abs(array - val)).argmin()
        return index
        
    def offset(self, sample_name, offset):
        if ':' in sample_name:
            title=sample_name.split(':')[0]
            name=sample_name.split(':')[1]
        else:
            title=None
            name=sample_name
        for i, sample in enumerate(self.samples):
            if name==sample.name:
                if title==None or sample.title==title:
                    print('found it!')
                    print(sample.name)
                    break
        self.samples.pop(i)
        print(len(self.original_samples))
        
        new_sample=Sample(sample.name, sample.file, sample.title)
        
        new_sample.data={}#dict(sample.data)
        for key in sample.data:
            new_sample.data[key]={}
            for key2 in sample.data[key]:
                new_sample.data[key][key2]=list(sample.data[key][key2])
        new_sample.spectrum_labels=list(sample.spectrum_labels)
        print('have not added offset')
        for sample in self.original_samples:
            print(sample.name)
            for label in sample.spectrum_labels:
                print(sample.data[label]['reflectance'][0])
        new_sample.add_offset(offset)
        print('just added offset')
        for sample in self.original_samples:
            print(sample.name)
            for label in sample.spectrum_labels:
                print(sample.data[label]['reflectance'][0])
        self.samples.insert(i,new_sample)
        for sample in self.original_samples:
            print(sample.name)
            for label in sample.spectrum_labels:
                print(sample.data[label]['reflectance'][0])
        self.refresh(original=self.original_samples)
        

    def calculate_avg_reflectance(self, left, right):
        left, right=self.validate_left_right(left, right)
        avgs=[]
        self.incidence_samples=[]
        self.emission_samples=[]
        artifact_warning=False
        
        self.contour_sample=Sample('all samples','file','title')
        self.contour_sample.data={'all samples':{'i':[],'e':[],'band depth':[]}}
        self.contour_sample.spectrum_labels=['all samples']
        
        for i, sample in enumerate(self.samples):
            incidence_sample=Sample(sample.name,sample.file,sample.title)
            emission_sample=Sample(sample.name,sample.file,sample.title)
            for label in sample.spectrum_labels: 
                e,i,g=self.plotter.get_e_i_g(label)
                
                if self.exclude_artifacts: #If we are excluding artifacts, don't calculate reflectance for anything in the range that is considered to be suspect
                    if self.plotter.artifact_danger(g, left, right):
                        artifact_warning=True
                        continue
                        
                wavelengths=np.array(sample.data[label]['wavelength'])
                reflectance=np.array(sample.data[label]['reflectance'])

                index_left=self.get_index(wavelengths, left)
                index_right=self.get_index(wavelengths, right)

                avg=np.mean(reflectance[index_left:index_right])

                incidence=sample.name+' (i='+str(i)+')'
                emission=sample.name+' (e='+str(e)+')'
                phase=sample.name
               
                
                if incidence not in incidence_sample.data:
                    incidence_sample.data[incidence]={'e':[],'g':[],'average reflectance':[]}
                    incidence_sample.spectrum_labels.append(incidence)
                if emission not in emission_sample.data:
                    emission_sample.data[emission]={'i':[],'average reflectance':[]}
                    emission_sample.spectrum_labels.append(emission)

                
                incidence_sample.data[incidence]['e'].append(e)
                incidence_sample.data[incidence]['g'].append(g)
                incidence_sample.data[incidence]['average reflectance'].append(avg)
                emission_sample.data[emission]['i'].append(i)
                emission_sample.data[emission]['average reflectance'].append(avg)
                
                self.contour_sample.data['all samples']['e'].append(e)
                self.contour_sample.data['all samples']['i'].append(i)
                self.contour_sample.data['all samples']['average reflectance'].append(avg)
                
                avgs.append(label+': '+str(avg))
            self.emission_samples.append(emission_sample)
            self.incidence_samples.append(incidence_sample)
        self.plot.draw_vertical_lines([left, right])

        return left, right, avgs, artifact_warning
        
    def calculate_band_centers(self, left, right):
        left, right=self.validate_left_right(left, right)
        centers=[]
        self.incidence_samples=[]
        self.emission_samples=[]
        artifact_warning=False
        
        self.contour_sample=Sample('all samples','file','title')
        self.contour_sample.data={'all samples':{'i':[],'e':[],'band center':[]}}
        self.contour_sample.spectrum_labels=['all samples']

        
        for i, sample in enumerate(self.samples):
            incidence_sample=Sample(sample.name,sample.file,sample.title)
            emission_sample=Sample(sample.name,sample.file,sample.title)
            for label in sample.spectrum_labels: 
                e,i,g=self.plotter.get_e_i_g(label)
                
                if self.exclude_artifacts: #If we are excluding artifacts, don't calculate slopes for anything in the range that is considered to be suspect
                    if self.plotter.artifact_danger(g, left, right):
                        artifact_warning=True
                        continue
                        
                wavelengths=np.array(sample.data[label]['wavelength'])
                reflectance=np.array(sample.data[label]['reflectance'])
                
                #find reflectance at left and right wavelengths.
                #if we're on the edges, average out a few values.
                w_left, r_left=self.get_vals(wavelengths, reflectance,left)
                index_left=self.get_index(wavelengths, left)

                
                w_right, r_right=self.get_vals(wavelengths, reflectance, right)
                index_right=self.get_index(wavelengths, right)

                
                
                slope=(r_right-r_left)/(w_right-w_left)
                r_min=np.min(reflectance[index_left:index_right])
                r_max=np.max(reflectance[index_left:index_right])
                
                index_r_min=self.get_index(reflectance,r_min)
                index_r_max=self.get_index(reflectance,r_max)
                w_min=wavelengths[index_r_min]
                w_max=wavelengths[index_r_max]
                delta_w_min=w_min-w_left
                delta_w_max=w_max-w_left
                
                r_continuum_min=r_left+slope*delta_w_min
                r_continuum_max=r_left+slope*delta_w_max

                
                depth_min=r_continuum_min-r_min
                depth_max=r_continuum_max-r_max
                
                if np.abs(depth_min)>np.abs(depth_max):
                    center=wavelengths[index_r_min]
                else:
                    center=wavelengths[index_r_max]
                
                

                            
                incidence=sample.name+' (i='+str(i)+')'
                emission=sample.name+' (e='+str(e)+')'
                phase=sample.name
               
                
                if incidence not in incidence_sample.data:
                    incidence_sample.data[incidence]={'e':[],'g':[],'band center':[]}
                    incidence_sample.spectrum_labels.append(incidence)
                if emission not in emission_sample.data:
                    emission_sample.data[emission]={'i':[],'band center':[]}
                    emission_sample.spectrum_labels.append(emission)


                
                incidence_sample.data[incidence]['e'].append(e)
                incidence_sample.data[incidence]['g'].append(g)
                incidence_sample.data[incidence]['band center'].append(center)
                emission_sample.data[emission]['i'].append(i)
                emission_sample.data[emission]['band center'].append(center)
                
                self.contour_sample.data['all samples']['e'].append(e)
                self.contour_sample.data['all samples']['i'].append(i)
                self.contour_sample.data['all samples']['band center'].append(center)

                
                centers.append(label+': '+str(center))
            self.emission_samples.append(emission_sample)
            self.incidence_samples.append(incidence_sample)
        self.plot.draw_vertical_lines([left, right])

        return left, right, centers, artifact_warning
        
    def calculate_band_depths(self, left, right):
        left, right=self.validate_left_right(left, right)
        depths=[]
        self.incidence_samples=[]
        self.emission_samples=[]
        self.phase_samples=[]
        artifact_warning=False
        
        self.contour_sample=Sample('all samples','file','title')
        self.contour_sample.data={'all samples':{'i':[],'e':[],'band depth':[]}}
        self.contour_sample.spectrum_labels=['all samples']
    
        
        
        for i, sample in enumerate(self.samples):
            incidence_sample=Sample(sample.name,sample.file,sample.title)
            emission_sample=Sample(sample.name,sample.file,sample.title)
            for label in sample.spectrum_labels: 
                e,i,g=self.plotter.get_e_i_g(label)
                
                if self.exclude_artifacts: #If we are excluding artifacts, don't calculate slopes for anything in the range that is considered to be suspect
                    if self.plotter.artifact_danger(g, left, right):
                        artifact_warning=True
                        continue
                        
                wavelengths=np.array(sample.data[label]['wavelength'])
                reflectance=np.array(sample.data[label]['reflectance'])
                
                #find reflectance at left and right wavelengths.
                #if we're on the edges, average out a few values.
                w_left, r_left=self.get_vals(wavelengths, reflectance,left)
                index_left=self.get_index(wavelengths, left)

                
                w_right, r_right=self.get_vals(wavelengths, reflectance, right)
                index_right=self.get_index(wavelengths, right)
                
                
                slope=(r_right-r_left)/(w_right-w_left)
                r_min=np.min(reflectance[index_left:index_right])
                r_max=np.max(reflectance[index_left:index_right])
                
                index_r_min=self.get_index(reflectance,r_min)
                index_r_max=self.get_index(reflectance,r_max)
                w_min=wavelengths[index_r_min]
                w_max=wavelengths[index_r_max]
                delta_w_min=w_min-w_left
                delta_w_max=w_max-w_left
                
                r_continuum_min=r_left+slope*delta_w_min
                r_continuum_max=r_left+slope*delta_w_max

                
                depth_min=r_continuum_min-r_min
                depth_max=r_continuum_max-r_max
                
                if np.abs(depth_min)>np.abs(depth_max):
                    depth=depth_min
                else:
                    depth=depth_max
                
                                
                incidence=sample.name+' (i='+str(i)+')'
                emission=sample.name+' (e='+str(e)+')'
                phase=sample.name
               
                
                if incidence not in incidence_sample.data:
                    incidence_sample.data[incidence]={'e':[],'g':[],'band depth':[]}
                    incidence_sample.spectrum_labels.append(incidence)
                if emission not in emission_sample.data:
                    emission_sample.data[emission]={'i':[],'band depth':[]}
                    emission_sample.spectrum_labels.append(emission)

                
                incidence_sample.data[incidence]['e'].append(e)
                incidence_sample.data[incidence]['g'].append(g)
                incidence_sample.data[incidence]['band depth'].append(depth)
                emission_sample.data[emission]['i'].append(i)
                emission_sample.data[emission]['band depth'].append(depth)
                
                self.contour_sample.data['all samples']['e'].append(e)
                self.contour_sample.data['all samples']['i'].append(i)
                self.contour_sample.data['all samples']['band depth'].append(depth)

                
                depths.append(label+': '+str(depth))
            self.emission_samples.append(emission_sample)
            self.incidence_samples.append(incidence_sample)
        self.plot.draw_vertical_lines([left, right])

        return left, right, depths, artifact_warning
        
    def get_e_i_g(self, label): #Extract e, i, and g from a label.
        i=int(label.split('i=')[1].split(' ')[0])
        e=int(label.split('e=')[1].strip(')'))
        if i<=0:
            g=e-i
        else:
            g=-1*(e-i)
        return e, i, g

        
    def calculate_slopes(self, left, right):
        left, right=self.validate_left_right(left, right)
        slopes=[]
        self.incidence_samples=[]
        self.emission_samples=[]
        self.phase_samples=[]
        
        self.contour_sample=Sample('all samples','file','title')
        self.contour_sample.data={'all samples':{'i':[],'e':[],'slope':[]}}
        self.contour_sample.spectrum_labels=['all samples']
        
        

        artifact_warning=False

        for i, sample in enumerate(self.samples):
            incidence_sample=Sample(sample.name,sample.file,sample.title)
            emission_sample=Sample(sample.name,sample.file,sample.title)
            phase_sample=Sample(sample.name,sample.file,sample.title)
            for label in sample.spectrum_labels: 
                e,i,g=self.plotter.get_e_i_g(label)
                
                if self.exclude_artifacts: #If we are excluding artifacts, don't calculate slopes for anything in the range that is considered to be suspect
                    if self.plotter.artifact_danger(g, left, right):
                        artifact_warning=True #We'll return this to the controller, which will throw up a dialog warning the user that we are skipping some spectra.
                        continue

                        
                wavelengths=np.array(sample.data[label]['wavelength'])
                reflectance=np.array(sample.data[label]['reflectance'])
                
                #find reflectance at left and right wavelengths.
                #if we're on the edges, average out a few values.
                w_left, r_left=self.get_vals(wavelengths, reflectance,left)
                w_right, r_right=self.get_vals(wavelengths, reflectance, right)
                
                slope=(r_right-r_left)/(w_right-w_left)
                
                
                
                incidence=sample.name+' (i='+str(i)+')'
                emission=sample.name+' (e='+str(e)+')'
                phase=sample.name
               
                
                if incidence not in incidence_sample.data:
                    incidence_sample.data[incidence]={'e':[],'g':[],'slope':[]}
                    incidence_sample.spectrum_labels.append(incidence)
                if emission not in emission_sample.data:
                    emission_sample.data[emission]={'i':[],'slope':[]}
                    emission_sample.spectrum_labels.append(emission)


                
                incidence_sample.data[incidence]['e'].append(e)
                incidence_sample.data[incidence]['g'].append(g)
                incidence_sample.data[incidence]['slope'].append(slope)
                emission_sample.data[emission]['i'].append(i)
                emission_sample.data[emission]['slope'].append(slope)
                
                self.contour_sample.data['all samples']['e'].append(e)
                self.contour_sample.data['all samples']['i'].append(i)
                self.contour_sample.data['all samples']['slope'].append(slope)

                
                slopes.append(label+': '+str(slope))
            self.emission_samples.append(emission_sample)
            self.incidence_samples.append(incidence_sample)
        self.plot.draw_vertical_lines([left, right])

        return left, right, slopes, artifact_warning
    def validate_left_right(self, left, right):
        try:
            left=float(left)
        except:
            
            for sample in self.samples:
                for i, label in enumerate(sample.spectrum_labels): 
                    
                    wavelengths=np.array(sample.data[label]['wavelength'])
                    if i==0:
                        left=np.min(wavelengths)
                    else:
                        left=np.min([left, np.min(wavelengths)])
        try:
            right=float(right)
        except:
            
            for sample in self.samples:
                for i, label in enumerate(sample.spectrum_labels): 
                    
                    wavelengths=np.array(sample.data[label]['wavelength'])
                    if i==0:
                        right=np.max(wavelengths)
                    else:
                        right=np.max([right, np.max(wavelengths)])

        return left, right
    def calculate_error(self, left, right):
        print('calc!')
        left, right=self.validate_left_right(left, right)
        
                        
        avgs=[]
        self.error_samples=[]
        error_sample_names=[]
        artifact_warning=False
        
        self.contour_sample=Sample('all samples','file','title')
        self.contour_sample.data={'all samples':{'i':[],'e':[],'difference':[]}}
        self.contour_sample.spectrum_labels=['all samples']

        
        
        for i, sample in enumerate(self.samples):
            if i==0:
                self.base_sample=sample#Sample(sample.name,sample.file,sample.title)
                continue

            else:
                error_sample=Sample(sample.name,sample.file,sample.title)
                self.error_samples.append(error_sample)


            for label in sample.spectrum_labels: 
                wavelengths=np.array(sample.data[label]['wavelength'])
                reflectance=np.array(sample.data[label]['reflectance'])
                e,i,g=self.plotter.get_e_i_g(label)
                index_left=self.get_index(wavelengths, left)
                index_right=self.get_index(wavelengths, right)
                found=False
                for existing_label in self.base_sample.spectrum_labels:
                    e_old,i_old,g_old=self.plotter.get_e_i_g(existing_label)
                    if e==e_old and i==i_old:
                        error_sample.data[label]={}
                        error_sample.data[label]['difference']=reflectance-self.base_sample.data[existing_label]['reflectance']
                        error_sample.data[label]['wavelength']=wavelengths
                        error_sample.spectrum_labels.append(label)
                        
                        self.contour_sample.data['all samples']['e'].append(e)
                        self.contour_sample.data['all samples']['i'].append(i)
                        if index_left!=index_right:
                            difference=reflectance-self.base_sample.data[existing_label]['reflectance'][index_left:index_right]
                            self.contour_sample.data['all samples']['difference'].append(np.mean(difference))
                        else:
                            difference=reflectance-self.base_sample.data[existing_label]['reflectance'][index_left]
                            self.contour_sample.data['all samples']['difference'].append(difference)
                        
                        found=True
                        break
                if found==False:
                    print('NO MATCH!!')
                    error_sample.data[label]={}
                    error_sample.data[label]['difference']=reflectance
                    error_sample.data[label]['wavelength']=wavelengths
                    error_sample.spectrum_labels.append(label)
                    
                    self.contour_sample.data['all samples']['e'].append(e)
                    self.contour_sample.data['all samples']['i'].append(i)
                    self.contour_sample.data['all samples']['difference'].append(np.mean(reflectance))
                    
                
                if self.exclude_artifacts: #If we are excluding artifacts, don't calculate slopes for anything in the range that is considered to be suspect
                    if self.plotter.artifact_danger(g, left, right):
                        artifact_warning=True #We'll return this to the controller, which will throw up a dialog warning the user that we are skipping some spectra.
                        continue


        avg_errs=[]
        for sample in self.error_samples:
            for label in sample.spectrum_labels:
                wavelengths=np.array(sample.data[label]['wavelength'])
                reflectance=np.array(sample.data[label]['difference'])
                index_left=self.get_index(wavelengths, left)
                index_right=self.get_index(wavelengths, right)
                if index_right!=index_left:
                    avg=np.mean(sample.data[label]['difference'][index_left:index_right])
                else:
                    avg=sample.data[label]['difference'][index_right]
                avg_errs.append(label+': '+str(avg))
            
        self.plot.draw_vertical_lines([left, right])

        return left, right, avg_errs, artifact_warning
        
    def calculate_reciprocity(self, left, right):
        left, right=self.validate_left_right(left, right)
        avgs=[]
        self.recip_samples=[]
        artifact_warning=False
        
        self.contour_sample=Sample('all samples','file','title')
        self.contour_sample.data={'all samples':{'i':[],'e':[],'delta R':[]}}
        self.contour_sample.spectrum_labels=['all samples']
        
        for i, sample in enumerate(self.samples):
            recip_sample=Sample(sample.name,sample.file,sample.title)
            for label in sample.spectrum_labels: 
                e,i,g=self.plotter.get_e_i_g(label)
                
                if self.exclude_artifacts: #If we are excluding artifacts, don't calculate slopes for anything in the range that is considered to be suspect
                    if self.plotter.artifact_danger(g, left, right):
                        artifact_warning=True #We'll return this to the controller, which will throw up a dialog warning the user that we are skipping some spectra.
                        continue

                wavelengths=np.array(sample.data[label]['wavelength'])
                reflectance=np.array(sample.data[label]['reflectance'])

                index_left=self.get_index(wavelengths, left)
                index_right=self.get_index(wavelengths, right)
                if index_right!=index_left:
                    avg=np.mean(reflectance[index_left:index_right])
                else:
                    avg=reflectance[index_left]

                recip_label=sample.name+' (i='+str(-1*e)+' e='+str(-1*i)+')'
                
                if label not in recip_sample.data and recip_label not in recip_sample.data:
                    recip_sample.data[label]={'e':[],'g':[],'i':[],'average reflectance':[]}
                    recip_sample.spectrum_labels.append(label)
                    
                if label in recip_sample.data:
                    recip_sample.data[label]['e'].append(e)
                    recip_sample.data[label]['i'].append(i)
                    recip_sample.data[label]['g'].append(g)
                    recip_sample.data[label]['average reflectance'].append(avg)
                    
                    if len(recip_sample.data[label]['average reflectance'])>1:
                        print('never get here')
                        self.contour_sample.data['all samples']['e'].append(e)
                        self.contour_sample.data['all samples']['i'].append(i)
                        diff=np.abs(recip_sample.data[label]['average reflectance'][0]-avg)
                        self.contour_sample.data['all samples']['delta R'].append(diff)
                    
                elif recip_label in recip_sample.data:
                    recip_sample.data[recip_label]['e'].append(e)
                    recip_sample.data[recip_label]['i'].append(i)
                    recip_sample.data[recip_label]['g'].append(g)
                    recip_sample.data[recip_label]['average reflectance'].append(avg)
                    print(recip_sample.data[recip_label]['average reflectance'])
                    
                    if len(recip_sample.data[recip_label]['average reflectance'])>1:
                        print('But I think we get here?')
                        
                        self.contour_sample.data['all samples']['e'].append(e)
                        self.contour_sample.data['all samples']['i'].append(i)
                        diff=np.abs(recip_sample.data[recip_label]['average reflectance'][0]-avg)
                        self.contour_sample.data['all samples']['delta R'].append(diff)
                        
                avgs.append(label+': '+str(avg))
            self.recip_samples.append(recip_sample)
            print('contour sample data points')
            print(self.contour_sample.data['all samples']['delta R'])
            print(self.contour_sample.data['all samples']['i'])
            print(self.contour_sample.data['all samples']['e'])
            
            
        self.plot.draw_vertical_lines([left, right])

        return left, right, avgs, artifact_warning
    def plot_error(self, x_axis):
        if x_axis=='e,i': 
            x_axis='contour'
            tab=Tab(self.plotter, u'\u0394'+'R compared to '+self.base_sample.name,[self.contour_sample], x_axis='contour',y_axis='difference')  
        else:
            tab=Tab(self.plotter, u'\u0394'+'R compared to '+self.base_sample.name,self.error_samples, x_axis='wavelength',y_axis='difference')  
        return tab 
    def plot_reciprocity(self, x_axis):
        if x_axis=='e,i': 
            x_axis='contour'
            tab=Tab(self.plotter, 'Reciprocity',[self.contour_sample], x_axis=x_axis,y_axis='delta R')
        else:
            for sample in self.recip_samples:
                for label in sample.spectrum_labels:
                    print(sample.data[label]['average reflectance'])
            tab=Tab(self.plotter, 'Reciprocity',self.recip_samples, x_axis=x_axis,y_axis='average reflectance')
        return tab

    def plot_avg_reflectance(self, x_axis):
        if x_axis=='e':
            tab=Tab(self.plotter, 'Reflectance vs '+x_axis,self.incidence_samples, x_axis=x_axis,y_axis='average reflectance')
        elif x_axis=='i':
            tab=Tab(self.plotter, 'Reflectance vs '+x_axis,self.emission_samples, x_axis=x_axis,y_axis='average reflectance')
        elif x_axis=='g':
            tab=Tab(self.plotter, 'Reflectance vs '+x_axis,self.incidence_samples, x_axis=x_axis,y_axis='average reflectance') 
        elif x_axis=='e,i':
            tab=Tab(self.plotter, 'Reflectance',[self.contour_sample], x_axis='contour',y_axis='average reflectance') 
    def plot_band_centers(self, x_axis):
        if x_axis=='e':
            tab=Tab(self.plotter, 'Band center vs '+x_axis,self.incidence_samples, x_axis=x_axis,y_axis='band center')
        elif x_axis=='i':
            tab=Tab(self.plotter, 'Band center vs '+x_axis,self.emission_samples, x_axis=x_axis,y_axis='band center')
        elif x_axis=='g':
            tab=Tab(self.plotter, 'Band center vs '+x_axis,self.incidence_samples, x_axis=x_axis,y_axis='band center') 
        elif x_axis=='e,i':
            tab=Tab(self.plotter, 'Band center',[self.contour_sample], x_axis='contour',y_axis='band center') 
    def plot_band_depths(self, x_axis):
        if x_axis=='e':
            tab=Tab(self.plotter, 'Band depth vs '+x_axis,self.incidence_samples, x_axis=x_axis,y_axis='band depth')
        elif x_axis=='i':
            tab=Tab(self.plotter, 'Band depth vs '+x_axis,self.emission_samples, x_axis=x_axis,y_axis='band depth')
        elif x_axis=='g':
            tab=Tab(self.plotter, 'Band depth vs '+x_axis,self.incidence_samples, x_axis=x_axis,y_axis='band depth')  
        elif x_axis=='e,i':
            tab=Tab(self.plotter, 'Band depth',[self.contour_sample], x_axis='contour',y_axis='band depth') 
            
    def plot_slopes(self, x_axis):
        if x_axis=='e,i':
            tab=Tab(self.plotter, 'Slope',[self.contour_sample], x_axis='contour',y_axis='slope')
        elif x_axis=='e':
            tab=Tab(self.plotter, 'Slope vs '+x_axis,self.incidence_samples, x_axis=x_axis,y_axis='slope')
        elif x_axis=='i':
            tab=Tab(self.plotter, 'Slope vs '+x_axis,self.emission_samples, x_axis=x_axis,y_axis='slope')
        elif x_axis=='g':
            tab=Tab(self.plotter, 'Slope vs '+x_axis,self.incidence_samples, x_axis=x_axis,y_axis='slope')
        elif x_axis=='i,e':
            tab=Tab(self.plotter, 'Slope',[self.contour_sample], x_axis='contour',y_axis='slope')
        
    def calculate_photometric_variability(self, left, right):
        left=float(left)
        right=float(right)
        photo_var=[]

        for i, sample in enumerate(self.samples):
            min_slope=None
            max_slope=None
            for i, label in enumerate(sample.spectrum_labels): 

                wavelengths=np.array(sample.data[label]['wavelength'])
                reflectance=np.array(sample.data[label]['reflectance'])
                index_left = (np.abs(wavelengths - left)).argmin() #find index of wavelength 
                index_right = (np.abs(wavelengths - right)).argmin() #find index of wavelength 
                slope=(reflectance[index_right]-reflectance[index_left])/(index_right-index_left)
                if i==0:
                    min_slope=slope
                    min_slope_label=label.split('(')[1].strip(')')+' ('+str(slope)+')'
                    max_slope=slope
                    max_slope_label=label.split('(')[1].strip(')')+' ('+str(slope)+')'
                else:
                    if slope<min_slope:
                        min_slope=slope
                        min_slope_label=label.split('(')[1].strip(')')+' ('+str(slope)+')'
                    if slope>max_slope:
                        max_slope=slope
                        max_slope_label=label.split('(')[1].strip(')')+' ('+str(slope)+')'

            var=max_slope-min_slope
            photo_var.append(sample.name+': '+str(var))
            photo_var.append('  min: '+min_slope_label)
            photo_var.append('  max: '+max_slope_label)
        
        self.plot.draw_vertical_lines([left, right])

        return photo_var
        
        
    def normalize(self, wavelength):
        wavelength=float(wavelength)

            
        normalized_samples=[]
        for i, sample in enumerate(self.samples):
            

            normalized_sample=Sample(sample.name, sample.file, sample.title) #Note that we aren't editing the original samples list, we're making entirely new objects. This way we can reset later.
            multiplier=None
            for label in sample.spectrum_labels: 
                wavelengths=np.array(sample.data[label]['wavelength'])
                reflectance=np.array(sample.data[label]['reflectance'])
                index = (np.abs(wavelengths - wavelength)).argmin() #find index of wavelength closest to wavelength we want to normalize to

                multiplier=1/reflectance[index] #Normalize to 1
                
                reflectance=reflectance*multiplier
                reflectance=list(reflectance)
                normalized_sample.add_spectrum(label, reflectance,sample.data[label]['wavelength'])
            normalized_samples.append(normalized_sample)
        self.samples=normalized_samples

        self.refresh(original=self.original_samples,xlim=self.xlim) #Let the tab know this data has been modified and we want to hold on to a separate set of original samples. If we're zoomed in, save the xlim but not the ylim (since y scale will be changing)
        
    def reset(self):
        self.samples=self.original_samples
        self.exclude_artifacts=False
        self.refresh()
        
    def close_right_click_menu(self, event):
        self.popup_menu.unpost()
        
    def open_analysis_tools(self):
        #Build up lists of strings telling available samples, which of those samples a currently plotted, and a dictionary mapping those strings to the sample options.
        self.build_sample_lists()
        self.plotter.controller.open_analysis_tools(self)
        #self.plotter.controller.open_data_analysis_tools(self,self.existing_indices,self.sample_options_list)
        
        
    def build_sample_lists(self):
        #Sample options will be the list of strings to put in the listbox. It may include the sample title, depending on whether there is more than one title.
        self.sample_options_dict={}
        self.sample_options_list=[]
        self.existing_indices=[]
        
        #Each file got a title assigned to it when loaded, so each group of samples from a file will have a title associated with them. 
        #If there are multiple possible titles, list that in the listbox along with the sample name.
        if len(self.plotter.titles)>1:
            for i, sample in enumerate(self.plotter.sample_objects):
                for plotted_sample in self.samples:
                    if sample.name==plotted_sample.name and sample.file==plotted_sample.file:
                        self.existing_indices.append(i)
                self.sample_options_dict[sample.title+': '+sample.name]=sample
                self.sample_options_list.append(sample.title+': '+sample.name)
        #Otherwise, the user knows what the title is (there is only one)
        else:
            for i, sample in enumerate(self.plotter.sample_objects):
                for plotted_sample in self.samples:
                    if sample.name==plotted_sample.name and sample.file==plotted_sample.file:
                        self.existing_indices.append(i)
                self.sample_options_dict[sample.name]=sample
                self.sample_options_list.append(sample.name)
        
        return self.sample_options_list
    
    #We want to pass a list of existing samples and a list of possible samples.
    def ask_which_samples(self):
        
        #Build up lists of strings telling available samples, which of those samples a currently plotted, and a dictionary mapping those strings to the sample options.
        self.build_sample_lists()
        #We tell the controller which samples are already plotted so it can initiate the listbox with those samples highlighted.
        self.plotter.controller.ask_plot_samples(self,self.existing_indices, self.sample_options_list, self.geoms, self.title)#existing_samples, new_samples)
    
    def set_samples(self, listbox_labels, title, incidences, emissions, exclude_specular=False, tolerance=None):
        #we made a dict mapping sample labels for a listbox to available samples to plot. This was passed back when the user clicked ok. Reset this tab's samples to be those ones, then replot.
        self.samples=[]
        if title=='':
            title=', '.join(listbox_labels)
        for label in listbox_labels:
            self.samples.append(self.sample_options_dict[label])
            
        incidences=incidences.split(',')
        for i in incidences:
            i=i.replace(' ','')
        if incidences==['']: 
            incidences=[]
    
        
        emissions=emissions.split(',')
        for e in emissions:
            e=e.replace(' ','')
        if emissions==['']: 
            emissions=[]
            
        self.geoms={'i':incidences,'e':emissions}
        self.exclude_specular=exclude_specular
        if self.exclude_specular:
            try:
                self.specularity_tolerance=int(tolerance)
            except:
                self.specularity_tolerance=0
        winnowed_samples=[] #These will only have the data we are actually going to plot, which will only be from the specificied geometries. 
        
        for i, sample in enumerate(self.samples):

            
            winnowed_sample=Sample(sample.name, sample.file, sample.title)
            
            for label in sample.spectrum_labels: #For every spectrum associated with the sample, check if it is for a geometry we are going to plot. if it is, attach that spectrum to the winnowed sample data
                try: #If there is no geometry information for this sample, this will throw an exception.
                    i=label.split('i=')[1].split(' ')[0]
                    e=label.split('e=')[1].strip(')')
                    if self.check_geom(i, e, exclude_specular, self.specularity_tolerance): #If this is a geometry we are supposed to plot
                        winnowed_sample.add_spectrum(label, sample.data[label]['reflectance'], sample.data[label]['wavelength'])
                except: #If there's no geometry information, plot the sample.
                    print('plotting spectrum with invalid geometry information')
                    winnowed_sample.add_spectrum(label,sample.data[label]['reflectance'],sample.data[label]['wavelength'])

                
                    
            winnowed_samples.append(winnowed_sample)

        self.samples=winnowed_samples
        self.title=title
        self.refresh()

    def refresh(self,original=None,xlim=None,ylim=None): #Gets called when data is updated, either from edit plot or analysis tools. We set original = False if calling from normalize, that way we will still hold on to the unchanged data.
        tab_index=self.plotter.notebook.index(self.plotter.notebook.select())
        self.plotter.notebook.forget(self.plotter.notebook.select())
        self.__init__(self.plotter,self.title,self.samples, tab_index=tab_index,title_override=True, geoms=self.geoms,original=original,xlim=xlim,ylim=ylim,exclude_artifacts=self.exclude_artifacts, exclude_specular=self.exclude_specular, specularity_tolerance=self.specularity_tolerance)
        

    def open_right_click_menu(self, event):
        self.popup_menu.post(event.x_root+10, event.y_root+1)
        self.popup_menu.grab_release()
    
    def close(self):
        tabid=self.plotter.notebook.select()
        self.plotter.notebook.forget(tabid)

    def check_geom(self, i, e, exclude_specular=False, tolerance=None):
        if exclude_specular:
            if np.abs(int(i)-(-1*int(e)))<=tolerance:
                return False
        if i in self.geoms['i'] and e in self.geoms['e']: return True
        elif i in self.geoms['i'] and self.geoms['e']==[]: return True
        elif self.geoms['i']==[] and e in self.geoms['e']: return True
        elif self.geoms['i']==[] and self.geoms['e']==[]: return True
        else: return False
        
    def adjust_x(self, left, right):
        left=float(left)
        right=float(right)
        self.xlim=[left,right]
        self.plot.adjust_x(left,right)
        
    
    def adjust_y(self, bottom, top):
        bottom=float(bottom)
        top=float(top)
        self.ylim=[bottom,top]
        self.plot.adjust_y(bottom,top)
        
    
        
class Plot():
    def __init__(self, plotter, fig, samples,title, oversize_legend=False,plot_scale=18,plot_width=215,x_axis='wavelength',y_axis='reflectance',xlim=None, ylim=None, exclude_artifacts=False):
        
        self.plotter=plotter
        self.samples=samples
        self.fig=fig
        self.title='' #This will be the text to put on the notebook tab
        #self.geoms={'i':[],'e':[]} #This is a dict like this: {'i':[10,20],'e':[-10,0,10,20,30,40,50]} telling which incidence and emission angles to include on the plot. empty lists mean plot all available.


        self.x_axis=x_axis
        self.y_axis=y_axis
        self.ylim=None #About to set based on either data limits or zoom if specified
        self.xlim=None #same as ylim
        self.exclude_artifacts=exclude_artifacts
        #If y limits for plot not specified, make the plot wide enough to display min and max values for all samples.
        if ylim==None and xlim==None:
            for i, sample in enumerate(self.samples):
                for j, label in enumerate(sample.spectrum_labels):
                    if self.y_axis not in sample.data[label] or self.x_axis not in sample.data[label]: continue
                    if i==0 and j==0:
                        self.ylim=[np.min(sample.data[label][self.y_axis]),np.max(sample.data[label][self.y_axis])]
                    else:

                        sample_min=np.min(sample.data[label][self.y_axis])
                        sample_max=np.max(sample.data[label][self.y_axis])
                        self.ylim[0]=np.min([self.ylim[0],sample_min])
                        self.ylim[1]=np.max([self.ylim[1],sample_max])
        
            #add a little margin around edges
            if self.ylim==None: self.ylim=[0,1] #Happens if you are making a new tab with no data
            delta_y=self.ylim[1]-self.ylim[0]
            self.ylim[0]=self.ylim[0]-delta_y*.02
            self.ylim[1]=self.ylim[1]+delta_y*.02 

        elif ylim==None:
            for i, sample in enumerate(self.samples):
                for j, label in enumerate(sample.spectrum_labels):
                    if self.y_axis not in sample.data[label] or self.x_axis not in sample.data[label]: continue
                    
                    index_left = (np.abs(np.array(sample.data[label][self.x_axis]) - xlim[0])).argmin() #find index of min x 
                    index_right = (np.abs(np.array(sample.data[label][self.x_axis]) - xlim[1])).argmin() #find index of max x
                    if i==0 and j==0:
                        self.ylim=[np.min(sample.data[label][self.y_axis][index_left:index_right]),np.max(sample.data[label][self.y_axis][index_left:index_right])]
                    else:
                        sample_min=np.min(sample.data[label][self.y_axis][index_left:index_right]) #find min value between min and max x
                        sample_max=np.max(sample.data[label][self.y_axis][index_left:index_right]) #find max value between min and max x
                        self.ylim[0]=np.min([self.ylim[0],sample_min])
                        self.ylim[1]=np.max([self.ylim[1],sample_max])
                            
            #add a little margin around edges
            if self.ylim==None: self.ylim=[0,1] #Happens if you are making a new tab with no data
            delta_y=self.ylim[1]-self.ylim[0]
            self.ylim[0]=self.ylim[0]-delta_y*.02
            self.ylim[1]=self.ylim[1]+delta_y*.02 

        else: #specified if this is a zoomed in plot
            self.ylim=ylim
        
        #If x limits for plot not specified, make the plot wide enough to display min and max values for all samples.
        if xlim==None:

            for i, sample in enumerate(self.samples):
                for j, label in enumerate(sample.spectrum_labels):
                    if self.y_axis not in sample.data[label] or self.x_axis not in sample.data[label]: continue
                    
                    if i==0 and j==0:
                        sample_min=np.min(sample.data[label][self.x_axis][0:10])
                        sample_min=np.min(sample.data[label][self.x_axis])
                        sample_max=np.max(sample.data[label][self.x_axis])
                        self.xlim=[sample_min,sample_max]
                    else:
                        sample_min=np.min(sample.data[label][self.x_axis])
                        sample_max=np.max(sample.data[label][self.x_axis])
                        self.xlim[0]=np.min([self.xlim[0],sample_min])
                        self.xlim[1]=np.max([self.xlim[1],sample_max])
            
            if self.xlim==None: self.xlim=[400,2400] #Happens if you are making a new tab with no data
            delta_x=self.xlim[1]-self.xlim[0]
            
            if self.x_axis!='wavelength': #add a little margin around edges
                self.xlim[0]=self.xlim[0]-delta_x*.02
                self.xlim[1]=self.xlim[1]+delta_x*.02 
                
        else: #This will be specified if this is a zoomed in plot

            self.xlim=xlim
            


        
        #we'll use these to generate hsv lists of colors for each sample, which will be evenly distributed across a gradient to make it easy to see what the overall trend of reflectance is.
        self.hues=[200,12,130,290,170,37,330]
        self.oversize_legend=oversize_legend
        self.plot_scale=plot_scale
        self.annotations=[] #These will be vertical lines drawn to help with analysis to show where slopes are being calculated, etc
        
        
        self.files=[]
        self.num_spectra=0 #This is the total number of spectra we're plotting. We want to get a count so we know where to put the legend (on top or to the right).
        for i, sample in enumerate(self.samples):
            if sample.file not in self.files:
                self.files.append(sample.file)
            sample.set_colors(self.hues[i%len(self.hues)])
            self.num_spectra+=len(sample.spectrum_labels)

        self.title=title
        
        self.max_legend_label_len=0 #This will tell us how much horizontal space to give the legend
        self.legend_len=0
        #The whole point in this is to figure out how much space the legend might need. We do the whole thing again in a moment, which dumb.
        for sample in self.samples:
            for label in sample.spectrum_labels:

                legend_label=label
                if self.x_axis=='wavelength' and self.y_axis=='reflectance':
                    if len(self.samples)==1: #No need to specify which sample if you are only plotting one.
                        legend_label=legend_label.replace(sample.name,'').replace('(i=','i=').strip('(')
                    # if len(self.files)>1:
                    #     legend_label=sample.title+': '+legend_label
                        
                if len(legend_label)>self.max_legend_label_len:
                    self.max_legend_label_len=len(legend_label)
                self.legend_len+=1
                    
      
        plot_width=plot_width*0.85
        if self.max_legend_label_len==0:
            ratio=1000
            self.legend_anchor=1.05
        else:
            ratio=int(plot_width/self.max_legend_label_len)+0.1
            self.legend_anchor=1.12+1.0/ratio*1.3

        gs = mpl.gridspec.GridSpec(1, 2, width_ratios=[ratio, 1]) 
        self.plot = fig.add_subplot(gs[0])
        pos1 = self.plot.get_position() # get the original position 

        
        y0=pos1.y0
        height=pos1.height
        if self.oversize_legend:
            height=pos1.height*self.plot_scale/self.legend_len
            y0=1-self.plot_scale/self.legend_len+pos1.y0*self.plot_scale/(self.legend_len)*0.5


        pos2 = [pos1.x0+.02, y0,  pos1.width, height] 

        self.plot.set_position(pos2) # set a new position, slightly adjusted so it doesn't go off the edges of the screen.
        

        
        self.draw()
        
        def on_closing():
            # for i in self.plots:
            #     del self.plots[i]
            # #del self.plots[i]
            top.destroy()
    

        
    def save(self):
        initialdir=self.plotter.save_dir
    
        if initialdir==None:
            if len(self.files)>0:
                if '\\' in self.files[0]:
                    initialdir='\\'.join(self.files[0].split('\\')[0:-1])
                    
                elif '/' in self.files[0]:
                    initialdir='/'.join(self.files[0].split('/')[0:-1])
                
        path=None
        if initialdir!=None:
            path=filedialog.asksaveasfilename(initialdir=initialdir)
        else:
            path=asksaveasfilename()
            
        self.plotter.save_dir=path
        if '\\' in path:
            self.plotter.save_dir='\\'.join(path.split('\\')[0:-1])
        elif '/' in path:
            self.plotter.save_dir='/'.join(path.split('/')[0:-1])
        self.fig.savefig(path)
        
    def set_title(self,title):
        self.title=title
        self.plot.set_title(title,fontsize=24)
        self.fig.canvas.draw()
        
    def draw_vertical_lines(self, xcoords):
        for _ in range(len(self.annotations)):
            try:
                self.annotations.pop(0).remove()
            except:
                print('Error! Annotation was erased somewhere it was not supposed to be!')
                pass #Shouldn't ever come up, but would happen if we already erased an annotation elsewhere.
        for x in xcoords:
            self.annotations.append(self.plot.axvline(x=x,color='lightgray',linewidth=1))
        self.fig.canvas.draw()
    
    def adjust_x(self, left, right):
        self.plot.set_xlim(left, right)
        print('ADJUST')
        print(left)
        print(right)
        self.xlim=[left,right]
        self.set_x_ticks()
        self.fig.canvas.draw()
        
        
        
    def adjust_y(self, bottom, top):
        self.plot.set_ylim(bottom, top)
        self.ylim=[bottom,top]
        self.set_y_ticks()
        self.fig.canvas.draw()
        
    def set_x_ticks(self):
        
        order=-3.0
        delta_x=(self.xlim[1]-self.xlim[0])
        
        # Decide where to place tick marks.
        while np.power(10,order)-delta_x<0:
            order+=1
        
        if delta_x/np.power(10,order)>0.5:
            order=order-1
        else:
            order=order-2

        order=int(order*-1)

        interval=np.round(delta_x/5,order)

        interval_2=np.round(interval/5,order)
        order2=order
        while interval_2==0:
            order2+=1
            interval_2=np.round(interval/5,order2)
        if np.round(self.xlim[0],order)<=self.xlim[0]:



            major_ticks = np.arange(np.round(self.xlim[0],order),self.xlim[1]+.01**float(-1*order), interval)
            minor_ticks = np.arange(np.round(self.xlim[0],order),self.xlim[1]+.01**float(-1*order), interval_2)
        else:

            major_ticks = np.arange(np.round(self.xlim[0],order)-10**float(-1*order),self.xlim[1]+.01**float(-1*order), interval)
            minor_ticks = np.arange(np.round(self.xlim[0],order)-10**float(-1*order),self.xlim[1]+.01**float(-1*order), interval_2)

        
        
        self.plot.set_xticks(major_ticks)
        self.plot.set_xticks(minor_ticks, minor=True)
        
    def set_y_ticks(self):
        order=-10.0
        delta_y=(self.ylim[1]-self.ylim[0])
        
        # Decide where to place tick marks.
        while np.power(10,order)-delta_y<0:
            order+=1
        
        if delta_y/np.power(10,order)>0.5:
            order=order-1
        else:
            order=order-2

        order=int(order*-1)
        interval=np.round(delta_y/5,order)
        while interval==0: #I don't think this ever happens.
            order+=1
            interval=np.round(delta_y/5,order)
        y_ticks = np.arange(self.ylim[0],self.ylim[1]+.01, interval)

        self.plot.grid(which='minor', alpha=0.1)
        self.plot.grid(which='major', alpha=0.1)
        
    def draw(self, exclude_wr=True):#self, title, sample=None, exclude_wr=True):
        self.lines=[]
        
        if self.x_axis=='contour':
            # self.plot.tricontour(self.samples[0].data['all samples']['e'], self.samples[0].data['all samples']['i'], self.samples[0].data['all samples'][self.y_axis], levels=14, linewidths=0.5, colors='k')
            x=self.samples[0].data['all samples']['e']
            y=self.samples[0].data['all samples']['i']
            z=self.samples[0].data['all samples'][self.y_axis]

            triang = mtri.Triangulation(x, y)
            cntr2=self.plot.tricontourf(triang, z)
            self.adjust_x(np.min(x),np.max(x))
            self.adjust_y(np.min(y),np.max(y))
        
            self.fig.colorbar(cntr2, ax=self.plot)
        
        repeats=False #Find if there are samples with the exact same name. If so, put the title in the legend as well as the name.
        names=[]
        for sample in self.samples:
            for label in sample.spectrum_labels:
                if self.y_axis not in sample.data[label] or self.x_axis not in sample.data[label]: continue
            if sample.name in names:
                repeats=True
            else:
                names.append(sample.name)
                
                
        for sample in self.samples:
            for label in sample.spectrum_labels:
                if self.y_axis not in sample.data[label] or self.x_axis not in sample.data[label]: continue
                
                legend_label=label
                if repeats:
                    legend_label=sample.title+': '+legend_label
                elif len(self.samples)==1:
                    legend_label=legend_label.replace(sample.name,'').replace('(i=','i=').replace(')','')

                color=sample.next_color()
                if (self.y_axis=='reflectance' or self.y_axis=='difference') and self.x_axis=='wavelength':
                    wavelengths=sample.data[label][self.x_axis]
                    reflectance=sample.data[label][self.y_axis]
                    if self.exclude_artifacts: #If we are excluding data from the suspect region from 1050 to 1450 nm, divide each spectrum into 3 segments. One on either side of that bad region, and then one straight dashed line through the bad region. All the same color. Only attach a legend label to the first one so the legend only gets drawn once.
                        e,i,g=self.plotter.get_e_i_g(label)
                        if self.plotter.artifact_danger(g):
                            artifact_index_left=self.plotter.get_index(np.array(wavelengths), MIN_WAVELENGTH_ARTIFACT_FREE)
                            artifact_index_right=self.plotter.get_index(np.array(wavelengths), MAX_WAVELENGTH_ARTIFACT_FREE)
                            w_1, r_1=wavelengths[0:artifact_index_left], reflectance[0:artifact_index_left]
                            w_2=[wavelengths[artifact_index_left],wavelengths[artifact_index_right]]
                            r_2= [reflectance[artifact_index_left],reflectance[artifact_index_right]]
                            w_3,r_3=wavelengths[artifact_index_right:-1], reflectance[artifact_index_right:-1]
                            self.lines.append(self.plot.plot(w_1,r_1, label=legend_label,color=color,linewidth=2))
                            self.lines.append(self.plot.plot(w_2,r_2,'--',color=color,linewidth=2))
                            self.lines.append(self.plot.plot(w_3,r_3, color=color, linewidth=2))
                        else:
                            self.lines.append(self.plot.plot(wavelengths,reflectance, label=legend_label,color=color,linewidth=2))
                    else:
                        self.lines.append(self.plot.plot(wavelengths,reflectance, label=legend_label,color=color,linewidth=2))
                elif self.x_axis=='g':

                    self.lines.append(self.plot.plot(sample.data[label][self.x_axis], sample.data[label][self.y_axis], 'o',label=legend_label,color=color, markersize=6))
                else:

                                        
                    self.lines.append(self.plot.plot(sample.data[label][self.x_axis], sample.data[label][self.y_axis], '-o',label=legend_label,color=color, markersize=5))
                
        self.plot.set_title(self.title, fontsize=24)
        
        if self.x_axis=='contour':
            self.plot.set_xlabel('Emission (degrees)',fontsize=18)
            self.plot.set_ylabel('Incidence (degrees)',fontsize=18)
        elif self.y_axis=='reflectance':
            self.plot.set_ylabel('Reflectance',fontsize=18)
        elif self.y_axis=='difference':
            self.plot.set_ylabel('$\Delta$R',fontsize=18)
        elif self.y_axis=='slope':
            self.plot.set_ylabel('Slope',fontsize=18)
        if self.x_axis=='wavelength':
            self.plot.set_xlabel('Wavelength (nm)',fontsize=18)
        elif self.x_axis=='i':
            self.plot.set_xlabel('Incidence (degrees)',fontsize=18)
        elif self.x_axis=='e':
            self.plot.set_xlabel('Emission (degrees)',fontsize=18)
        elif self.x_axis=='g':
            self.plot.set_xlabel('Phase angle (degrees)',fontsize=18)
        
        self.plot.tick_params(labelsize=14)

        if self.x_axis!='contour': #If it is a contour map, we put in the colorbar already above.
            self.plot.legend(bbox_to_anchor=(self.legend_anchor, 1), loc=1, borderaxespad=0.)
        
        
        self.plot.set_xlim(*self.xlim)
        self.plot.set_ylim(*self.ylim)
        self.set_x_ticks()
        self.set_y_ticks()


class NotScrolledFrame(Frame):
    def __init__(self, parent, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)  
        self.interior=self
        self.scrollbar=NotScrollbar()
        
class NotScrollbar():
    def __init__(self):
        pass
    def pack_forget(self):
        pass
        
            
            

        
            
        
        