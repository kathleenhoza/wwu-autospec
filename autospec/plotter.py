#Plotter takes a Tk root object and uses it as a base to spawn Tk Toplevel plot windows.

import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from tkinter import *
from tkinter import filedialog
import colorutils

import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from verticalscrolledframe import VerticalScrolledFrame

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
        
    def notebook_click(self, event):
        self.close_right_click_menus(event)
        self.maybe_close_tab(event)
    
    def update_tab_names(self):
        pass
        
    def new_tab(self):
        tab=Tab(self, 'New tab',[], title_override=True)
        tab.ask_which_samples()
        
    def open_right_click_menu(self,event):
        print('hooray!')
        print(event)
        print(event.x)
        
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
                    
            if spectrum_label not in self.samples[file][sample_label].spectrum_labels: #This should do better and actually check that all the data is an exact duplicate, but that seems hard. Just don't label things exactly the same and save them in the same file with the same viewing geometry.
                self.samples[file][sample_label].add_spectrum(spectrum_label, reflectance[i], wavelengths)



        for sample in self.samples[file]:
            tab=Tab(self, title,[self.samples[file][sample]])

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
        self.data[spectrum_label]={'reflectance':[],'wavelengths':[]}
        self.data[spectrum_label]['reflectance']=reflectance
        self.data[spectrum_label]['wavelengths']=wavelengths
        
    #generate a list of hex colors that are evenly distributed from dark to light across a single hue. 
    def set_colors(self, hue):
        N=len(self.spectrum_labels)/2
        if len(self.spectrum_labels)%2!=0:
            N+=1
        N=int(N)+1
        
        hsv_tuples = [(hue, 1, x*1.0/N) for x in range(2,N)]
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
    def __init__(self, plotter, title, samples,tab_index=None,title_override=False, geoms={'i':[],'e':[]}, scrollable=True):
        self.plotter=plotter
        self.samples=samples
        self.geoms=geoms
        if title_override==False:
            self.title=title+ ': '+samples[0].name
        else:
            self.title=title
        
        width=self.plotter.notebook.winfo_width()
        self.height=self.plotter.notebook.winfo_height()
        
        #If we need a bigger frame to hold a giant long legend, expand.
        self.legend_len=0
        for sample in self.samples:
            self.legend_len+=len(sample.spectrum_labels)
        self.legend_height=self.legend_len*21+100 #23 px per legend entry.
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
        self.fig = mpl.figure.Figure(figsize=(width/self.plotter.dpi, self.height/self.plotter.dpi),dpi=self.plotter.dpi) 
 
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
                print('event height')
                print(event.height)
                print('legend height')
                print(self.legend_height)
                inv=self.legend_height/event.height
                y0=0.41+inv/9.7-.2
                print(self.legend_height/130000)
                y0=y0+self.legend_height/130000
                if y0>0.88:
                    y0=0.88
                print(y0)
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

        
        self.plot=Plot(self.plotter, self.fig, self.samples,self.title, self.oversize_legend)



        self.canvas.draw()
        self.popup_menu = Menu(self.top.interior, tearoff=0)
        self.popup_menu.add_command(label="Edit plot",
                                    command=self.ask_which_samples)
        self.popup_menu.add_command(label="Open analysis tools",
                                    command=self.open_analysis_tools)
        self.popup_menu.add_command(label="Save plot",
                                    command=self.save)

        self.popup_menu.add_command(label="New tab",
                                    command=self.new)
        self.popup_menu.add_command(label="Close tab",
                                    command=self.close)

        self.plotter.menus.append(self.popup_menu)
        
    def save(self):
        self.plot.save()
    
    def new(self):
        self.plotter.new_tab()

    def on_visibility(self, event):
        self.close_right_click_menu(event)
        

    def close_right_click_menu(self, event):
        self.popup_menu.unpost()
        
    def open_analysis_tools(self):
        #Build up lists of strings telling available samples, which of those samples a currently plotted, and a dictionary mapping those strings to the sample options.
        self.build_sample_lists()
        print('Analyze!')
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
    
    def set_samples(self, listbox_labels, title, incidences, emissions):
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
        
        winnowed_samples=[] #These will only have the data we are actually going to plot, which will only be from the specificied geometries. 
        
        for i, sample in enumerate(self.samples):

            
            winnowed_sample=Sample(sample.name, sample.file, sample.title)
            
            for label in sample.spectrum_labels: #For every spectrum associated with the sample, check if it is for a geometry we are going to plot. if it is, attach that spectrum to the winnowed sample data
                try: #If there is no geometry information for this sample, this will throw an exception.
                    i=label.split('i=')[1].split(' ')[0]
                    e=label.split('e=')[1].strip(')')
                    if self.check_geom(i, e): #If this is a geometry we are supposed to plot
                        winnowed_sample.add_spectrum(label, sample.data[label]['reflectance'], sample.data[label]['wavelengths'])
                except: #If there's no geometry information, plot the sample.
                    print('plotting spectrum with invalid geometry information')
                    winnowed_sample.add_spectrum(label,sample.data[label]['reflectance'],sample.data[label]['wavelengths'])

                
                    
            winnowed_samples.append(winnowed_sample)

        
        tab_index=self.plotter.notebook.index(self.plotter.notebook.select())
        self.plotter.notebook.forget(self.plotter.notebook.select())
        self.__init__(self.plotter,title,winnowed_samples, tab_index=tab_index,title_override=True, geoms=self.geoms)

    def open_right_click_menu(self, event):
        self.popup_menu.post(event.x_root+10, event.y_root+1)
        self.popup_menu.grab_release()
        #self.popup_menu.attributes('-topmost', 0)
    
    def close(self):
        tabid=self.plotter.notebook.select()
        self.plotter.notebook.forget(tabid)

    def check_geom(self, i, e):
        if i in self.geoms['i'] and e in self.geoms['e']: return True
        elif i in self.geoms['i'] and self.geoms['e']==[]: return True
        elif self.geoms['i']==[] and e in self.geoms['e']: return True
        elif self.geoms['i']==[] and self.geoms['e']==[]: return True
        else: return False
        
    
        
class Plot():
    def __init__(self, plotter, fig, samples,title, oversize_legend=False):
        
        self.plotter=plotter
        self.samples=samples
        self.fig=fig
        self.title='' #This will be the text to put on the notebook tab
        #self.geoms={'i':[],'e':[]} #This is a dict like this: {'i':[10,20],'e':[-10,0,10,20,30,40,50]} telling which incidence and emission angles to include on the plot. empty lists mean plot all available.

        #we'll use these to generate hsv lists of colors for each sample, which will be evenly distributed across a gradient to make it easy to see what the overall trend of reflectance is.
        self.hues=[200,130,12,280]
        self.oversize_legend=oversize_legend
        
        
        
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
                if len(self.samples)==1:
                    legend_label=legend_label.replace(sample.name,'').replace('(i=','i=').strip('(')

                if len(self.files)>1:
                    legend_label=sample.title+': '+legend_label
                    
                if len(legend_label)>self.max_legend_label_len:
                    self.max_legend_label_len=len(legend_label)
                self.legend_len+=1
                    
        self.legend_anchor=1.05+self.max_legend_label_len/97
        plot_width=215 #very vague character approximation of plot width
        if self.max_legend_label_len==0:
            ratio=1000
        else:
            ratio=int(plot_width/self.max_legend_label_len)
        gs = mpl.gridspec.GridSpec(1, 2, width_ratios=[ratio, 1]) 
        self.plot = fig.add_subplot(gs[0])
        pos1 = self.plot.get_position() # get the original position 
        y0=pos1.y0 +self.legend_len/130

        if self.legend_len<70 and self.oversize_legend:
            height=pos1.height -self.legend_len/150
            if y0>0.8:
                y0=0.8
            print('SMALL')
            #Looks very reasonable all the way through range of small
        elif self.oversize_legend:
            print('BIG')
            print(self.legend_len)
            height=pos1.height-.36-self.legend_len/600 #A little too small at 176, a tiny bit big at 135, good at 76.
            
            #y0=pos1.y0 +self.legend_len/210 #good at 76, too small at 105, too big at 212. Need less dependence on legend len. 
            #y0=pos1.y0 +.2+self.legend_len/500 far too small at 105
            if self.legend_len<150:
                print('YAY!')
                #y0=pos1.y0+self.legend_len/100 #Too high for 140 and 108 and 76
                y0=pos1.y0-.4+self.legend_len/100 #plot is Too high for 140, plot is way too low for 76. Need y0 smaller for 140, y0 greater at 76
                #y0=pos1.y0+.2+self.legend_len/300 #plot is slightly low at 140, and very slightly lower at 76
                #y0=pos1.y0+.23+self.legend_len/300 #plot is perfect at 140, anda little low at 76. Need y0 to be bigger at 76.
                #y0=pos1.y0+.27+self.legend_len/330 #very close! plot is perfect at 140, anda little low at 76. Need y0 to be bigger at 76.
                y0=pos1.y0+.36+self.legend_len/430 #very close! plot is perfect at 140, anda little low at 76. Need y0 to be bigger at 76.
                print(y0)
            else:
                #y0=pos1.y0 +.36+self.legend_len/520 #Good at 212, plot is too low at 156. Need y0 to be bigger for 156
                #y0=pos1.y0 +.5+self.legend_len/800 #perfect at 212, plot slightly too low at 162
                y0=pos1.y0 +.57+self.legend_len/1100
                
                
            if y0>0.9:
                y0=0.9
        else:
            print('NOT OVERSIZE!')
            y0=pos1.y0
            height=pos1.height
        if height<0.1:
            height=0.1
        pos2 = [pos1.x0+0.02, y0,  pos1.width, height] 
        print('pos2!')
        print(pos2)
        self.plot.set_position(pos2) # set a new position, slightly adjusted so it doesn't go off the edges of the screen.
        
        
        #If there is data from more than one data file, associate each sample name with that file. Otherwise, just use the sample name.

        # if len(self.files)>1:
        #     for sample in samples:
        #         for i, label in sample.labels:
        #             if sample.title not in sample.labels[i]:
        #                 sample.extended_labels[i]=sample.title+' '+label
        #                 sample.data[sample.extended_labels[i]]=sample.data[label]
        #                 
        #         sample.labels=sample.title+' '+sample.label
        #         for sample in samples[tsv_title]:
        #             label=tsv_title+' '+sample
        #             self.labels.append(label)
        #             self.data[label]=plotter.data[tsv_title][sample]
        # else:
        #     for tsv_title in samples:
        #         for sample in samples[tsv_title]:
        #             label=sample
        #             self.labels.append(label)
        #             self.data[label]=plotter.data[tsv_title][sample]

        
        self.draw()
        
        def on_closing():
            # for i in self.plots:
            #     del self.plots[i]
            # #del self.plots[i]
            top.destroy()
    

        
    def save(self):
        initialdir=None
        if len(self.files)>0:
            if '\\' in self.files[0]:
                initialdir='\\'.join(self.files[0].split('\\')[0:-1])
            elif '/' in self.files[0]:
                initialdir='/'.join(self.files[0].split('/')[0:-1])
                
        if initialdir!=None:
            path=filedialog.asksaveasfilename(initialdir=initialdir)
            self.fig.savefig(path)
        else:
            path=asksaveasfilename()
            self.fig.savefig(path)
        
    def draw(self, exclude_wr=True):#self, title, sample=None, exclude_wr=True):
        for sample in self.samples:
            lines=[]
            for label in sample.spectrum_labels:

                # if 'White reference' in sample.name and exclude_wr and sample==None:
                #     continue
                legend_label=label
                if len(self.samples)==1:
                    legend_label=legend_label.replace(sample.name,'').replace('(i=','i=').strip(')')

                if len(self.files)>1:
                    legend_label=sample.title+': '+legend_label

                color=sample.next_color()
                lines.append(self.plot.plot(sample.data[label]['wavelengths'], sample.data[label]['reflectance'], label=legend_label,color=color,linewidth=2))
                
            # Create a legend for this sample
            #legend = plt.legend(bbox_to_anchor=(self.legend_anchor, 1),handles=lines[0], loc=1)
            #ax = plt.gca().add_artist(legend)
        # if sample!=None:
        #     if title in self.title_bases:
        #         base=self.title_bases[title]
        #     else:
        #         base=title
        #     plot.set_title(base+' '+sample, fontsize=24)
        # else:
        self.plot.set_title(self.title, fontsize=24)
            
        self.plot.set_ylabel('Relative Reflectance',fontsize=18)
        self.plot.set_xlabel('Wavelength (nm)',fontsize=18)
        self.plot.tick_params(labelsize=14)
        
        self.plot.legend(bbox_to_anchor=(self.legend_anchor, 1), loc=1, borderaxespad=0.)

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
        
            
            

        
            
        
        