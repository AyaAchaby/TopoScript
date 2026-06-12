import numpy as np


def calculate_light_iv_params(voltage, current):
    V = np.array(voltage, dtype=float)
    I = np.array(current, dtype=float)

    idx_isc = np.argmin(np.abs(V))
    isc = I[idx_isc]

    voc = np.nan
    sign_change = np.where(np.diff(np.sign(I)) != 0)[0]

    if len(sign_change) > 0:
        idx = sign_change[0]
        i_fit = I[idx:idx + 2]
        v_fit = V[idx:idx + 2]
        voc = np.polyfit(i_fit, v_fit, 1)[1]

    power = -I * V

    idx_pmax = np.argmax(power)
    pmax = power[idx_pmax]
    imp = I[idx_pmax]
    vmp = V[idx_pmax]

    ff = np.nan
    if not np.isnan(voc) and isc != 0 and voc != 0:
        ff = -pmax / (isc * voc)

    return {
        "Isc_A": isc,
        "Voc_V": voc,
        "Pmax_W": pmax,
        "Imp_A": imp,
        "Vmp_V": vmp,
        "FF": ff,
    }