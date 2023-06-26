import sys, os
import helper
from multiprocessing import Pool
import json

def run_klee(arguments):
    config, output = arguments
    os.environ['PATH'] = "/home/zzhan173/Linux_kernel_UC_KLEE/install/bin:" + os.environ['PATH']
    os.environ['PATH'] = "/home/zzhan173/Linux_kernel_UC_KLEE/cmake-build/bin:" + os.environ['PATH']

    string1 = "klee --config="+config+" 2>"+output
    print("Start:", string1)
    helper.command(string1)
    print("Done:", string1)
    string1 = "python3 get_lineoutput.py "+ output + "> "+output+"_line"
    print(string1)
    helper.command(string1)

def generate_configlist(PATH):
    configs_dir = PATH + "/configs"

    config_file = PATH+"/configs/config_cover_doms.json"
    with open(config_file, "r") as f:
        config_cover_doms = json.load(f)
    calltrace = config_cover_doms["97_calltrace"]

    new_config_cover_doms = config_cover_doms
    length = 3
    while length < len(calltrace):
        new_calltrace = calltrace[-1*length:]
        new_config_cover_doms["97_calltrace"] = new_calltrace
        new_config_cover_doms["3_entry_function"] = new_calltrace[0]
        new_path = config_file = PATH+"/configs/config_cover_doms_" + str(length) + ".json"
        with open(new_path, "w") as f:
            json.dump(new_config_cover_doms, f, indent=4)
        length += 1


def get_configlist(PATH):
    configs_dir = PATH + "/configs"
    files = os.listdir(configs_dir)

    json_files = [configs_dir + "/" + filename for filename in files if filename.endswith('.json')]
    return json_files

if __name__ == "__main__":
    config_output = []
    with open("/home/zzhan173/Linux_kernel_UC_KLEE/cases/OOBRcases", "r") as f:
        s_buf = f.readlines()
    for syzbothash in s_buf:
        syzbothash = syzbothash[:-1]
        PATH = "/data3/zzhan173/OOBR/"+syzbothash+"/refkernel"
        generate_configlist(PATH)
        configlist = get_configlist(PATH)
        for config in configlist:
        #config = PATH+"/configs/config_cover_doms.json"
        #if os.path.exists(PATH+"/configs/config_cover_doms_updated.json"):
        #    config = PATH+"/configs/config_cover_doms_updated.json"
            output = config.replace(".json", "_output")
            if os.path.exists(config):
                config_output += [(config, output)]

    with Pool(20) as p:
        p.map(run_klee, config_output)
