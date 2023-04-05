def stats_sizing_function(df, timestep):
    # because E_BTMS is one entry longer than the other entries, the last entry is dropped with [:-2]
    btms_size = df['param: btms size, a,b_sys,b_cap,b_loan,c'].iloc[0]
    cost_a = df['param: btms size, a,b_sys,b_cap,b_loan,c'].iloc[1] * df['P_Grid'].max() 
    cost_b_sys = df['param: btms size, a,b_sys,b_cap,b_loan,c'].iloc[2] * df['P_BTMS'][:].abs().max()
    cost_b_cap = df['param: btms size, a,b_sys,b_cap,b_loan,c'].iloc[3] * sum(df['P_BTMS_Ch'][:-2].abs() * timestep/3600)
    cost_b_loan = df['param: btms size, a,b_sys,b_cap,b_loan,c'].iloc[4] * sum(df['P_BTMS_Ch'][:-2].abs() * timestep/3600)
    cost_b = cost_b_sys + cost_b_cap
    cost_c = df['param: btms size, a,b_sys,b_cap,b_loan,c'].iloc[5] * (sum(df['P_BTMS_Ch'][:-2].abs() * timestep/3600) - sum(df['P_BTMS_DCh'][:-2].abs() * timestep/3600))
    cost_total = cost_a + cost_b + cost_c
    share_cost_a = cost_a / cost_total
    share_cost_b_sys = cost_b_sys / cost_total
    share_cost_b_cap = cost_b_cap / cost_total
    share_cost_b_loan = cost_b_loan / cost_total
    share_cost_b = cost_b / cost_total
    share_cost_c = cost_c / cost_total
    E_Charge = sum(df['P_Charge'][:-2] * timestep/3600)
    c_rate = df['P_BTMS'].abs().max() / btms_size
    cycles_day = sum(df['P_BTMS_DCh'][:-2].abs()*timestep/3600) / btms_size
    btms_ratio = sum(df['P_BTMS_DCh'][:-2].abs()*timestep/3600) / sum(df['P_Charge'][:-2]*timestep/3600)
    load_factor = df['P_Grid'][:-2].mean() / df['P_Grid'][:-2].max()
    btms_peak_to_grid_ratio = df['P_BTMS'].abs().max() / df['P_Grid'].max()
    grid_peak_to_charge_peak_ratio = df['P_Grid'].max() / df['P_Charge'].max()

    return {'btms_size': btms_size, 'cost_a': cost_a, 'cost_b_sys': cost_b_sys, 'cost_b_cap': cost_b_cap, 'cost_b_loan': cost_b_loan, 'cost_b': cost_b, 'cost_c': cost_c, 'cost_total': cost_total, 'share_cost_a': share_cost_a, 'share_cost_b_sys': share_cost_b_sys, 'share_cost_b_cap': share_cost_b_cap, 'share_cost_b_loan': share_cost_b_loan, 'share_cost_b': share_cost_b, 'share_cost_c': share_cost_c, 'E_Charge': E_Charge, 'c_rate': c_rate, 'cycles_day': cycles_day, 'btms_ratio': btms_ratio, 'load_factor': load_factor, 'btms_peak_to_grid_ratio': btms_peak_to_grid_ratio, 'grid_peak_to_charge_peak_ratio': grid_peak_to_charge_peak_ratio}