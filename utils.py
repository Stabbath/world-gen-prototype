import random

def gaussian_in_range(mean=0, std_dev=0.4, min=-1, max=1):
    counter = 0
    while counter < 10: # to prevent eternal loops
        value = random.gauss(mean, std_dev)
        if min <= value <= max:
            return value
        else:
            counter += 1
    raise Exception("Bad parameters for gaussian_in_range; could not succeed after 10 tries")
