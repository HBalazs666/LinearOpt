import params
import solution
import exp_plot

print("0: A program a forráskódban beállított értékekkel számol.\n"
      "1: A program exponenciális tesztelést hajt végre az inputok egyeztetése után.")

decision = input()

if decision == "1":
    # A program 0-tól kezdődően 10-esével növeli a ms-ek darabszámát.
    parameters = params.params_in()
    print(parameters)
    darab, time = solution.sol(parameters) # visszaadja az időhosszakat és ms darabszámokat
    exp_plot.plot(darab, time) # megcsinálja a grafikont és el is menti valahová
    print(darab, time)
elif decision =="0":
    solution.base() # az a forráskód, amit kézzel kell átírni egyedi teszteléshez
