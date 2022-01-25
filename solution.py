import numpy as np
import time
import random
import excel
from docplex.mp.model import Model

def base():
    # Virtuális gép költségei
    a = np.array([15, 15, 15, 15, 15])

    # Hardvergépek költségei
    b = np.array([100, 100, 100])

    c_ii = []
    m_ii = []

    for i in range(8):
        c_ii.append(random.randint(20, 20))
        m_ii.append(random.randint(20, 20))

    # microservicekhez tartozó CPU és memóriaköltségek
    c_i = np.array(c_ii)
    print(c_i)
    m_i = np.array(m_ii)
    print(m_i)

    # virtuális gépekhez tartozó CPU és memória kapacitások
    c_j = np.array([60, 60, 60, 60, 60])
    m_j = np.array([60, 60, 60, 60, 60])

    # hardvergépekhez tartozó kapacitások
    c_k = np.array([500, 500, 500])
    m_k = np.array([500, 500, 500])

    start_time = time.time()

    # modell példányosítás
    opt_model = Model('Opt')

    # döntési változók microserviceknek
    x_ijk = opt_model.binary_var_cube(c_i.size, c_j.size, c_k.size, name='x_ijk')
    print(x_ijk)

    # döntési változók a backup ms-eknek
    xx_ijk = opt_model.binary_var_cube(c_i.size, c_j.size, c_k.size, name='xx_ijk')
    print(xx_ijk)

    # döntési változók virtuális gépeknek
    y_jk = opt_model.binary_var_matrix(c_j.size, c_k.size, name='y_jk')
    print(y_jk)

    # döntési változók hardvergépeknek
    z_k = opt_model.binary_var_list(c_k.size, name='z_k')

    # constraint no.1: Minden microservicet ki kell szolgálni, azaz minden microservice pontosan 1 gépen fut
    opt_model.add_constraints((sum([x_ijk[i, j, k] for j in range(c_j.size) for k in range(c_k.size)]) == 1
                               for i in range(c_i.size)),
                              names='Task_completion')

    # constraint no.1/2: Minden backupot is ki kell szolgálni
    opt_model.add_constraints((sum([xx_ijk[i, j, k] for j in range(c_j.size) for k in range(c_k.size)]) == 1
                               for i in range(c_i.size)),
                              names='Task_completion_copy')

    # constraint no.2: Ha egy gépen legalább 1 microservice, vagy annak másolata fut, akkor a gép be van kapcsolva
    opt_model.add_constraints(((x_ijk[i, j, k] + xx_ijk[i, j, k]) <= y_jk[j, k]
                               for k in range(c_k.size) for j in range(c_j.size)
                               for i in range(c_i.size)), names='V_on')

    # constraint no.3: A virtuális gép CPU kapacitáshatárának eleget kell tenni
    opt_model.add_constraints((sum(c_i[i]*(x_ijk[i, j, k] + xx_ijk[i, j, k]) for i in range(c_i.size)) <= c_j[j]
                               for j in range(c_j.size) for k in range(c_k.size)),
                              names='CPU_capacity_V')

    # constraint no.4: A virtuális gép memória kapacitáshatárának eleget kell tenni
    opt_model.add_constraints((sum(m_i[i]*(x_ijk[i, j, k] + xx_ijk[i, j, k]) for i in range(c_i.size)) <= m_j[j]
                               for j in range(c_j.size) for k in range(c_k.size)),
                              names='memory_capacity_V')

    # constraint no.5: Ha egy hardvergépen legalább egy virtuális gép fut, akkor a hardvergép be van kapcsolva
    opt_model.add_constraints((y_jk[j, k] <= z_k[k]
                               for j in range(c_j.size) for k in range(c_k.size)),
                              names='H_on')

    # constraint no.6: A hardvergép CPU kapacitásának eleget kell tenni
    opt_model.add_constraints((sum(c_j[j]*y_jk[j, k] for j in range(c_j.size)) <= c_k[k]
                               for k in range(c_k.size)),
                              names='CPU_capacity_H')

    # constraint no.7: A hardvergép cPU kapacitásának eleget kell tenni
    opt_model.add_constraints((sum(m_j[j]*y_jk[j, k] for j in range(m_j.size)) <= m_k[k]
                               for k in range(c_k.size)),
                              names='memory_capacity_H')

    # constraint no.8: Ugyanazon a hardvergépen vagy csak az eredeti, vagy csak a backup ms fut
    for i in range(c_i.size):
        for k in range(c_k.size):
            opt_model.add_constraint(sum((x_ijk[i, j, k] + xx_ijk[i, j, k]) for j in range(c_j.size)) <= 1)

    # Objective function
    obj_fn = sum([a[j]*y_jk[j, k] for j in range(c_j.size) for k in range(c_k.size)]) + \
             100*sum(b[k]*z_k[k] for k in range(c_k.size))

    opt_model.print_information()
    #print(opt_model.export_as_lp_string())

    # solution
    opt_model.set_objective('min', obj_fn)
    #opt_model.print_information()
    #print(opt_model.export_as_lp_string())

    #opt_model.set_time_limit(1) szuboptimális megoldáshoz
    a = opt_model.solve()
    opt_model.print_solution()

    x = []
    xx = []
    yj = []
    zk = []
    xijk = []

    for k in range(c_k.size):
        x.append([])
        for j in range(c_j.size):
            x[k].append([])
            for i in range(c_i.size):
                x[k][j].append(a.get_value(x_ijk[i, j, k]))

    print(x)

    for k in range(c_k.size):
        xx.append([])
        for j in range(c_j.size):
            xx[k].append([])
            for i in range(c_i.size):
                xx[k][j].append(a.get_value(xx_ijk[i, j, k]))

    excel.excel(x, xx, c_i.size, c_j.size, c_k.size)

    print('- -  -   -    -     -      -       -        -         -          -           -')
    print("--- %s seconds ---" % (time.time() - start_time))
    return


def egy_ciklus(parameters, ms_db):

    if ms_db == 0:
        return 0

    time_start = time.time()
    c_ii = []
    m_ii = []
    c_jj = [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000]
    m_jj = [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000]
    c_kk = [99999999, 999999999]
    m_kk = [99999999, 999999999]

    # legalább 2 gép kell legyen
    #c_kk.append(random.randint(parameters[6], parameters[7]))
    #m_kk.append(random.randint(parameters[6], parameters[7]))
    #c_kk.append(random.randint(parameters[6], parameters[7]))
    #m_kk.append(random.randint(parameters[6], parameters[7]))
    #aa = []
    #bb = []
    # töltsük ki az ms kapacitásait
    for i in range(ms_db):
        c_ii.append(random.randint(parameters[2], parameters[3]))
        m_ii.append(random.randint(parameters[2], parameters[3]))

    # V darabszáma és kapacitása fix

    # a ms-k kapacitásai alapján hat meg a H-k darabszámát és kapacitásait
    #while sum(c_kk) < 4*sum(c_ii) or sum(m_kk) < 4*sum(m_ii):
    #    c_kk.append(random.randint(parameters[6], parameters[7]))
    #    m_kk.append(random.randint(parameters[6], parameters[7]))

    # ki kell még tölteni a költségfüggvényeket is
    #for i in range(len(c_jj)):
    #    aa.append(random.randint(parameters[8], parameters[9]))

    #for i in range(len(c_kk)):
    #    bb.append(random.randint(parameters[10], parameters[11]))
    #ezek alapján már rá lehet térni a már meglévő megoldófüggvényre

    # modell példányosítás
    opt_model = Model('Opt')

    c_i = np.array(c_ii)
    c_j = np.array(c_jj)
    c_k = np.array(c_kk)
    m_i = np.array(c_ii)
    m_j = np.array(c_jj)
    m_k = np.array(c_kk)
    a = np.array([10, 10, 10, 10, 10, 10, 10, 10, 10])
    b = np.array([100, 100])

    # döntési változók microserviceknek
    x_ijk = opt_model.binary_var_cube(c_i.size, c_j.size, c_k.size, name='x_ijk')
    print(x_ijk)

    # döntési változók a backup ms-eknek
    xx_ijk = opt_model.binary_var_cube(c_i.size, c_j.size, c_k.size, name='xx_ijk')
    #print(xx_ijk)

    # döntési változók virtuális gépeknek
    y_jk = opt_model.binary_var_matrix(c_j.size, c_k.size, name='y_jk')
    #print(y_jk)

    # döntési változók hardvergépeknek
    z_k = opt_model.binary_var_list(c_k.size, name='z_k')

    # constraint no.1: Minden microservicet ki kell szolgálni, azaz minden microservice pontosan 1 gépen fut
    opt_model.add_constraints((sum([x_ijk[i, j, k] for j in range(c_j.size) for k in range(c_k.size)]) == 1
                               for i in range(c_i.size)),
                              names='Task_completion')

    # constraint no.1/2: Minden backupot is ki kell szolgálni
    opt_model.add_constraints((sum([xx_ijk[i, j, k] for j in range(c_j.size) for k in range(c_k.size)]) == 1
                               for i in range(c_i.size)),
                              names='Task_completion_copy')

    # constraint no.2: Ha egy gépen legalább 1 microservice, vagy annak másolata fut, akkor a gép be van kapcsolva
    opt_model.add_constraints(((x_ijk[i, j, k] + xx_ijk[i, j, k]) <= y_jk[j, k]
                               for k in range(c_k.size) for j in range(c_j.size)
                               for i in range(c_i.size)), names='V_on')

    # constraint no.3: A virtuális gép CPU kapacitáshatárának eleget kell tenni
    opt_model.add_constraints((sum(c_i[i]*(x_ijk[i, j, k] + xx_ijk[i, j, k]) for i in range(c_i.size)) <= c_j[j]
                               for j in range(c_j.size) for k in range(c_k.size)),
                              names='CPU_capacity_V')

    # constraint no.4: A virtuális gép memória kapacitáshatárának eleget kell tenni
    opt_model.add_constraints((sum(m_i[i]*(x_ijk[i, j, k] + xx_ijk[i, j, k]) for i in range(c_i.size)) <= m_j[j]
                               for j in range(c_j.size) for k in range(c_k.size)),
                              names='memory_capacity_V')

    # constraint no.5: Ha egy hardvergépen legalább egy virtuális gép fut, akkor a hardvergép be van kapcsolva
    opt_model.add_constraints((y_jk[j, k] <= z_k[k]
                               for j in range(c_j.size) for k in range(c_k.size)),
                              names='H_on')

    # constraint no.6: A hardvergép CPU kapacitásának eleget kell tenni
    opt_model.add_constraints((sum(c_j[j]*y_jk[j, k] for j in range(c_j.size)) <= c_k[k]
                               for k in range(c_k.size)),
                              names='CPU_capacity_H')

    # constraint no.7: A hardvergép cPU kapacitásának eleget kell tenni
    opt_model.add_constraints((sum(m_j[j]*y_jk[j, k] for j in range(m_j.size)) <= m_k[k]
                               for k in range(c_k.size)),
                              names='memory_capacity_H')

    # constraint no.8: Ugyanazon a hardvergépen vagy csak az eredeti, vagy csak a backup ms fut
    for i in range(c_i.size):
        for k in range(c_k.size):
            opt_model.add_constraint(sum((x_ijk[i, j, k] + xx_ijk[i, j, k]) for j in range(c_j.size)) <= 1)

    # Objective function
    obj_fn = sum([a[j]*y_jk[j, k] for j in range(c_j.size) for k in range(c_k.size)]) + \
             100*sum(b[k]*z_k[k] for k in range(c_k.size))

    #opt_model.print_information()
    #print(opt_model.export_as_lp_string())

    # solution
    opt_model.set_objective('min', obj_fn)
    #opt_model.print_information()
    #print(opt_model.export_as_lp_string())

    a = opt_model.solve()
    opt_model.print_solution()

    print(ms_db)
    print(time.time() - time_start)

    return time.time() - time_start


def sol(parameters):
    start_time1 = time.time()
    ms_db = 0
    time_list = []
    db_list = []
    next_cycle = 1

    #while time.time() - start_time1 < parameters[0]:
    for i in range(40):
        f = open("meres5.txt", "a")
        db_list.append(ms_db)
        start_time1 = time.time()
        a = egy_ciklus(parameters, ms_db)

        time_list.append(a)
        ms_db += 10

        #mentés fájlba
        f.write(str(db_list) + "\n" + str(time_list) + "\n\n")
        f.close()

    # print("Még egy ciklus?")
    #next_cycle = int(input())
    return db_list, time_list
