import os,sys


def extract_sourceinfo_fromoutput(filepath):
    with open(filepath,"r") as f:
        s_buf = f.readlines()
    
    sourceinfolist = []
    state_sourceinfo = {}
    filelist = []
    statelist = []

    state_simstate = {}
    simstate = 1
    state = "None"
    prevtrace = ""
    prevsourceline = ""
    funcname = ""
    for index in range(len(s_buf)):
        #if index%100 == 0:
        #    print(index)
        line = s_buf[index]
        line = line.strip()
        if "WARNING ONCE:" in line:
            continue
        if line.startswith("KLEE: "):
            line = line[6:]
        if "ExecutionState &state" in line:
            prevstate = state
            state = line.split(": ")[1]
            if state not in state_sourceinfo:
                statelist += [state]
                state_sourceinfo[state] = ['prevstate: '+prevstate]
                #if prevstate!="None":
                #    state_sourceinfo[state] += state_sourceinfo[prevstate][1:]
                state_simstate[state] = "S"+str(simstate)
                simstate += 1
        if "bb name" in line:
            if len(line.split("-")) >3:
                funcname = line.split("-")[-2]
            #print funcname
        if "line sourceinfo" in line:
            sourceinfo = line.split(" ")[2]
            filename = sourceinfo.split("#")[0].split("/source/")[1]
            #filename = sourceinfo.split("linux.git/tree/")[1].split("?id")[0]
            if ".c" in filename and filename not in filelist:
                filelist += [filename]
            #print sourceinfo
            newline = state+" "+str(index)+" "+funcname+" "+sourceinfo
            newline = newline.replace("https://elixir.bootlin.com/linux/v5.5-rc5/source/", "")
            newline = newline.replace("https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/", "")
            newline = newline.replace("?id=63de37476ebd1e9bab6a9e17186dc5aa1da9ea99", "")
            if len(sourceinfolist)==0 or newline != sourceinfolist[-1]:
                sourceinfolist += [newline]
                state_sourceinfo[state] += [newline]
            #sourceinfolist +=[state+" "+funcname + " "+sourceinfo]
        #if "reach low priority line list" in line or "branches" in line or "BBkey" in line:
        if any(ele in line for ele in ["reach low priority line list", "branches", "BBkey", "terminate", "BB_targetBB_counter[currentBB]", "Forced Br", "Ignore low priority line list"]):
            #if line not in sourceinfolist:
            sourceinfolist += [state+" "+str(index)+" "+funcname+" "+line]
            if state not in state_sourceinfo:
                state_sourceinfo[state] = []
            state_sourceinfo[state] += [state+" "+funcname+" "+line]
        elif "sourcecodeLine:" in line:
            if line != prevsourceline:
                sourceinfolist += [state+" "+str(index)+" "+funcname+" "+line]
                state_sourceinfo[state] += [state+" "+funcname+" "+line]
            prevsourceline = line
        elif "call trace" in line:
            if line != prevtrace:
                sourceinfolist += [state+" "+str(index)+" "+funcname+" "+line]
                state_sourceinfo[state] += [state+" "+str(index)+" "+funcname+" "+line]
                prevtrace = line
        elif "ERROR:" in line or " error: " in line or "terminate" in line or "return value:" in line:
            sourceinfolist += [state+" "+str(index)+" "+funcname+" "+line]
            state_sourceinfo[state] += [state+" "+str(index)+" "+funcname+" "+line]
    
    for i in range(len(sourceinfolist)):
        for state in state_simstate:
            sourceinfolist[i] = sourceinfolist[i].replace(state, state_simstate[state]+" "+state)
    prev_index = 0
    for line in sourceinfolist:
        #print(line)
        S_index = int(line[1:].split(" ")[0])
        if S_index < prev_index:
            print("\n"+line)
        elif "terminate" in line:
            print("\n"+line)
        else:
            print(line)
        prev_index = S_index
    #for state in statelist:
    #    print "\nstate:",state_simstate[state]
    #    for info in state_sourceinfo[state]:
    #        for state in state_simstate:
    #            info = info.replace(state, state_simstate[state])
    #        print info
    print("filelist:\n",filelist)
    return filelist,sourceinfolist

home_path = "/home/zzhan173/repos/Linux_kernel_UC_KLEE/build"
kernel= "/data3/zheng/Linux_bc/4_14_clang11_defconfig/"
outputfile = "./OOBW/c7a91bc7/built-in2.bc"
def link_bclist(filelist):
    link_cmd = home_path+"/llvm-project/build/bin/llvm-link -o " + outputfile

    for filename in filelist:
        bcpath = kernel+filename.replace(".c",".llbc")
        link_cmd = link_cmd + " " + bcpath
    print(link_cmd)

#[cover]: coverage file generated by syzkaller reproducer
#[debugino]: debug file (tmp_o) extracted from vmlinux
def get_cover_lineinfo(cover, debuginfo):
    with open(debuginfo,"r") as f:
        debug_buf = f.readlines()
    st = 0
    ed = len(debug_buf)-1

    with open(cover, "r") as f:
        s_buf = f.readlines()

    #numberlist = []
    funclist = []
    filelist = []
    for line in s_buf:
        number = long(line[:-1],16)
        number = 4*(number/4)
        lineinfos = get_lineinfo(debug_buf, st, ed, number)
        for lineinfo in lineinfos:
            print(str(hex(number))[:-1],lineinfo[0],lineinfo[1])
            if lineinfo[0] not in funclist:
                funclist += [lineinfo[0]]
            if lineinfo[1].split(":")[0] not in filelist and ".c" in lineinfo[1]:
                filelist += [lineinfo[1].split(":")[0]]
        #numberlist += [str(hex(number))[:-1]]
        #print str(hex(number))[:-1]
    print("number of c files:",len(filelist))
    print(filelist)
    print("number of functions:",len(funclist))
    print(funclist)

def get_lineinfo(s_buf, st, ed, number):
    while "(inlined by)" in s_buf[st]:
        st -=1
    while "(inlined by)" in s_buf[ed]:
        ed -=1
    mid = (st+ed)/2
    while "(inlined by)" in s_buf[mid]:
        mid -=1
    #print st,ed,mid
    line = s_buf[mid]
    midnumber = long(line.split(":")[0], 16)
    #print "number:",hex(number),"midenumber:",hex(midnumber)

    if st == mid:
        for lineindex in range(st,ed+1):
            line = s_buf[lineindex]
            if "(inlined by)" in line:
                continue
            midnumber = long(line.split(":")[0], 16)
            if midnumber == number:
                return get_singleinfo(s_buf, lineindex)
        return []

    if midnumber == number:
        return get_singleinfo(s_buf, mid)
    elif midnumber < number:
        return get_lineinfo(s_buf, mid, ed, number)
    else:
        return get_lineinfo(s_buf, st, mid, number)

def get_singleinfo(s_buf, mid):
    totalinfo = []
    line = s_buf[mid]
    funcname = line.split(" ")[1]
    sourceinfo = line[:-1].split(" ")[-1]
    totalinfo += [(funcname, sourceinfo)]

    while "(inlined by)" in s_buf[mid+1]:
        mid +=1
        line = s_buf[mid]
        funcname = line[:-1].split("inlined by) ")[1].split(" ")[0]
        sourceinfo = line[:-1].split(" ")[-1]
        totalinfo += [(funcname, sourceinfo)]
    return totalinfo

# sourceinfolistfile,  output of extract_sourceinfo_fromoutput
def stat_line_numbers(sourceinfolistfile):
    funcline_numbers = {}
    with open(sourceinfolistfile, "r") as f:
        s_buf = f.readlines()
    for line in s_buf:
        if not line.startswith("S"):
            continue
        #print line[:-1].split(" ")
        if len(line[:-1].split(" ")) !=3:
            continue
        state,func,line = line[:-1].split(" ")
        funcline = func+" "+line
        if funcline not in funcline_numbers:
            funcline_numbers[funcline] =1
        else:
            funcline_numbers[funcline] +=1
    funcline_number_list = [(key,funcline_numbers[key]) for key in funcline_numbers]
    funcline_number_list.sort(key=lambda x:x[0])
    funcline_number_list.sort(key=lambda x:x[1],reverse =True)
    for ele in funcline_number_list:
        print(ele)

def get_fork_lines(sourceinfolistfile):
    result = []
    with open(sourceinfolistfile, "r") as f:
        s_buf = f.readlines()
    for line in s_buf:
        if "#n" in line:
            lineinfoline = line
        elif "branches." in line and "(nil)" not in line:
            result += [lineinfoline]
            result += [line]
    for line in result:
        print(line[:-1])
if __name__ == "__main__":
    filelist,sourceinfolist = extract_sourceinfo_fromoutput(sys.argv[1])
    #stat_line_numbers(sys.argv[1])
    #get_fork_lines(sys.argv[1])
    #link_bclist(filelist)
    
    #cover = "/home/zzhan173/Qemu/OOBW/pocs/c7a91bc7/e69ec487b2c7/cover2.0"
    #debuginfo = "/home/zzhan173/Qemu/OOBW/pocs/c7a91bc7/e69ec487b2c7/tmp_o"
    #get_cover_lineinfo(cover, debuginfo)
