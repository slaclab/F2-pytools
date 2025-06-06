# This file creates a class that handles loading a BMAD model instance and the helper functions you need to set quads

import pytao
from pytao import Tao, SubprocessTao
import pandas as pd
import numpy as np

class bmadModel:

    def __init__(self, idx1 = 0, idx2 = 174):
        # This is hard coded because it is the default location for the most up to date lattice on the control system.
        tao_init_file = "/usr/local/facet/tools/facet2-lattice/bmad/models/f2_elec/tao.init"
        # Fire up the model using pytao
        self.tao = Tao("-init " + tao_init_file + " -noplot")

        # Create a list of all the elements in desired region
        self.all_ele = self.tao.lat_list(str(idx1) + ":" + str(idx2), "ele.name")

        # Extract all the BPMS
        self.bpms_bmad = [i.split("#")[0] for i in self.all_ele if self.tao.lat_list(i, "ele.key")[0] == 'Monitor' and i.split("#")[0][0:3] == "BPM"]
        # The EPICS bpms will be missing the _X and _Y
        self.bpms_epic = [self.tao.ele_head(i)["alias"].replace(":", "_") for i in self.bpms_bmad]

        # Extract all the quads
        self.quads_bmad = [i.split("#")[0] for i in self.all_ele if self.tao.lat_list(i, "ele.key")[0] == 'Quadrupole']
        self.quads_bmad = list(dict.fromkeys(self.quads_bmad))

        # Load the default model quad fields, which are in T/m
        # Is this used?
        # self.quads_fields = [self.tao.ele_gen_attribs(i)["B1_GRADIENT"] for i in self.quads_bmad]
        
        self.quads_epic = [self.tao.ele_head(i)["alias"].replace(":", "_")+"_BACT" for i in self.quads_bmad]

    def printAllQuads(self) -> "Pandas Dataframe":
        """
        Print out all the quads that are currently used by the instance of the class.
        Going to use a pandas method to do this, though it is overkill. Consider re-writing later.
        """
        df = pd.DataFrame(data = {"bmadQuadsNames" : self.quads_bmad, "epicQuadsNames" : self.quads_epic, "bmadQuadFieldTperM" : self.quads_fields})
        return df

    def printAllBpms(self) -> "Pandas Dataframe":
        """
        Print out all the quads that are currently used by the instance of the class.
        Going to use a pandas method to do this, though it is overkill. Consider re-writing later.
        """
        df = pd.DataFrame(data = {"bmadBpms" : self.bpms_bmad, "epicBpms" : self.bpms_epic})
        return df

    # def currentModelQuadSettings(self) -> "List : T/m":
    #     """
    #     Output the current model quad settings for the quads in the model

    #     Return: List of quad values used by the model
    #     """
    #     return self.quads_fields

    def outputBetaFunctions(self, loc_list : "list, string" = None) -> np.ndarray:
        """
        Output the beta function for all the locations requested

        Return: numpy array where array[:,0] is beta_x, array[:,1] is beta_y
        """
        if loc_list is None:
            loc_list = self.all_ele

        temp = np.zeros((len(loc_list), 2))
        for i in range(len(loc_list)):
            temp[i, 0] = self.tao.ele_twiss(loc_list[i])['beta_a']
            temp[i, 1] = self.tao.ele_twiss(loc_list[i])['beta_b']
            
        return temp   

    def setQuadkG(self, quadName, integratedFieldkG):
        """EPICS uses integrated field in kG for the quad settings. BMAD uses T/m.
        So you need to know the quad length to convert between the two.
        There is also a sign convention difference between BMAD and EPICS.
        
        Inputs:
        quadName : string of element number or name
        integratedFieldkG: float/double of the desired quad setting in EPICS format
    
        Outputs:
        None
        """
        quadLength = self.tao.ele_gen_attribs(quadName)["L"]
        bmadGradientTeslaPerMeter = -0.1 * integratedFieldkG / quadLength
        self.tao.cmd(f"set ele {quadName} B1_GRADIENT = bmadGrabmadGradientTeslaPerMeter")
    
        return

    def convertEPICSkGtoBMADTperM(self, quadName : "List: string" , EPICSintegratedFieldkG : "List: float" ) -> "list : float":
        """
        EPICS uses integrated field in kG for the quad settings. BMAD uses T/m.
        So you need to know the quad length to convert between the two.
        There is also a sign convention difference between BMAD and EPICS.
        
        Inputs:
        quadName : list of string of element number or name
        integratedFieldkG: list of float/double of the desired quad setting in EPICS format
    
        Outputs:
        bmadGradientTeslaPerMeter: The field in T/m for with BMAD sign convention
        """

        # If the input is a single element, turn it into a list
        if not isinstance(quadName,list):
            quadName = [quadName]
            EPICSintegratedFieldkG = [EPICSintegratedFieldkG]

        temp = []
        for i in zip(quadName, EPICSintegratedFieldkG):
            quadLength = self.tao.ele_gen_attribs(i[0].split("#")[0])["L"]
            temp.append(-0.1 * i[1] / quadLength)
            
        return temp
    
    def convertBMADTperMtoEPICSkG(self, quadName, bmadGradientTeslaPerMeter) -> float:
        """
        EPICS uses integrated field in kG for the quad settings. BMAD uses T/m.
        So you need to know the quad length to convert between the two.
        There is also a sign convention difference between BMAD and EPICS.
    
        Inputs:
        quadName : string of element number or name
        integratedFieldkG: float/double of the desired quad setting in EPICS format
    
        Outputs:
        None
        """
        
        quadLength = self.tao.ele_gen_attribs(quadName.split("#")[0])["L"]
        EPICSintegratedFieldkG = -10 * quadLength * bmadGradientTeslaPerMeter
        return EPICSintegratedFieldkG
    
    def setBmadQuad(self, quadName : "List: string" = None, fieldInTperM : "List : T/m" = None):
        
        """
        Update the quad values in the model.

        To set quad strengths in BMAD you sometimes need to find the "lord" element.
        This function handles finding the lord and setting the gradient.
        
        Quads that a split are defined using #. So Q19801 is the 'lord' to Q19801#1 and Q19801#2.
        To set the quad you should split off the # component and then write the quad value.
        I believe this split is automatic, so is fairly reliable.
        In the future you should find a way to get the slave_status and then its associated 
        lords so you don't need to rely on names.
        
        Parameters
        ----------
        bmadQuadNames : list
            list of bmad element names for quads to update.
        fieldInTperM : list
            The field to update to. In T/m.
        
        Returns
        -------
        Nothing
            Function returns nothing.
        
        Raises
        ------
        KeyError
            when a key error
        OtherError
            when an other error
        """
        # If the input is a single element, turn it into a list
        if not isinstance(quadName,list):
            quadName = [quadName]
            fieldInTperM = [fieldInTperM]

        for i in zip(quadName, fieldInTperM):
            if np.isnan(i[1]):
                continue
            self.tao.cmd("set ele {} B1_GRADIENT = {}".format(i[0].split('#')[0], i[1]))

        # # Update the quad fields in the current class instance
        # self.quads_fields = [self.tao.ele_gen_attribs(i)["B1_GRADIENT"] for i in self.quads_bmad]

    def calculateRMatrix(self, bmadEleNamesStart : "list, strings" , bmadEleNamesEnd : "list, strings" ) -> "list, nd.nparray":     
        """
        Calculate the R matrix between two BMAD elements. Note that by default BMAD returns the R matrix from the END of the first element to the end of the second.
        
        Parameters
        ----------
        bmadEleNamesStart : list
            list of strings that are bmad element names.
        bmadEleNamesEnd : list
            list of strings that are bmad element names.
        
        Returns
        -------
        R-matrix
            list of nd.nparray of the R matrices
        """
        # If the input is a single element, turn it into a list
        if not isinstance(bmadEleNamesStart,list):
            bmadEleNamesStart = [bmadEleNamesStart]
        if not isinstance(bmadEleNamesEnd,list):
            bmadEleNamesEnd = [bmadEleNamesEnd]
        
        # Populate the transport matrix elements
        output = []
        for i in zip(bmadEleNamesStart, bmadEleNamesEnd):
            output.append(self.tao.matrix(i[0], i[1])["mat6"])
        
        return output

    def translateBmadBpmsToEpics(self, bmadBpmsNames : "list, strings" = None) -> "list, strings":
        """
        Translate BMAD element BPM names to DAQ/EPICS scalar data names.
        Note that the BPMS must be part of the current instance, this is not a generic function.
        i.e. they must be in self.bpms_bmad
        
        Parameters
        ----------
        bmadBpmsNames : list
            list of strings that are bmad element names.
        
        Returns
        -------
        epics bpm names : list
            list of strings that are daq/epics element names
        """
        if bmadBpmsNames is None:
            return []
        
        # If the input is a single element, turn it into a list
        if not isinstance(bmadBpmsNames,list):
            bmadBpmsNames = [bmadBpmsNames]

        output = []
        for ele in bmadBpmsNames:
            try:
                output.append(self.bpms_epic[self.bpms_bmad.index(ele)])
            except ValueError:
                print('BPM name not found, returning empty string.')
                output.append('')

        return output
        
    def calculateTMatrix(self, bmadEleNames : "list, strings") -> "list, np.adarray":
        """
        Generate the "T" matrix that is used to derive the beam phase space at the first element in the list of inputs.
        
        Parameters
        ----------
        bmadEleNames : list
            list of strings that are bmad element names.
        
        Returns
        -------
        T-matrix
            list of nd.nparray of the T matrices. First entry is X, second is Y.
        """
        
        temp = self.calculateRMatrix(len(bmadEleNames)*[bmadEleNames[0]], bmadEleNames)
        Tx = np.zeros((len(bmadEleNames), 3))
        Ty = np.zeros((len(bmadEleNames), 3))
        for i in range(len(temp)):
            Tx[i, 0:2] = temp[i][0, 0:2]
            Tx[i, 2] = temp[i][0, 5]
        
            Ty[i, 0:2] = temp[i][2, 2:4]
            Ty[i, 2] = temp[i][2, 5]

        return [Tx, Ty]

    def returnBmadQuadValues(self, bmadQuadNames : "list, strings" = None) -> "list, float":
        """
        Return the current quad values from the bmad model.
        Currently no error handling for bad element names, it will just error.
        
        Parameters
        ----------
        bmadQuadNames : list
            list of strings that are bmad quad element names.
        
        Returns
        -------
        output : list, float
            list of floats that correspond to the quad setting in T/m
        """
        if bmadQuadNames == None:
            bmadQuadNames = self.quads_bmad
        
        # If the input is a single element, turn it into a list
        if not isinstance(bmadQuadNames, list):
            bmadQuadNames = [bmadQuadNames]
        
        return [self.tao.ele_gen_attribs(i)["B1_GRADIENT"] for i in bmadQuadNames]

