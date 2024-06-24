import time

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '▊', printEnd = "\r"):
    time.sleep(0.00001)
    if iteration == total: 
        fill = '█'
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    
    spaceBuffer = " " * (len("100.0") - len(percent))

    print(f'\r{prefix}└┤{bar}| {suffix} [{spaceBuffer}\033[0;33m{percent}%\033[0m]', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print(f'\r{prefix}└┤\x1b[38;2;82;105;64m{bar}\x1b[0m| {suffix} [{spaceBuffer}\033[0;33m{percent}%\033[0m]', end = printEnd)
        print()

# █
# \x1b[38;2;82;105;64m{percent}\x1b[0m
# \x1b[38;2;255;0;0m
# \x1b[0m\n