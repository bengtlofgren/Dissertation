import numpy as np
from dataclasses import dataclass, field
from typing import List
from scipy.stats import poisson, norm
import random as rand
import matplotlib as mp
import matplotlib.pyplot as plt
import gc
import pandas as pd


vh_freq = 0.4
@dataclass
class Parameters:
    e_b: float
    e_g: float
    e_b_h: float # defined as proportion of e_b that is h (prob h given e_b)
    e_g_h: float = 0.5
    # tao: float
    number_of_blue: int = 1
    number_of_green: int = 1
    total_n: int = number_of_blue + number_of_green
    h_b: float = 1
    h_g: float = 1
    w_min: float = 0.0
    # Alternatively, ref_dist can be 'normal on normal'
    ref_distribution: str = "Poisson" 
    value_distribution: str = "vh vl"
    vh : float = 2
    vl : float = 0
    alpha: float = 0.5
    alpha_b: float = alpha
    alpha_g: float = alpha
    
    # 0.2549378627974277
    vh_freq: float = vh_freq
    b_v_freq: float = vh_freq
    g_v_freq: float = vh_freq
    
    value_mean: float = vh_freq * vh + (1-vh_freq) * vl
    value_variance: float = (vh ** 2) * vh_freq + (vl ** 2) * (1-vh_freq) - (value_mean ** 2)
    
    b_value_mean: float = value_mean
    g_value_mean: float = value_mean
    
    b_value_variance: float = value_variance
    g_value_variance: float = value_variance
    
    b_value_sigma : float = b_value_variance ** (0.5)
    g_value_sigma : float = g_value_variance ** (0.5)
    
    prob_b : float = number_of_blue / total_n
    prob_b_h : float = prob_b * b_v_freq
    prob_b_l : float = prob_b * (1 - b_v_freq)
    prob_g : float = number_of_green / total_n
    prob_g_h : float = prob_g * (g_v_freq)
    prob_g_l : float = prob_g * (1 - g_v_freq)
    
    # Should be equilibrium employed g_v_freq
    # gh_earning : float = (1 - e_b)*(h_g)*(alpha_g*g_v_freq)
    
    r: float = 1.0
    
    def calculate_threshold(self):
        p = self
        e_b = p.e_b
        e_b_h = p.e_b_h
        e_b_l = 1 - e_b_h
        e_g_h = p.e_g_h
        e_g_l = 1 - e_g_h
        e_g = 1 - e_b
        # figure somehting out here
        # self.alpha_b = self.alpha
        # self.alpha_g = 0.5 + (self.alpha_g - 0.5 + p.tao * e_g)/(1+p.tao)
        # print('alpha b is ')
        # print(self.alpha_b)
        
        if self.ref_distribution == "Poisson":
            b_h_lambda = 1/(p.b_v_freq * p.number_of_blue) * ( (e_b * p.h_b * ((e_b_h * p.alpha_b) + (1-p.alpha_b)*(e_b_l))) + (1-p.h_g)*e_g * ((e_g_h * p.alpha_g) + (e_g_l) * (1-p.alpha_g)))
            b_l_lambda = 1/((1-p.b_v_freq) * p.number_of_blue) * ( (e_b * p.h_b * (((1-e_b_h) * p.alpha_b) + (1-p.alpha_b)*(e_b_h))) + (1-p.h_g)*e_g * (((1-e_g_h)* p.alpha_g) + (e_g_h * (1-p.alpha_g))))
            
            
            g_h_lambda = 1/(p.g_v_freq * p.number_of_green) * ( (e_g * p.h_g * ((e_g_h * p.alpha_g) + (1-p.alpha_g)*(1-e_g_h))) + (1-p.h_b)*e_b * ((e_b_h* p.alpha_b) + (1-e_b_h) * (1-p.alpha_b)))
            g_l_lambda = 1/((1-p.g_v_freq) * p.number_of_green) * ( (e_g * p.h_g * (((1-e_g_h) * p.alpha_g) + (1-p.alpha_g)*(e_g_h))) + (1-p.h_b)*e_b * (((1-e_b_h)* p.alpha_b) + (e_b_h * (1-p.alpha_b))))
            
            
            p_b_h_zero = poisson.pmf(0, b_h_lambda)
            p_b_l_zero = poisson.pmf(0, b_l_lambda)
            
            p_g_h_zero = poisson.pmf(0, g_h_lambda)
            p_g_l_zero = poisson.pmf(0, g_l_lambda)

        
        prob_b = p.number_of_blue / p.total_n
        prob_b_h = prob_b * p.b_v_freq
        prob_b_l = prob_b * (1-p.b_v_freq)
        prob_g = p.number_of_green / p.total_n
        prob_g_h = prob_g * p.g_v_freq
        prob_g_l = prob_g * (1 - p.g_v_freq)
        
        l_h_s = p.w_min - 1
        r_h_s = p.w_min
        
     
        while abs(l_h_s - r_h_s) != 0:
            l_h_s = r_h_s 
            r_h_s = (
                            ( 
                                # Numerator = E(v and in pool)
                                (   (p_b_h_zero*prob_b_h + p_g_h_zero*prob_g_h)* p.vh + p.vl*(prob_b_l + prob_g_l) )
                            )
                        /
                        (
                                # Denominator = Prob of being in the pool
                            (
                                p_b_h_zero * prob_b_h + p_g_h_zero * prob_g_h + prob_b_l + prob_g_l
                            )
                        )
                    )
        self.v_tilda = r_h_s
        threshold = max(self.v_tilda, self.w_min)
        # threshold = 0.1541919477612662
        self.threshold = threshold
        return (threshold)
    
    def hire_continuous(self) -> float:
        p = self
        e_b = p.e_b
        e_g = p.e_g
        e_b_h = p.e_b_h
        e_b_l = 1 - e_b_h
        e_g_h = p.e_g_h
        e_g_l = 1 - e_g_h
        assert self.threshold >= self.w_min, "Make sure to calculate threshold before hiring"
        assert e_b <= 1, "Something wrong with the logic"
        
        if self.ref_distribution == "Poisson":
            b_h_lambda = 1/(p.b_v_freq * p.number_of_blue) * ( (e_b * p.h_b * ((e_b_h * p.alpha_b) + (1-p.alpha_b)*(e_b_l))) + (1-p.h_g)*e_g * ((e_g_h * p.alpha_g) + (e_g_l) * (1-p.alpha_g)))
            self.b_h_lambda = b_h_lambda
            b_l_lambda = 1/((1-p.b_v_freq) * p.number_of_blue) * ( (e_b * p.h_b * (((1-e_b_h) * p.alpha_b) + (1-p.alpha_b)*(e_b_h))) + (1-p.h_g)*e_g * (((1-e_g_h)* p.alpha_g) + (e_g_h * (1-p.alpha_g))))
            self.b_l_lambda = b_l_lambda

            g_h_lambda = 1/(p.g_v_freq * p.number_of_green) * ( (e_g * p.h_g * ((e_g_h * p.alpha_g) + (1-p.alpha_g)*(1-e_g_h))) + (1-p.h_b)*e_b * ((e_b_h* p.alpha_b) + (1-e_b_h) * (1-p.alpha_b)))
            g_l_lambda = 1/((1-p.g_v_freq) * p.number_of_green) * ( (e_g * p.h_g * (((1-e_g_h) * p.alpha_g) + (1-p.alpha_g)*(e_g_h))) + (1-p.h_b)*e_b * (((1-e_b_h)* p.alpha_b) + (e_b_h * (1-p.alpha_b))))


            p_b_h_zero = poisson.pmf(0, b_h_lambda)

            p_b_l_zero = poisson.pmf(0, b_l_lambda)
            
            p_g_h_zero = poisson.pmf(0, g_h_lambda)

            p_g_l_zero = poisson.pmf(0, g_l_lambda)

        # prob hired from pool - same for both men and women
        
        # b_p_h_pool = (
        #     (1 -
        #          ((1 - p_b_h_zero) * p.prob_b_h * p.number_of_blue + (1 - p_g_h_zero) * p.prob_g_h * p.number_of_green)
        #          )
        # /
        #     (
        #     (p_b_h_zero * p.prob_b_h + p.prob_b_l)*p.number_of_blue + (p_g_h_zero * p.prob_g_h + p.prob_g_l)*p.number_of_green
        #     )
        # )
        
        # Commented out p.prob_b_h because it is given if (1-p_g_h_zero)
        b_p_h_pool = (
            (1 -
                 ((1 - p_b_h_zero)*p.b_v_freq * p.number_of_blue + (1 - p_g_h_zero)*p.g_v_freq * p.number_of_green)
                 )
        /
            (
            (1-(1-p_b_h_zero)*p.b_v_freq)*p.number_of_blue + (1-(1-p_g_h_zero)*p.g_v_freq)*p.number_of_green
            )
        )

                
        assert b_p_h_pool >= 0, "whoopsy doopsy"
        
        if b_p_h_pool > 1:
            print('uh oh probability greater than one check logic')
        
        b_p_h_pool = b_p_h_pool if self.v_tilda >= p.w_min else 0
        
        # print(f'{b_p_h_pool} is bph pool')
                     
        
        # g_p_h_pool = b_p_h_pool
        
        # prob hired given blue received a referral
        # Prob v > threshold * 1 + Prob v< threshold and hired from pool
        b_p_h_r = p.prob_b_h
        g_p_h_r = p.prob_g_h
        
        
        b_p_h_not_r = b_p_h_pool
        
        # This is an intersection of sets, we want probability given, thus converted in next step
        non_norm_ebh_next = (p_b_h_zero* b_p_h_not_r + (1-p_b_h_zero)) * p.number_of_blue * p.b_v_freq
        non_norm_egh_next = (p_g_h_zero * b_p_h_pool + (1-p_g_h_zero)) * p.number_of_green * p.g_v_freq

        non_norm_ebl_next = b_p_h_pool * p.number_of_blue * (1-p.b_v_freq)

        theta_b, theta_g = p.b_v_freq*(1-p_b_h_zero), p.g_v_freq*(1-p_g_h_zero)
        
        e_b_next = ((1- theta_b) * b_p_h_not_r + theta_b) * p.number_of_blue
        e_g_next = ((1-theta_g) * b_p_h_not_r + theta_g) * p.number_of_green
        

        # assert non_norm_ebh_next + non_norm_ebl_next == e_b_next, f'''
        # epsilon h = {non_norm_ebh_next},
        # epsilon l = {non_norm_ebl_next},
        # e_b = {e_b_next},
        # SUM = {non_norm_ebh_next + non_norm_ebl_next}'''

        # print((theta_b-theta_g)*(1-b_p_h_not_r))
        
        ebh_next = non_norm_ebh_next/e_b_next
        egh_next = non_norm_egh_next/e_g_next
        
        # print(e_b_next, e_g_next)
        
        # Check logic by employment summing to 1 
        # print(e_g_next + e_b_next)

        # n = p.number_of_blue
        # h_b, h_g, alpha_b, alpha_g = p.h_b, p.h_g, p.alpha_b, p.alpha_g
        # print('lambda bh')
        # print(1/(p.vh_freq * n) * ( (e_b_next * h_b * (ebh_next * alpha_b))))
        # print('lambda bl')
        # print(1/((1-p.vh_freq) * n) * ((e_b_next * h_b * (((1-ebh_next) * alpha_b) + (1-alpha_b)*(ebh_next))) + (1-h_g)*(1-e_b_next) * (egh_next * (1-alpha_g) + (1-egh_next) * (alpha_g))))
        # print('lambda gh')
        # print(1/((p.vh_freq) * n) * (((1-e_b_next) * h_g * ((egh_next * alpha_b) + (1-alpha_b)*(egh_next))) + (1-h_b)*(e_b_next) * (ebh_next * alpha_b + (1-ebh_next) * (1-alpha_g))))
        
        return {'e_b' : e_b_next, 'e_b_h': ebh_next, 'e_g_h': egh_next, 'e_g': e_g_next}

def run_periods(periods = 15, e_b = 0.8, e_g= 0.2, e_b_h = 0.5, e_g_h = 0.5, n= 2.0, alpha_b= 1, alpha_g= 1, 
                      h_b= 1, h_g= 1 ):
    e_b = e_b
    e_b_h = e_b_h
    e_g_h = e_g_h
    periods = periods

        
    for period in range(periods):
        # Testing with alpha b = ebh!!! remove later
        
        p = Parameters(e_b = e_b, e_g = e_g, e_b_h = e_b_h, e_g_h = e_g_h, number_of_blue= n, number_of_green=n, alpha_b= alpha_b, alpha_g= alpha_g, 
                      h_b= h_b, h_g= h_g)
        if period == 0:
            print(f'The parameters for p are {p}')
        print(f'the male employment rate in period {period} is {e_b}')
        print(f'the high skilled male employment is {e_b_h}')
        print(f'the high skilled female emp is {e_g_h}')
        p.calculate_threshold()

        # print(f'the skill threshold for this period is {p.threshold} ')
        # if e_b <= 0.5:
            # print(f'It took {period} generations for the male employment rate to equal the female employment rate')
            # break
        future_emp_dict = p.hire_continuous()
        e_b, e_g, e_b_h, e_g_h = future_emp_dict['e_b'], future_emp_dict['e_g'], future_emp_dict['e_b_h'], future_emp_dict['e_g_h']

        
# vh_freq doesnt work, watch out
def run_period(e_b, e_g, e_b_h: float = 0.5, e_g_h: float = 0.5, n: float = 2.0, 
                n_b : float = None, n_g : float = None, alpha_b: float = 0.8, alpha_g: float = 0.8,
                h_b: float = 0.8, h_g: float = 0.8, vh_freq = 0.7):

    n_b = n_b if n_b else n
    n_g = n_g if n_g else n
    
    p = Parameters(e_b = e_b, e_g =e_g, e_b_h = e_b_h, e_g_h = e_g_h, number_of_blue= n_b, number_of_green=n_g, alpha_b= alpha_b, alpha_g= alpha_g, 
                      h_b= h_b, h_g= h_g, vh_freq = vh_freq)
    
    
    p.calculate_threshold()

    future_emp_dict = p.hire_continuous()
    e_b, e_g, e_b_h, e_g_h = future_emp_dict['e_b'], future_emp_dict['e_g'], future_emp_dict['e_b_h'], future_emp_dict['e_g_h']
    
    return (e_b, e_g, e_b_h, e_g_h)

    # vh_freq doesn't work cuz dataclass, will need to fix
def find_steady_state(e_b_0: float, alpha_b: float, alpha_g: float, h_b: float,  h_g: float,
                        e_b_h_0: float = 0.5, e_g_h_0: float = 0.5, vh_freq = 0.4,
                       n_b : float = None, n_g : float = None, n : float = 2.0,
                       max_iterations: int = 1000, return_iterations: bool = False,
                       verbose = True):
    iteration = 0
    e_b = e_b_0
    e_g = 1 - e_b_0
    e_b_h = e_b_h_0
    e_g_h = e_g_h_0

    n_b = n if not n_b else n_b
    n_g = n if not n_g else n_g

    # Just for return param
    p = Parameters(e_b = e_b, e_g = e_g, e_b_h = e_b_h, e_g_h = e_g_h, number_of_blue= n_b, number_of_green=n_g, alpha_b= alpha_b, alpha_g= alpha_g, 
                      h_b= h_b, h_g= h_g, vh_freq = vh_freq )

    e_b_new = 0
    e_g_new = 0
    ebh_new = 0
    egh_new = 0

    if return_iterations:

        while (abs(e_b - e_b_new) != 0.0 or abs(e_b_h - ebh_new) != 0.0 or abs(e_g_h - egh_new) != 0.0) and iteration < max_iterations:
            iteration +=1
            e_b = e_b_new if e_b_new else e_b
            e_g = e_g_new if e_g_new else e_g
            e_b_h = ebh_new if ebh_new else e_b_h
            e_g_h = egh_new if egh_new else e_g_h
            e_b_new, e_g_new, ebh_new, egh_new = run_period(e_b = e_b, e_g = e_g, e_b_h = e_b_h, e_g_h = e_g_h, n_b = n_b, n_g = n_g, alpha_b=alpha_b, alpha_g=alpha_g, h_b = h_b, h_g = h_g)
    
    else:
        
        while (e_b != e_b_new or e_b_h != ebh_new or e_g_h != egh_new) and iteration < max_iterations:
            iteration +=1
            e_b = e_b_new if e_b_new else e_b
            e_g = e_g_new if e_g_new else e_g            
            e_b_h = ebh_new if ebh_new else e_b_h
            e_g_h = egh_new if egh_new else e_g_h

            # Engdogenising alpha_b
            lambda_bh_n = (1/(p.vh_freq * n) * ( (e_b_new * h_b * ((ebh_new * alpha_b) + (1-alpha_b)*(1-ebh_new))) + (1-h_g)*(1-e_b_new) * ((egh_new * alpha_g) + (1-egh_new) * (1-alpha_g))))
            lambda_gh_n = (1/(p.vh_freq * n) * ( (e_b_new * (1-h_b) * ((ebh_new * alpha_b) + (1-alpha_b)*(1-ebh_new))) + (h_g)*(e_g_new) * ((egh_new * alpha_g) + (1-egh_new) * (1-alpha_g))))

            pbh_2plus = 1 - poisson.pmf(0 , lambda_bh_n) - poisson.pmf(1, lambda_bh_n)
            pgh_2plus = 1 - poisson.pmf(0 , lambda_gh_n) - poisson.pmf(1, lambda_gh_n)
            
            # alpha_b = pbh_2plus + 0.5*(1-pbh_2plus)
            # alpha_g = pgh_2plus + 0.5*(1-pgh_2plus)

            e_b_new, e_g_new, ebh_new, egh_new = run_period(e_b = e_b, e_g= e_g, e_b_h = e_b_h, e_g_h = e_g_h, n_b = n_b, n_g = n_g, alpha_b = alpha_b , alpha_g = alpha_g, h_b = h_b, h_g = h_g)
        
    if iteration == max_iterations:
        if verbose:
            print('max iteration reached')
        if return_iterations:
            return iteration
        else:
            return (e_b_new, e_g_new, ebh_new, egh_new, iteration)
    
    else:
        if verbose:
            print(f'reached in iteration # {iteration}')
        if return_iterations:
            return iteration
        else:
            if verbose:
                p = Parameters(e_b = e_b, e_g=e_g, e_b_h = e_b_h, e_g_h = e_g_h, number_of_blue= n_b, number_of_green=n_g, alpha_b= alpha_b, alpha_g= alpha_g, 
                        h_b= h_b, h_g= h_g )
                print('lambda bh')
                # print(p.vh_freq, n, e_b_new, ebh_new, alpha_b, alpha_g, h_b, h_g)
                lambda_bh_n = (1/(p.vh_freq * n_b) * ( (e_b_new * h_b * ((ebh_new * alpha_b) + (1-alpha_b)*(1-ebh_new))) + (1-h_g)*(1-e_b_new) * ((egh_new * alpha_g) + (1-egh_new) * (1-alpha_g))))
                print(lambda_bh_n)

                print('lambda bl')
                print(1/((1-p.vh_freq) * n_b) * ((e_b_new * h_b * (((1-ebh_new) * alpha_b) + (1-alpha_b)*(ebh_new))) + (1-h_g)*(1-e_b_new) * (egh_new * (1-alpha_g) + (1-egh_new) * (alpha_g))))
                print('lambda gh')
                print(1/((p.vh_freq) * n_g) * (((1-e_b_new) * h_g * ((egh_new * alpha_b) + (1-alpha_b)*(egh_new))) + (1-h_b)*(e_b_new) * (ebh_new * alpha_b + (1-ebh_new) * (1-alpha_g))))
            return (e_b_new, e_g_new, ebh_new, egh_new, iteration)
    
    
def plot_e_b():
    n_array = np.linspace(0.6, 3, num = 10)
    a_b_array = np.linspace(0.5, 1, num = 6)
    a_g_array = np.linspace(0.5, 1, num = 6)
    h_g_array = np.linspace(0.5, 1, num = 6)
    h_b_array = np.linspace(0.5, 1, num = 6)

    e_b_array_dict = {
    # 'n, a_b':
    # [n_array, list(map(lambda a_b: [a_b, np.array([find_steady_state(e_b_0 = 0.8, n=n, alpha_b = a_b, 
    #                                         alpha_g = 0.5, h_b = 1, h_g = 1) for n in n_array])], a_b_array))]
    # ,
    # 'n, h_b, h_g = 0.5':
    #     [n_array, list(map(lambda h_b: [h_b, np.array([find_steady_state(e_b_0 = 0.8, n=n, alpha_b = 1, 
    #                                         alpha_g = 0.5, h_b = h_b, h_g = 0.5) for n in n_array])], h_b_array))]
    # ,
    'a_b, h':
        [a_b_array, list(map(lambda h_b: [h_b, np.array([find_steady_state(e_b_0 = 0.8, n=1.0, alpha_b = a, 
                                            alpha_g = 0.5, h_b = h_b, h_g = h_b) for a in a_b_array])], h_b_array))]
    ,
    'just h_b':
        [h_b_array, list(map(lambda a: [a, np.array([find_steady_state(e_b_0 = 0.8, n=1.0, alpha_b = a, 
                                            alpha_g = 0.5, h_b = h_b, h_g = 0.5) for h_b in h_b_array])], [0.5]*len(a_b_array)))]
    ,
    'h_b, n = 1 and alpha':
        [h_b_array, list(map(lambda a: [a, np.array([find_steady_state(e_b_0 = 0.8, n=1.0, alpha_b = a, 
                                            alpha_g = a, h_b = h_b, h_g = 0.5) for h_b in h_b_array])], a_b_array))]
    ,
    'h_b, alpha_b, alpha_g = 0.5 and h_g =0.5 and n = 1':
        [h_b_array, list(map(lambda a: [a, np.array([find_steady_state(e_b_0 = 0.8, n=1.0, alpha_b = a, 
                                            alpha_g = 0.5, h_b = h_b, h_g = 0.5) for h_b in h_b_array])], a_b_array))]
    }

    for key in e_b_array_dict:
        print(e_b_array_dict[key][1])

    # print(e_b_arrays_n)
    fig, axs = plt.subplots(len(e_b_array_dict),1, figsize = (25,25))

    for j,key in enumerate(e_b_array_dict):
        
        key_list = key.split(',')
        e_b_arrays = e_b_array_dict[key][1]
        x_array = e_b_array_dict[key][0]
        
        for i in range(len(a_b_array)):
            axs[j].plot(x_array, e_b_arrays[i][1], label=f"{key_list[1]} = {e_b_arrays[i][0]}, {key_list[2] if len(key_list) > 2 else ''}")
            axs[j].legend()
            axs[j].set_ylim(0.4,0.8)
            axs[j].set_xlabel(f'{key_list[0]}')
            axs[j].set_ylabel('e_b')
            axs[j].set_title(f'e_b as a function of {key_list[0]}')
    plt.show()

def cartesian_product(*arrays):
    la = len(arrays)
    dtype = np.result_type(*arrays)
    arr = np.empty([len(a) for a in arrays] + [la], dtype=dtype)
    for i, a in enumerate(np.ix_(*arrays)):
        arr[...,i] = a
    arr = arr.reshape(-1, la)
    return arr

def make_df(vh = vh_freq):
    n_array = np.linspace(1, 2, num = 3)
    a_b_array = np.linspace(0.5, 1, num = 6)
    a_g_array = np.linspace(0.5, 1, num = 6)
    h_g_array = np.linspace(0.5, 1, num = 6)
    h_b_array = np.linspace(0.5, 1, num = 6)
    
    cart_product = cartesian_product(n_array, h_b_array, h_g_array, a_b_array, a_g_array)
    
    result_list = []
    for x in cart_product:
        result_list.append(find_steady_state(e_b_0 = 1, n=x[0], alpha_b = x[3], alpha_g = x[4], h_b = x[1], h_g = x[2],
                                            e_b_h_0 = vh, e_g_h_0 = vh, return_iterations=False, verbose = False))
        gc.collect()
    
    print(len(result_list))
    results = np.array(result_list)
    print(results.shape)
    
    print(results[0:2])
    param_cols = cart_product.transpose()
    result_cols = results.transpose()
    result_dict = {
        "n": param_cols[0], "h_b": param_cols[1], "h_g": param_cols[2], "a_b": param_cols[3], "a_g": param_cols[4], 
        "e_b" : result_cols[0], "e_g" : result_cols[1], "ebh" : result_cols[2], "egh" : result_cols[3], "iteration": result_cols[4]
    }

    
    df = pd.DataFrame(result_dict)
    df.to_csv("/Users/uknowit/Dissertation/sim_vh_{vh}.csv".format(vh=vh))
    
    print(df.head())

def plot_iterations():
    n_array = np.linspace(0.6, 3, num = 10)
    a_b_array = np.linspace(0.5, 1, num = 6)
    a_g_array = np.linspace(0.5, 1, num = 6)
    h_g_array = np.linspace(0.5, 1, num = 6)
    h_b_array = np.linspace(0.5, 1, num = 6)

    iteration_no_array_dict = {
            'n, a_b':
        [n_array, list(map(lambda a_b: [a_b, np.array([find_steady_state(e_b_0 = 0.8, n=n, alpha_b = a_b, 
                                                alpha_g = 0.5, h_b = 1, h_g = 1, return_iterations=True) for n in n_array])], a_b_array))]
        ,
        'n, h_b, h_g = 0.5 and alpha_b = 1':
            [n_array, list(map(lambda h_b: [h_b, np.array([find_steady_state(e_b_0 = 0.8, n=n, alpha_b = 1, 
                                                alpha_g = 0.5, h_b = h_b, h_g = 0.5, return_iterations=True) for n in n_array])], h_b_array))]
        ,
        'h_b, n = 2 and alpha':
            [h_b_array, list(map(lambda a: [a, np.array([find_steady_state(e_b_0 = 0.8, n=2.0, alpha_b = a, 
                                                alpha_g = a, h_b = h_b, h_g = 0.5, return_iterations=True) for h_b in h_b_array])], a_b_array))]
        ,
        'h_b, alpha_b, alpha_g = 0.5 and h_g =0.5 and n = 2':
            [h_b_array, list(map(lambda a: [a, np.array([find_steady_state(e_b_0 = 0.8, n=2.0, alpha_b = a, 
                                                alpha_g = 0.5, h_b = h_b, h_g = 0.5, return_iterations=True) for h_b in h_b_array])], a_b_array))]
    }                       

    fig, axs = plt.subplots(len(iteration_no_array_dict),1, figsize = (25,25))

    for j,key in enumerate(iteration_no_array_dict):
        
        key_list = key.split(',')
        iteration_no_arrays = iteration_no_array_dict[key][1]
        x_array = iteration_no_array_dict[key][0]
        
        for i in range(len(a_b_array)):
            axs[j].plot(x_array, iteration_no_arrays[i][1], label=f"{key_list[1]} = {iteration_no_arrays[i][0]}, {key_list[2] if len(key_list) > 2 else ''}")
            axs[j].legend()
            axs[j].set_ylim(0,20)
            axs[j].set_xlabel(f'{key_list[0]}')
            axs[j].set_ylabel('iteration_no')
            axs[j].set_title(f'iteration_no as a function of {key_list[0]}')
    plt.show()

k = 1
print(find_steady_state(e_b_0 = 1.0, e_b_h_0=vh_freq, e_g_h_0 = vh_freq, n_b = 1 ,n_g = 1, alpha_b = 1, alpha_g = 1, h_b = 1, h_g = 1, return_iterations=False))

# make_df(vh = vh_freq)

# run_periods(periods=15, e_b = 0.8, e_g =0.2, e_b_h = 0.8, n=2.0, alpha_b = 1.0, alpha_g = 1, h_b = 1, h_g = 1)

# run_periods()

# plot_e_b()

