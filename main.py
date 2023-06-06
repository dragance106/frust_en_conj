# import bare necessities
import concurrent.futures
import multiprocessing
import os
import subprocess as sp
import math

def generate_params():
    """
    Generator of all (n, m, big_delta, small_delta) tuples
    for potential counterexamples to the frustrating energy conjecture.

    :return: a new (n, m, big_delta, small_delta) tuple on each call
    """

    # for n in [11, 12, 13, 14]:      # one comp will work out 11 and 14, the other 12 and 13
    for n in [10]:
        for m in range((n*(n-1))//2, n-2, -1):      # from the densest to the sparsest graphs...
            min_big_delta = max(math.ceil(n-1 - math.log(2*m/n)),
                                math.ceil((n-1)**((n-1)/n)),
                                math.ceil(2*m/n))
            for big_delta in range(min_big_delta, n):
                min_small_delta = max(n+1-big_delta,
                                      math.ceil(2*m/n - math.log(2*m/n)),
                                      math.ceil(-big_delta + math.sqrt(2*m + n*(n-1))))
                for small_delta in range(min_small_delta, math.floor(2*m/n)):
                    yield (n, m, big_delta, small_delta)

def run_frust(param):
    (n, m, big_delta, small_delta) = param
    print(f'Processing params n={n}, m={m}, big_delta={big_delta}, small_delta={small_delta}...')

    # has this part been already processed - maybe computer crashed in the meantime?
    cwd = os.getcwd()
    file_name = f'frust-n={n}-m={m}-big_delta={big_delta}-small_delta={small_delta}'
    graphs_file = os.path.join(cwd, file_name)
    results_file = os.path.join(cwd, f'{file_name}-results.csv')
    if os.path.isfile(results_file) and not os.path.isfile(graphs_file):
        print(f'Params ({n}, {m}, {big_delta}, {small_delta}) are already processed - skipping them for now...')

    # put geng in the current directory and
    # then call it to generate graphs in this part
    cmd = f'./geng -cd{small_delta}D{big_delta} {n} {m} > {file_name}'
    try:
        sp.check_call(cmd, shell=True)
    except sp.CalledProcessError:
        print(f'geng je nesto zafrknuo stvari s parametrima ({n}, {m}, {big_delta}, {small_delta})...')

    # frust.jar should also be in the current directory, so
    # call it to select border-energetic graphs from this part
    cmd = f'java -jar frust.jar {file_name} 1'
    try:
        sp.check_call(cmd, shell=True)
    except sp.CalledProcessError:
        print(f'frust je nesto zafrknuo stvari s parametrima ({n}, {m}, {big_delta}, {small_delta})...')

    # we no longer need graphs from this part
    os.remove(file_name)


if __name__ == '__main__':
    # this would have been the old way
    # params = range(total_parts)
    # with mp.pool(max(mp.cpu_count(), 1)) as pool:
    #     pool.map(run_be, params)

    # the new way using "spawned" subprocesses
    params = generate_params()
    ctx = multiprocessing.get_context('spawn')
    with concurrent.futures.ProcessPoolExecutor(mp_context=ctx) as pool:
       pool.map(run_frust, params)

    # now put all the separate csv files into a single csv file
    combined_data = []
    missing_parts = []
    params = generate_params()      # restart the generator...
    for param in params:
        (n, m, big_delta, small_delta) = param
        file_name = f'frust-n={n}-m={m}-big_delta={big_delta}-small_delta={small_delta}-results.csv'
        try:
            fin = open(file_name, 'r')
            data = fin.read()
            fin.close()
            combined_data.append(data)
            os.remove(file_name)
        except OSError:
            missing_parts.append(param)

    # write everything together
    fout = open(f'be-total-results.csv', 'w')
    for item in combined_data:
        fout.write(item)
    fout.close()

    # write the missing parts as well
    fout = open(f'be-missing-pieces.csv', 'w')
    for item in missing_parts:
        fout.write(str(item) + '\n')
    fout.close()
