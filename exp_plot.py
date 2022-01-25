import numpy as np
import matplotlib.pyplot as plt

def plot(x, y):

    # plotting the points
    plt.plot(x, y, color='green', linestyle='dashed', linewidth = 3,
             marker='o', markerfacecolor='blue', markersize=12)

    # setting x and y axis range
    plt.ylim(0,)
    plt.xlim(0,)

    # naming the x axis
    plt.xlabel('microservicek [darabszám]')
    # naming the y axis
    plt.ylabel('futási idő [sec]')

    # giving a title to my graph
    plt.title('A futási idő a microservicek darabszámának függvényében')

    # function to show the plot
    plt.show()