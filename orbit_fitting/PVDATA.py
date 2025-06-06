import numpy as np

class pvData:
    """
    This class is for storing the data associated with one PV.
    Including data by step.

    """

    def __init__(self, inputName : "String" = None,
                 inputData : "array like" = None,
                 inputSteps : "array like" = None):
        
        # Name of the PV
        self.name = inputName
        
        # The data that isn't divided by step
        self.data = inputData
        
        # The steps for each data point
        self.steps = inputSteps

        # Holder for the data by steps
        self.dataBySteps = None
        self.splitDataIntoSteps()

    def mean(self) -> np.float32:
        """
        Return the mean of all the data in the PV. Ignores nans in the data.
        
        Parameters
        ----------
        inputPV : None

        Returns
        -------
        np.float32 or np.nan if all data is nan
        """
        return np.nanmean(self.data)

    def std(self) -> np.float32:
        """
        Return the std of all the data in the PV. Ignores nans in the data.
        
        Parameters
        ----------
        None

        Returns
        -------
        np.float32 or np.nan is all data is nan
        """
        return np.nanstd(self.data)

    def splitDataIntoSteps(self):
        """
        Split the data into steps and store the data in the class for use later.
        Stored in self.dataBySteps.
        
        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        temp = []
        for u in np.unique(self.steps):
            temp.append(self.data[np.where(self.steps == u)])
        self.dataBySteps = temp

    def isAllNan(self):
        """
        Test if all the data is nans
        
        Parameters
        ----------
        None

        Returns
        -------
        True if all nans, false otherwise
        """
        if np.isnan(self.data).sum() == len(self.data):
            return True
        else:
            return False
        
        
    def meanByStep(self) -> np.float32:
        """
        Return the means of each step in the data.
        If there is only one step, result is the same as self.mean().
        
        Parameters
        ----------
        inputPV : None

        Returns
        -------
        np.float32
        """
        return [np.nanmean(K) for K in self.dataBySteps]

    def stdByStep(self) -> np.float32:
        """
        Return the stds of each step in the data.
        If there is only one step, result is the same as self.mean().
        
        Parameters
        ----------
        inputPV : None

        Returns
        -------
        np.float32
        """
        return [np.nanstd(K) for K in self.dataBySteps]




