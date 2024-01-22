from geoh5py.groups import ContainerGroup
from geoh5py.workspace import Workspace
import pandas as pd
import time
from os import mkdir, path
from geoh5py.shared import Entity
from shutil import move
import numpy as np
from geoh5py.objects import Curve, Surface
import os
from builtins import any as b_any


class updater(object):
    """
    Class to handle the creation and updating of a geoh5 file
    geoh5 file consists of objects generated using data that is ouput by provus modelling software
    """

    def __init__(self):
        """
        User defines the directory that the provus results are stored and the directory that GA is monitoring
        The Dir paths and workspace name are entered via command line
        """
        self.input_directory = (input("path to provus directory: "))
        self.monitoring_directory = (input("path to GA monitoring directory: "))
        self.input_name = (input("project name: ") + ".geoh5")
        self.export_mode = (input("true to export, false to update:  ")) # can be replaced with flag or GUI tkinter implementation
        if self.export_mode == 'true':
            self.export_dir = (input("path to export directory: "))
    def ga_output(self, selected_path, entity: Entity, data: dict = {}):
        """
        Create a temporary geoh5 file in the monitoring folder and export entity for update.
        :param entity: Entity to be updated
        :param data: Data name and values to be added as data to the entity on export {"name": values}
        """
        if self.export_mode == "true":
            geoh5_export = f"temp{time.time():.3f}.geoh5"
            workspace = Workspace(path.join(self.export_dir, geoh5_export))
            for key, value in data.items():
                entity.add_data({key: {"values": value}})
            entity.copy(parent=workspace)

        else:
            working_path = path.join(selected_path, "working_temp")
            if not path.exists(working_path):
                mkdir(working_path)

            temp_geoh5 = f"temp{time.time():.3f}.geoh5"


            temp_workspace = Workspace(path.join(working_path, temp_geoh5))

            for key, value in data.items():
                entity.add_data({key: {"values": value}})

            entity.copy(parent=temp_workspace)


                    # Move the geoh5 to monitoring folder
            #shutil.copyfile(path.join(working_path, temp_geoh5), path.join(selected_path))

            source = os.path.join(working_path, temp_geoh5)
            dest = os.path.join(selected_path, temp_geoh5)

            try:
                move(
                    source,
                    dest
                )
            except PermissionError:
                print('as expected')
                temp_workspace.close()
            try:
                move(
                 source,
                 dest
             )

            except PermissionError:
                print('you will not see this')


    def search_for_file_path(self):
        """
        Opens windows explorer to get the two required directory inputs from user (provus + monitoring directory)
        Not used currently in favor of command line input defined above
        """
        #currdir = os.getcwd()
        #self.temp_prov_dir = filedialog.askdirectory(parent=root, initialdir=currdir,
                                                    # title='Please select the active provus folder')
        #if len(self.temp_prov_dir) > 0:
            #print("Provus directory set: %s" % self.temp_prov_dir)
        #self.temp_ga_dir = filedialog.askdirectory(parent=root, initialdir=currdir,
                                                  # title='Please select the folder that GA is monitoring')
       #if len(self.temp_ga_dir) > 0:
            #print("GA monitoring directory set: %s" % self.temp_ga_dir)
        #return self.temp_prov_dir, self.temp_ga_dir

    def prov_updater(self):

        """
        Main function that is called upon update to provus dir, or set amount of elapsed time
        Reads in all data from the provus dir and creates corresponding entities in geoh5 workspace
        Once all entities are created, a temp geoh5 file is pushed to GA monitoring Dir
        """

        # initializing empty dictionaries to store each data type generated by provus

        curves = {}
        surfaces = {}
        indices = {}
        curveLabel = {}
        surfaceLabel = {}
        # defining str keys that determine what type of xyz file is being read *subject to change*
        curv = "curve"
        surface = "surface"
        indi = "_indices"
        flag = "update"

        # setting directories to the user input paths
        global input_directory
        global monitoring_directory
        global export_mode
        if self.export_mode == 'true':
            global export_directory
            export_directory = self.export_dir
        input_directory = self.input_directory
        monitoring_directory = self.monitoring_directory
        export_mode = self.export_mode
        if export_mode == 'true':
            export_dir = self.export_dir
        if os.path.exists(os.path.join(monitoring_directory,"processed")):
            DeleteMonitor = os.listdir(os.path.join(monitoring_directory,"processed"))
            for tmp in DeleteMonitor:
                if tmp.endswith(".geoh5"):
                    os.remove(os.path.join(os.path.join(monitoring_directory,"processed"), tmp))
        InactiveGa = os.listdir(monitoring_directory)
        for tmp in InactiveGa:
            if tmp.endswith(".geoh5"):
                    os.remove(os.path.join(monitoring_directory, tmp))

        input_name = self.input_name
        files = os.listdir(input_directory)

        workspace = Workspace(input_name)  # define active workspace with user defined name
        
        
        
        
        # The following checks the file type being read in from input directory and assigns the data to appropriate dictionary
        if b_any(flag in f for f in files):
            for x in files:
                if flag in x:
                    os.remove(os.path.join(input_directory, x))

                if curv in x:
                    with open(os.path.join(input_directory, x)) as f:
                        name_hole = f.readline()

                    curveLabel[x] = name_hole.strip('\n')
                    pts_curve = pd.read_csv(os.path.join(input_directory, x), skiprows=1)
                    coord_curve = pts_curve.to_numpy()
                    curves[x] = coord_curve

                elif indi in x:
                    df_indi = pd.read_csv(os.path.join(input_directory, x))
                    attributes = df_indi.loc[:, ~df_indi.columns.isin(['X', 'Y', 'Z'])]
                    attribute_names = attributes.columns.tolist()
                    allData = pd.read_csv(os.path.join(input_directory, x))
                    data_headers = allData.head()
                    pts_indi = pd.read_csv(os.path.join(input_directory, x), usecols=["X", "Y", "Z"])
                    coord_indi = pts_indi.to_numpy()
                    indices[x] = coord_indi.astype(np.int32)
                    tester = 9

                elif surface in x:
                    with open(os.path.join(input_directory, x)) as g:
                        name_surface = g.readline()
                    surfaceLabel[x] = name_surface.strip('\n')
                    pts_surface = pd.read_csv(os.path.join(input_directory, x), skiprows=1, usecols=["X", "Y", "Z"])
                    coord_surface = pts_surface.to_numpy()
                    surfaces[x] = coord_surface.astype(np.float64)
                # iterate through all xyz files in provus dir


                # check what type each file is, read in data and place in corresponding dict where key = file name

        for y in files:
            if y.endswith('.xyz'):
                os.remove(os.path.join(input_directory, y))
                
                
                
                
        # create a list of all file names for each type of entity
        list_drillhole_names = list(curves.keys())
        list_surface_names = list(surfaces.keys())
        list_indices_names = list(indices.keys())
        list_surface_labels = list(surfaceLabel.values())
        list_curve_labels = list(curveLabel.values())
        ga_drill_name = "Provus Drillholes"  # container group name
        ga_surface_name = "Provus Surfaces"  # container group name

        # Create container groups for drillholes and surfaces
        # Checks to see if the group already exists in the root so no dupes are created

        groups_dr = [
            group_dr
            for group_dr in workspace.groups
            if group_dr.name == ga_drill_name
        ]
        if any(groups_dr):
            ga_group_dr = groups_dr[0]
        else:
            ga_group_dr = ContainerGroup.create(
                workspace, name=ga_drill_name
            )

        groups_sf = [
            group_sf
            for group_sf in workspace.groups
            if group_sf.name == ga_surface_name
        ]
        if any(groups_sf):
            ga_group_sf = groups_sf[0]
        else:
            ga_group_sf = ContainerGroup.create(
                workspace, name=ga_surface_name
            )

        # while loop that creates the curve entity for each drillhole in the input directory
        # checks to see if an entity   of same name belongs to the group
        # if entity of same name exists it just updates the data in the curve, else creates new curve

        i = 0
        while i < len(list_drillhole_names):
            drill_data = curves.get(list_drillhole_names[i])

            curve_entities = [
                child
                for child in ga_group_dr.children
                if child.name == list_curve_labels[i]
            ]
            if any(curve_entities):

                curve_temp = curve_entities[0]

                for child in curve_temp.children:
                   workspace.remove_entity(child)

                curve_temp.vertices = drill_data

                i += 1

            else:
                curve = Curve.create(
                    workspace,
                    name=list_curve_labels[i],
                    vertices=drill_data,
                    parent=ga_group_dr,
                )

                i += 1

        # while loop that creates the curve entity for each surface in the input directory
        # checks to see if an entity of same name belongs to the group
        # if entity of same name exists it just updates the data in the surface, else creates new surface

        j = 0
        while j < len(list_surface_names):
            surface_data = surfaces.get(list_surface_names[j])
            cell_data = indices.get(list_indices_names[j])

            surface_entities = [
                child
                for child in ga_group_sf.children
                if child.name == list_surface_labels[j]
            ]
            if any(surface_entities):

                surface_temp = surface_entities[0]

                #for child in surface_temp.children:
                  #workspace.remove_entity(child)

                surface_temp.vertices = surface_data
                surface_temp.cells = cell_data



                j += 1

            else:

                surface = Surface.create(
                    workspace,
                    vertices=surface_data,  # Add vertices
                    cells=cell_data,
                    name=list_surface_labels[j],
                    parent=ga_group_sf
                )
                if len(attribute_names) > 0:
                    attribute_counter = 0
                    while attribute_counter < len(attribute_names):
                        attribute_numpy = attributes[attribute_names[attribute_counter]].to_numpy()
                        surface.add_data({
                           attribute_names[attribute_counter]: {
                                "association": "CELL",
                                "values":attribute_numpy.astype(np.float64)
                             }

                         })
                        attribute_counter += 1
                j += 1

        # call live_link_output for each group to generate temporary geoh5 and move it to monitoring dir

        self.ga_output(
            monitoring_directory, ga_group_dr
        )
        self.ga_output(
            monitoring_directory, ga_group_sf
        )
        workspace.finalize()


DeleteWork = os.listdir(os.getcwd())
for z in DeleteWork:
    if z.endswith(".geoh5"):
        os.remove(os.path.join(os.getcwd(), z))
# call main function every 1 second(s), this checks if the update flag file exists will call main routine if it exists and deletes file upon completion
starttime = time.time()
app = updater()

try:
    app.prov_updater()
    print("CTRL -C to exit")
    while True:

        if export_mode == 'true':
            break

        if os.path.exists(os.path.join(input_directory, "update_flag.txt")) == True:
            app.prov_updater()
            time.sleep(1.0 - ((time.time() - starttime) % 1.0))
        else: time.sleep(1.0 - ((time.time() - starttime) % 1.0))

except KeyboardInterrupt:
    print('ending monitoring')
