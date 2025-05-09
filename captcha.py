import random

def generate_captcha():
    """
    Generate a calculus integral CAPTCHA of the form ∫(ax + bx^2) dx
    where 'a' is even, 'b' is divisible by 3, and the result is a 
    single-digit positive integer.
    """
    while True:
        # Generate coefficients
        a = random.choice([2, 4, 6])  # Even coefficient for x
        b = random.choice([3, 6])     # Coefficient divisible by 3 for x^2
        
        # Generate bounds (keep them small to manage result size)
        lower_bound = random.randint(0, 1) 
        upper_bound = lower_bound + random.randint(1, 2) # Keep range small (1 or 2)

        # Calculate integral: ∫(ax + bx^2)dx = (ax^2)/2 + (bx^3)/3
        # Evaluate from lower to upper bound
        
        # Since a is even and b is divisible by 3, divisions will result in integers
        a_div_2 = a // 2
        b_div_3 = b // 3

        upper_res = (a_div_2 * (upper_bound ** 2)) + (b_div_3 * (upper_bound ** 3))
        lower_res = (a_div_2 * (lower_bound ** 2)) + (b_div_3 * (lower_bound ** 3))
        
        result = upper_res - lower_res
        
        # Check if result is a single-digit positive integer
        if 0 < result < 10:
            result = int(result) # Ensure it's an integer type
            break
            
    # Create LaTeX representation for MathJax
    term1 = f"{a}x"
    term2 = f"{b}x^2"
    latex_expr = f"\\int_{{{lower_bound}}}^{{{upper_bound}}} ({term1} + {term2}) \\, dx"
    
    return latex_expr, result