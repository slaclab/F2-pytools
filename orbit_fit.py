import numpy as np
from epics import get_pv
from meme.model import Model
from orbit import FacetOrbit
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

AIDA_NAME_FLIP_LIST=  [
    "BPMS:LI11:401", 
    "BPMS:LI11:501",
    "BPMS:LI11:601",
    "BPMS:LI11:701",
    "BPMS:LI11:801",
    "BPMS:LI11:901",
    "BPMS:LI12:201",
    "BPMS:LI12:301",
    "BPMS:LI12:401",
    "BPMS:LI12:501",
    "BPMS:LI12:601",
    "BPMS:LI12:701",
    "BPMS:LI12:801",
    "BPMS:LI12:901",
    "BPMS:LI13:201",
    "BPMS:LI13:301",
    "BPMS:LI13:401",
    "BPMS:LI13:501",
    "BPMS:LI13:601",
    "BPMS:LI13:701",
    "BPMS:LI13:801",
    "BPMS:LI13:901",
    "BPMS:LI14:201",
    "BPMS:LI14:301",
    "BPMS:LI14:401",
    "BPMS:LI14:501",
    "BPMS:LI14:601",
    "BPMS:LI14:701",
    "BPMS:LI14:901",
    "BPMS:LI15:201",
    "BPMS:LI15:301",
    "BPMS:LI15:401",
    "BPMS:LI15:501",
    "BPMS:LI15:601",
    "BPMS:LI15:701",
    "BPMS:LI15:801",
    "BPMS:LI15:901",
    "BPMS:LI16:201",
    "BPMS:LI16:301",
    "BPMS:LI16:401",
    "BPMS:LI16:501",
    "BPMS:LI16:601",
    "BPMS:LI16:701",
    "BPMS:LI16:801",
    "BPMS:LI16:901",
    "BPMS:LI17:201",
    "BPMS:LI17:301",
    "BPMS:LI17:401",
    "BPMS:LI17:501",
    "BPMS:LI17:601",
    "BPMS:LI17:701",
    "BPMS:LI17:801",
    "BPMS:LI17:901",
    "BPMS:LI18:201",
    "BPMS:LI18:301",
    "BPMS:LI18:401",
    "BPMS:LI18:501",
    "BPMS:LI18:601",
    "BPMS:LI18:701",
    "BPMS:LI18:801",
    "BPMS:LI18:901",
    "BPMS:LI19:201",
    "BPMS:LI19:301",
    "BPMS:LI19:401",
    "BPMS:LI19:501",
    "BPMS:LI19:601",
    "BPMS:LI19:701",
    "BPMS:LI19:801",
    "BPMS:LI19:901",
    ]

LI19_BLACKLIST = [
    "BPMS:LI19:501",
    "BPMS:LI19:601",
    "BPMS:LI19:701",
    "BPMS:LI19:901",
    ]


def fit_orbit(live_orbit, model, sigma_0=0.0001, axis='x', z_in=None, z_fin=None):
    """
    Fits the BPM orbit data to extract trajectory parameters A, B, C.
    
    Parameters:
      live_orbit
      model
      sigma_0: placehokder BPM resolution in meters
      axis: 'x' or 'y' (which orbit to fit)
    
    Returns:
      p: array [A, B, C]
      sigma_p: array of uncertainties [sigma_A, sigma_B, sigma_C]
    """
    bpms = live_orbit.bpms
    B_list = []
    z_list = []
    
    for bpm in bpms:

        # Filter BPMs based on z-interval if specified
        if z_in is not None and z_fin is not None:
            if bpm.z < z_in or bpm.z > z_fin:
                continue
        
        # get the measurement based on the axis
        if axis == 'x':
            nu = bpm.x_pv_obj.get()
        elif axis == 'y':
            nu = bpm.y_pv_obj.get()
            
        if nu is None or np.isnan(nu):
            continue
        nu /= 1000  # convert mm to m
        
        # Check if BPM name exists in the model
        bpm_name = bpm.name
        if bpm_name in LI19_BLACKLIST: continue
        if bpm_name in AIDA_NAME_FLIP_LIST:
            ns = bpm_name.split(':')
            if bpm_name == 'BPMS:LI13:301':
                bpm_name = f'{ns[1]}:{ns[0]}:303'
            else:
                bpm_name = f'{ns[1]}:{ns[0]}:{ns[2]}'

        model._get_indices_for_names([bpm_name], split_suffix=False, ignore_bad_names=False)
        
        twiss = model.get_twiss(bpm_name)
        if axis == 'x':
            beta = twiss['beta_x']
            psi  = twiss['psi_x']
            eta  = twiss['eta_x']
        else:  # axis == 'y'
            beta = twiss['beta_y']
            psi  = twiss['psi_y']
            eta  = twiss['eta_y']
        
        g1 = np.sqrt(beta) * np.sin(psi)
        g2 = np.sqrt(beta) * np.cos(psi)
        g3 = eta
        sigma_nu = sigma_0
        
        B_row = [g1 / sigma_nu, g2 / sigma_nu, g3 / sigma_nu]
        z_nu = nu / sigma_nu
        
        B_list.append(B_row)
        z_list.append(z_nu)
    
    
    B = np.array(B_list)
    z = np.array(z_list)
    
    T = np.linalg.inv(B.T @ B)
    p = T @ B.T @ z
    sigma_p = np.sqrt(np.diag(T))
    
    return p, sigma_p


def plot_orbit_fit(live_orbit, model, p, sigma_p, sigma_0=0.0001, num_points=1000, axis='x', z_in=None, z_fin=None, ax=None):
    """
    Plots the measured BPM data and the fitted trajectory within a specified z-interval.
    
    Parameters:
      live_orbit: Orbit data object containing BPMs
      model: Model object providing twiss parameters
      p: Array of fitted trajectory parameters [A, B, C]
      sigma_p: Array of uncertainties [sigma_A, sigma_B, sigma_C]
      sigma_0: Placeholder BPM resolution in meters 
      num_points: Number of points for the fitted trajectory
      axis: 'x' or 'y' (which orbit to plot)
      z_in: Start of the z-interval in meters 
      z_fin: End of the z-interval in meters 
      ax: Matplotlib axis object to plot on
      
    Returns:
      ax: Matplotlib axis with the plot
    """
    
    bpms = live_orbit.bpms
    
    # Collect twiss data for interpolation from all BPMs with valid measurements
    s_known = []
    beta_known = []
    psi_known = []
    eta_known = []
    
    for bpm in bpms:
        if axis == 'x':
            nu = bpm.x_pv_obj.get()
        elif axis == 'y':
            nu = bpm.y_pv_obj.get()
          
        if nu is None or np.isnan(nu):
            continue
        
        try:
            twiss = model.get_twiss(bpm.name)
            if axis == 'x':
                beta = twiss['beta_x']
                psi  = twiss['psi_x']
                eta  = twiss['eta_x']
            else:
                beta = twiss['beta_y']
                psi  = twiss['psi_y']
                eta  = twiss['eta_y']
            s_known.append(bpm.z)
            beta_known.append(beta)
            psi_known.append(psi)
            eta_known.append(eta)
        except (IndexError, KeyError, AttributeError):
            print(f"Warning: Could not retrieve twiss parameters for BPM {bpm.name}. Skipping for interpolation.")
            continue
    
    # Collect measurements for plotting within the specified z-interval
    s_bpm = []
    nu_bpm = []
    sigma_bpm = []
    
    for bpm in bpms:
        if axis == 'x':
            nu = bpm.x_pv_obj.get()
        elif axis == 'y':
            nu = bpm.y_pv_obj.get()
          
        if nu is None or np.isnan(nu):
            continue
        nu /= 1000  # Convert mm to m
        
        # Filter BPMs based on z-interval if specified
        if z_in is not None and z_fin is not None:
            if bpm.z < z_in or bpm.z > z_fin:
                continue
        
        s_bpm.append(bpm.z)
        nu_bpm.append(nu)
        sigma_bpm.append(sigma_0)
    
    # Determine the range for the fitted trajectory
    if z_in is not None and z_fin is not None:
        s_min = z_in
        s_max = z_fin
    else:
        s_min = min(s_bpm)
        s_max = max(s_bpm)
    
    s_fit = np.linspace(s_min, s_max, num_points)
    
    # Sort known points for interpolation
    sorted_indices = np.argsort(s_known)
    s_known = np.array(s_known)[sorted_indices]
    beta_known = np.array(beta_known)[sorted_indices]   
    psi_known = np.array(psi_known)[sorted_indices]
    eta_known = np.array(eta_known)[sorted_indices]
    
    # Create interpolation functions
    beta_interp = interp1d(s_known, beta_known, kind='linear', fill_value="extrapolate")
    psi_interp = interp1d(s_known, psi_known, kind='linear', fill_value="extrapolate")
    eta_interp = interp1d(s_known, eta_known, kind='linear', fill_value="extrapolate")
    
    # Generate fitted trajectory
    nu_fit = []
    for s in s_fit:
        beta_val = beta_interp(s)
        psi_val = psi_interp(s)
        eta_val = eta_interp(s)
        
        g1 = np.sqrt(beta_val) * np.sin(psi_val)
        g2 = np.sqrt(beta_val) * np.cos(psi_val)
        g3 = eta_val
        
        nu_val = p[0] * g1 + p[1] * g2 + p[2] * g3
        nu_fit.append(nu_val)
    
    nu_fit = np.array(nu_fit)
    
    # Plot BPM measurements with error bars
    ax.errorbar(s_bpm, nu_bpm, yerr=sigma_bpm, fmt='o', label=f'BPM {axis.upper()} Measurements', capsize=3)
    
    # Plot fitted trajectory
    ax.plot(s_fit, nu_fit, 'r-', label=f'Fitted {axis.upper()} Trajectory')
    
    # Add fitted parameters to the plot
    param_text = (
        f"Fit Parameters:\n"
        f"A = {p[0]:.6f} ± {sigma_p[0]:.6f}\n"
        f"B = {p[1]:.6f} ± {sigma_p[1]:.6f}\n"
        f"C = {p[2]:.6f} ± {sigma_p[2]:.6f}"
    )
    if z_in is not None and z_fin is not None:
        param_text += f"\nFit over z = [{z_in}, {z_fin}] m"
    
    ax.text(0.98, 0.98, param_text,
            verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes,
            bbox=dict(boxstyle='round,pad=0.5', fc='wheat', alpha=0.5))

    ax.set_xlabel('Longitudinal Position s [m]')
    if axis == 'x':
        ax.set_ylabel('Horizontal Position x [m]')
        ax.set_title('X Orbit Fit')
    else:
        ax.set_ylabel('Vertical Position y [m]')
        ax.set_title('Y Orbit Fit')
    ax.legend()
    ax.grid(True)
    
    return ax

if __name__ == '__main__':
    # Test orbit fit & plot with a z-interval

    # Create model and live orbit objects
    model = Model('FACET2E', 'BMAD', use_design=True)
    live_orbit = FacetOrbit(ignore_bad_bpms=True, rate_suffix='TH', scp_suffix='57')
    live_orbit.connect()

    # Define z-interval
    z_in = 1000
    z_fin = 1500  

    # Fit x orbit with z-interval
    p_x, sigma_p_x = fit_orbit(live_orbit, model, sigma_0=0.0001, axis='x', z_in=z_in, z_fin=z_fin)
    print("X Orbit Fit:")
    print(f"A = {p_x[0]:.6f} ± {sigma_p_x[0]:.6f}")
    print(f"B = {p_x[1]:.6f} ± {sigma_p_x[1]:.6f}")
    print(f"C = {p_x[2]:.6f} ± {sigma_p_x[2]:.6f}")

    # Fit y orbit with z-interval
    p_y, sigma_p_y = fit_orbit(live_orbit, model, sigma_0=0.0001, axis='y', z_in=z_in, z_fin=z_fin)
    print("\nY Orbit Fit:")
    print(f"A = {p_y[0]:.6f} ± {sigma_p_y[0]:.6f}")
    print(f"B = {p_y[1]:.6f} ± {sigma_p_y[1]:.6f}")
    print(f"C = {p_y[2]:.6f} ± {sigma_p_y[2]:.6f}")

    # Create a figure with two subplots to display both fits
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))
    plot_orbit_fit(live_orbit, model, p_x, sigma_p_x, sigma_0=0.0001, num_points=1000, axis='x', z_in=z_in, z_fin=z_fin, ax=ax1)
    plot_orbit_fit(live_orbit, model, p_y, sigma_p_y, sigma_0=0.0001, num_points=1000, axis='y', z_in=z_in, z_fin=z_fin, ax=ax2)
    plt.tight_layout()
    plt.show()

