import numpy as np

class imgData:
    """
    This class is for storing the data associated with one PV.
    Including data by step.

    """

    def __init__(self, inputName : "String" = None,
                 inputSteps : "array like" = None,
                fileNames : "array like" = None,
                 pici : "array like" = None,
                n_shot : "scalar" = None):
        
        # Name of the PV/camera
        self.name = inputName
        
        # The steps for each data point
        self.steps = inputSteps

        # The index for each matched data point
        self.pici = pici

        # The requested number of shots per step
        self.n_shot = n_shot

        # The filenames including path for the hdf5 files
        self.filelocs = fileNames

        # Holder for scalars that result from applying a function to the images.
        self.scalars = None

        # Populate the idxByStep Data
        # If we have two steps with 3 shots each and all data is matched:
        # This is the list of absolute indices for each step so [[0,1,2], [3,4,5]]
        # This will be in order of the matched steps, so there should be no skipped numbers.
        # It should be the same length as self.steps.
        self.absoluteIdxByStep = None
        
        # This is the list of relative indices for each step so [[0,1,2], [0,1,2]]
        self.relativeIdxByStep = None
        self.convertScalarIndexToIndexByStep()

        # # Where image data for a given step will be stored.
        # self.singleStepOfImageData = None

    def convertScalarIndexToIndexByStep(self) -> None:
        """
        The indexing that comes from the DAQ is a linear list of all matched data that doesn't indicate step.
        So if you have a data set that has 2 steps of three shots each the DAQ tells you to use
        idx = [0, 1, 2, 3, 4, 5] (python counting, the conversion from matlab counting is handled elsewhere.)
        The images for each step are stored in separate HDF5 files, and each file will start counting at 0.

        This function splits up the matched indices by step and stores them in a list for easy access later.
        In the above example the list that is stored is [[0, 1, 2], [0, 1, 2]]
        
        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.absoluteIdxByStep = []
        self.relativeIdxByStep = []
        k = 0
        for u in np.unique(self.steps):
            # Indexes where to find the images that are matched
            temp = self.pici[np.where(self.steps == u)]
            
            # Store the relative indexes in the class
            self.relativeIdxByStep.append(temp - (u-1)*self.n_shot)
            
            # Create the lists that contain the absolute index of each matched shot.
            # self.absoluteIdxByStep.append(self.pici[np.where(self.steps == u)])
            self.absoluteIdxByStep.append([j for j in range(k, k+len(temp))])
            k = k + len(temp)

    def applyFunctionToImagesScalarOutput(self, funcIn, *args) -> None:
        """
        Applies a user supplied function 'funcIn' to all the images in the data set.
        Result is written to self.scalars.
        
        Parameters
        ----------
        funcIn : callable
                The model function, f(x, …). It must take an image as its first argument.
        *args  : Any arguments required for funcIn


        Returns
        -------
        None
        """
        # Create a holder for the data
        a = np.zeros(len(self.steps), dtype=np.float32)

        k = 0
        for u in np.unique(self.steps):
            # Load the HDF5 file
            f = h5py.File(fart.filelocs[u-1], "r")
            # Iterate through the matched shots and apply a function
            for i in zip(self.relativeIdxByStep[u-1], self.absoluteIdxByStep[u-1]):
                f['entry']['data']['data'][i]
            
            print(self.filelocs[u - 1])
        # You need to loop through the list of relativeIdxByStep and apply the function to the images, then save in the correct location using absoluteIdxByStep.
        
        



