import numpy as np
from scipy.stats import norm
import math

############LOCAL HELPER FUNCTION##############
def norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def black_scholes_price(S, K, T, r, sigma, option_type):
    if T <= 0:
        if option_type == 'call':
            return max(S - K, 0.0)
        else:
            return max(K - S, 0.0)
    
    if S <= 0 or sigma <= 0 or T <= 0:
        if option_type == 'call':
            return max(S - K, 0.0)
        else:
            return max(K - S, 0.0)
    
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    if option_type == 'call':
        price = S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
    else:
        price = K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)
    
    return max(price, 0.0)


def calc_stop_loss_delta_price(open_credit, stop_debit, delta, gamma, theta, t):
    """Calcuate price change of a underlying to hit stop loss as a function of time

    Args:
        open_credit (_type_): _description_
        stop_debit (_type_): _description_
        delta (_type_): _description_
        gamma (_type_): _description_
        theta (_type_): _description_
        t (_type_): _description_
    """
    
    # (1/2)*gamma*delta_S^2 + delta*delta_S + theta*t - delta_V = 0
    # delta_V = stop_debit - open_credit
    
    a = 0.5 * gamma
    b = delta
    c = theta * t - (stop_debit - open_credit)
    
    val_square = b**2 - 4*a*c
    val_square = np.where(val_square < 0, 0, val_square)
    val = np.sqrt(val_square)
    
    delta_S = (-b - val) / (2 * a)
    return delta_S

def get_stop_loss_barrier_curve(s, delta_S: list):
    s_list = [s] * len(delta_S)
    return [s_i - d_i for s_i, d_i in zip(s_list, delta_S)]

#only used to evaluate intraday scenario, ignore drift.
def barrier_crossing_probability(S, S_stop, sigma, T):
    if S_stop >= S or T <= 0:
        return 0
    z = np.log(S/S_stop) / (sigma * np.sqrt(T))
    return 2 * norm.cdf(-z)


def find_spot_price_to_hit_target_price_credit_spread(target_value, K_short, K_long, T, r, sigma, option_type, tol=1e-8, max_iter=1000):
    if option_type == 'put':
        min_value = K_long - K_short
        max_value = 0.0
        if target_value < min_value or target_value > max_value:
            raise ValueError(f"Target value must be in [{min_value:.4f}, {max_value}] for put spread")
    elif option_type == 'call':
        min_value = K_short - K_long
        max_value = 0.0
        if target_value < min_value or target_value > max_value:
            raise ValueError(f"Target value must be in [{min_value:.4f}, {max_value}] for call spread")
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    
    def F(S):
        if option_type == 'put':
            long_leg = black_scholes_price(S, K_long, T, r, sigma, 'put')
            short_leg = black_scholes_price(S, K_short, T, r, sigma, 'put')
        else:
            long_leg = black_scholes_price(S, K_long, T, r, sigma, 'call')
            short_leg = black_scholes_price(S, K_short, T, r, sigma, 'call')
        return (long_leg - short_leg) - target_value
    
    low = 0.0
    high = 2 * max(K_short, K_long)
    
    f_low = F(low)
    f_high = F(high)
    
    if option_type == 'put':
        while f_high < 0:
            high *= 2
            f_high = F(high)
            if high > 1e12:
                raise RuntimeError("Failed to find upper bound for put spread")
    else:
        while f_low > 0:
            low = max(0, low - 0.5 * (high - low))
            if low < 0:
                low = 0
            f_low = F(low)
    
    for _ in range(max_iter):
        mid = (low + high) / 2
        f_mid = F(mid)
        
        if abs(f_mid) < tol or (high - low) < tol:
            return mid
        
        if f_low * f_mid <= 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid
    
    return (low + high) / 2


def find_spot_price_to_hit_target_price_single_option(theo_price, K, T, r, sigma, option_type, tol=1e-8, max_iter=1000):
    if theo_price < 0:
        raise ValueError("Option price cannot be negative")
    
    # Set lower bound to avoid log(0)
    low = 1e-10  # Small positive value instead of zero
    high = 10 * K  # Conservative upper bound
    
    # Adjust high to ensure the root is bracketed
    f_low = black_scholes_price(low, K, T, r, sigma, option_type) - theo_price
    f_high = black_scholes_price(high, K, T, r, sigma, option_type) - theo_price
    
    # For puts: f_low > 0 and f_high < 0 due to negative relationship
    if option_type == 'put':
        while f_high >= 0:  # Put price too low, increase spot
            high *= 2
            f_high = black_scholes_price(high, K, T, r, sigma, option_type) - theo_price
            if high > 1e12:  # Safety break
                raise RuntimeError("Upper bound too high")
    
    # Bisection loop
    for _ in range(max_iter):
        mid = (low + high) / 2
        f_mid = black_scholes_price(mid, K, T, r, sigma, option_type) - theo_price
        
        if abs(f_mid) < tol or (high - low) < tol:
            return mid
        
        if (f_low * f_mid) <= 0:
            high, f_high = mid, f_mid
        else:
            low, f_low = mid, f_mid
    
    return (low + high) / 2