import scipy
import numpy as np

class daqDataSet:

    def __init__(self, daqFile = None):
        if daqFile is None:
            DAQ_NUM = "E300_12005"
            daqFile = "/nas/nas-li20-pm00/E300/2025/20250330/"+DAQ_NUM+"/"+DAQ_NUM+".mat"
        
        self.data = scipy.io.loadmat(daqFile, simplify_cells=True)["data_struct"]
        
        
        # If the DAQ has SCP data, select the appropriate indexes
        for k in self.data['scalars'].keys():
            if k.split("_")[0] == "SCP":
                # --------- If you find this later than 8/30/25 delete the stuff between -------
                # # psci = python scalar common index (for BSA data)
                # self.psci = self.data['scalars']['common_index_inclSCP'] - 1

                # # pssi = python scalar scp index
                # self.pssi = self.data['scalars']['common_index_SCP'] - 1
                # ------------------------------------------------------------------------------

                # Load the BSA and SCP indices
                try:
                    # Try to load the new style of BSA and SCP indices
                    # psci = python scalar common index (for BSA data)
                    self.psci = self.data['scalars']['common_index_inclSCP'] - 1
                except:
                    # If the old style is found, warn the user they may not match.
                    print("Found old style SCP indexes - they won't match EPICS BSA data automatically")
                    # Load the old style of indices.
                    self.psci = self.data['scalars']['common_index'] - 1
                    self.pssi = self.data['scalars']['SCP_common_idx'] - 1
                else:
                    # If there is no error, load the new style of indices
                    # psci = python scalar common index (for BSA data)
                    self.psci = self.data['scalars']['common_index_inclSCP'] - 1
                    # pssi = python scalar scp index
                    self.pssi = self.data['scalars']['common_index_SCP'] - 1
                  
                self.has_scp = 1
                break
            else:
                # There is always BSA data even if there isn't SCP data
                # Store the scalar index for python. psci = python scalar common index
                self.psci = self.data['scalars']['common_index'] - 1
                self.has_scp = 0
        
        self.steps = self.data['scalars']['steps'][self.psci]
        self.daqnum = daqFile.split("/")[-2]

    def returnScalarPVmean(self, inputPVList) -> np.ndarray:
        """
        Return a list of mean values for a list of PV strings
        
        Parameters
        ----------
        inputPV : list of strings
            List of strings that are PV names

        Returns
        -------
        np.ndarray
            Array of means of PV values for the common_indices
            Returns np.nan if the array for a particular PV value is empty
        """
        
        # If the input is a single element, turn it into a list
        if not isinstance(inputPVList, list):
            inputPVList = [inputPVList]

        temp = self.returnScalarPV(inputPVList)
        # return [np.nanmean(PV) if np.size(PV) > 0 else np.nan for PV in temp]
        output = []
        for o in temp:
            # Take the mean only if the array isn't empty and also if it isn't all nans
            if (np.size(o) > 0) and (~np.isnan(o).all()):
                output.append(np.nanmean(o))
            else:
                output.append(np.nan)
        return output


    def returnScalarPVstd(self, inputPVList : "list, np.ndarray") -> np.ndarray:
        """
        Return a list of std values for a list of PV strings
        
        Parameters
        ----------
        inputPV : list of strings
            List of strings that are PV names

        Returns
        -------
        np.ndarray
            Array of std of PV values for the common_indices
            Returns np.nan if the array for a particular PV value is empty
        """
        
        # If the input is a single element, turn it into a list
        if not isinstance(inputPVList, list):
            inputPVList = [inputPVList]

        temp = self.returnScalarPV(inputPVList)
        # return [np.nanmean(PV) if np.size(PV) > 0 else np.nan for PV in temp]
        output = []
        for o in temp:
            # Take the mean only if the array isn't empty and also if it isn't all nans
            if (np.size(o) > 0) and (~np.isnan(o).all()):
                output.append(np.nanstd(o))
            else:
                output.append(np.nan)
        return output

    
    def returnScalarPV(self, inputPVList : "list, strings") -> "list, np.ndarray":
        """
        Return a list of PV arrays for user provided list of PV strings
        
        Parameters
        ----------
        inputPV : list of strings
            List of strings that are PV names

        Returns
        -------
        np.ndarray
            Array of PV values for the common_indices
            Returns empty array if PV is not found.
        """
        
        # If the input is a single element, turn it into a list
        if not isinstance(inputPVList, list):
            inputPVList = [inputPVList]

        return [self.returnSingleScalarPV(PV) for PV in inputPVList]

    
    def returnSingleScalarPV(self, inputPV : "string") -> np.ndarray:     
        """
        Find and return the scalar data labeled with the input PV.
        If the same PV exists in two datasets, like BPM 3156 in both BSA and SCP,
        then the BSA data is returned.
        
        Parameters
        ----------
        inputPV : string
            String that is a PV name
        
        Returns
        -------
        np.ndarray
            Array of PV values for the common_indices
            Returns empty array if PV is not found.
        """
        
        # Find the PV by traversing the list of scalar groups
        # The sorted ensures that BSA elements come before SCP elements
        # which means if a PV is the same between BSA and SCP, you get the BSA data.
        for k in sorted(self.data['scalars'].keys()):

            # Now cycle through the PVs and return the PV if it is found
            # This only goes one level deep because that is all there is in the DAQ/Scalars
            if isinstance(self.data['scalars'][k], dict):
                for j in sorted(self.data['scalars'][k].keys()):
                    if j == inputPV:
                        if k.split("_")[0] == "SCP":
                            # The SCP data can have 0s in it when it doesn't get data.
                            # There is still a good time stamp, but not good data.
                            # Convert those zeros to nans here
                            temp = self.data['scalars'][k][j][self.pssi].astype(float)
                            temp[temp == 0] = np.nan
                            return temp
                        else:
                            return self.data['scalars'][k][j][self.psci].astype(float)
        
        # If the PV isn't found, return a list of nan that is the correct shape for BSA data
        temp = np.empty((np.shape(self.psci)))
        temp[:] = np.nan
        return temp
        # return np.empty((0))

    def returnBpmXandY(self, epicsEleNames : "list, strings") -> "list, np.adarray":
        """
        Generate the "B" matrix that is used to derive the beam phase space at the first element
        in the list of inputs.
        
        Parameters
        ----------
        bmadEleNames : list
            list of strings that are epics element names.
            The element names should not include the "_X" otr "_Y"
        
        Returns
        -------
        B-matrix
            list of nd.nparray of the B matrices. First entry is X, second is Y.
        """

        # If the input is a single element, turn it into a list
        if not isinstance(epicsEleNames, list):
            epicsEleNames = [epicsEleNames]
        
        # Modify the input PVs to include the X and Y pieces.
        X = self.returnScalarPV([F + "_X" for F in epicsEleNames])
        Y = self.returnScalarPV([F + "_Y" for F in epicsEleNames])
        
        # Subtract off the mean for all the elements. Divide by STD to normalize the data.
        # X = [(i - i.mean())/i.std() for i in X]
        # Y = [(i - i.mean())/i.std() for i in Y]

        # X = [(i - np.nanmean(i))/np.nanstd(i) for i in X]
        # Y = [(i - np.nanmean(i))/np.nanstd(i) for i in Y]

        # X = [(i - np.nanmean(i)) for i in X]
        # Y = [(i - np.nanmean(i)) for i in Y]
        
        # Stack the BPM vectors to generate the BPM matrix
        Bx = np.vstack(X)
        By = np.vstack(Y)

        return [Bx, By]

    def returnScalarPVByStep(self, inputPVList : "list, strings") -> "list of lists, np.ndarray":
        """
        Return a list of PV arrays for user provided list of PV strings
        Each PV returns a list of lists where each list is the data divided by a matched step.

        Example:
        Your data is a DAQ that scanned some parameter for 7 steps.
        You request data for 3 PVs from this function using input ["PV1", "PV2", "PV3"].
        
        This function returns a list with in a list that is
        len(output) = 3, for the 3 PVs requested
        len(output[0]) = 7, for the 7 steps in the scan
            Each step will have a different number of entries depending on how many matched shot
            there are in each step.
        
        Parameters
        ----------
        inputPV : list of strings
            List of strings that are PV names

        Returns
        -------
        np.ndarray
            Array of PV values for the matched shots, divided by the steps
            Returns empty array if PV is not found.
        """

        steppedData = self.returnScalarPV(inputPVList)
        uniques = np.unique(self.steps)
        # Double list comprehension can be a bit confusing.
        # Consider rewriting to make easier to understand after a long day.
        return [ [K[np.where(self.steps == i)] for i in uniques] for K in steppedData]


    def returnScalarPVByStepMean(self, inputPVList : "list, strings") -> "list of lists, np.ndarray":
        """
        Return a list of means for user provided list of PV strings
        Each PV returns a list where each list is the mean of the data divided by a matched step.

        Example:
        Your data is a DAQ that scanned some parameter for 7 steps.
        You request data for 3 PVs from this function using input ["PV1", "PV2", "PV3"].
        
        This function returns a list with in a list that is
        len(output) = 3, for the 3 PVs requested
        len(output[0]) = 7, for the 7 steps in the scan
            Each step will have one value
        
        Parameters
        ----------
        inputPV : list of strings
            List of strings that are PV names

        Returns
        -------
        np.ndarray
            Array of means of PV values for each steps
            Returns nan if PV is not found.
        """

        allData = self.returnScalarPVByStep(inputPVList)
        return [[np.nanmean(J) for J in K] for K in allData]

    def returnScalarPVByStepStd(self, inputPVList : "list, strings") -> "list of lists, np.ndarray":
        """
        Return a list of stds for user provided list of PV strings
        Each PV returns a list where each list is the std of the data divided by a matched step.

        Example:
        Your data is a DAQ that scanned some parameter for 7 steps.
        You request data for 3 PVs from this function using input ["PV1", "PV2", "PV3"].
        
        This function returns a list with in a list that is
        len(output) = 3, for the 3 PVs requested
        len(output[0]) = 7, for the 7 steps in the scan
            Each step will have one value
        
        Parameters
        ----------
        inputPV : list of strings
            List of strings that are PV names

        Returns
        -------
        np.ndarray
            Array of stds of PV values for each steps
            Returns nan if PV is not found.
        """

        allData = self.returnScalarPVByStep(inputPVList)
        return [[np.nanstd(J) for J in K] for K in allData]

    def returnSingleCameraMetaData(self, inputCamName : "string") -> "np.ndarray, array of strings":
        """
        Returns the metadata required to load camera images from hdf5 files.
        The metadata required is the step number for each valid shot and the list of hdf5 file locations.
        Valid in this case means it is contained in the matched list with BSA and SCP PVs.
        
        Parameters
        ----------
        inputPV : a camera name
            i.e. SYAG or GAMMA1

        Returns
        -------
        np.ndarray
            A list of step numbers that is aligned with the BSA and SCP data.
            A list of where to find the hdf5 files for each step.
        """
        if self.has_scp == 0:
            idx = self.data['images'][inputCamName]['common_index']-1

        if self.has_scp == 1:
            idx = self.data['images'][inputCamName]['common_index_inclSCP']-1

        steps = self.data['images'][inputCamName]['step'][idx]
        filelocs = self.data['images'][inputCamName]['loc']
        n_shot = self.data['params']['n_shot']

        return steps, filelocs, idx, n_shot












            

