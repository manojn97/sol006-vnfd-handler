import os, glob, shutil
import argparse
import sys
import yaml
import json
from pathlib import Path
from distutils.dir_util import copy_tree


#Gets list of vdus
def getVduList(f):
    vdu = []
    properties =f["vnfd"]["vdu"]
    for i in properties:
        vdu.append(i["id"])
    return vdu

#get the name of VNF
def getVnfName(f):
    vnfname =f["vnfd"]["id"]
    return vnfname

#converts yaml to json
def yamlToJson(inputyaml):
    data = {}
    st = {}
    with open(inputyaml) as inputyaml:
        filecontent = yaml.load(inputyaml, Loader=yaml.FullLoader)
    return(filecontent)
    
#creates output file structure
def createStructure(inputDir,outputDir,filename,vduList):
    vnfPath = os.path.normpath(outputDir + "/" +filename)
    descriptorPath = vnfPath+"/Descriptor/"
    Path(vnfPath).mkdir(parents=True, exist_ok=True)
    for items in vduList:
        Path(vnfPath+"/Contains/"+items).mkdir(parents=True, exist_ok=True)
        Path(vnfPath+"/Contains/"+items+"/Definitions/lm").mkdir(parents=True, exist_ok=True)
        copy_tree(inputDir+"/Files/"+items, vnfPath+"/Contains/"+items)     
    Path(descriptorPath).mkdir(parents=True, exist_ok=True)  
    
#create Assembly properties from Config
def createAssemblyPropertiesFromConfProp(confProps,vduList,deploymentLocation):
    finalconf = {}
    valueconf = {}
    for key,val in confProps.items():
        valueconf[key] = {}
        if "instance" in val:
            valueconf[key]["value"] = "${"+str(val)[1:-1]+"}"
        else:
            valueconf[key]["type"] = "string"
        finalconf.update(valueconf)
        if deploymentLocation == "common":
            deploylocation={}
            deploylocation["deployment_location"] = {}
            deploylocation["deployment_location"]["type"]="string"
            finalconf.update(deploylocation)
        else:
            for items in vduList:
                deploylocation={}
                deploylocation[items +"_deployment_location"] = {}
                deploylocation[items +"_deployment_location"]["type"]="string"
                finalconf.update(deploylocation)
    return finalconf

#Create Assembly properties from extcpd
def createAssemblyPropertiesFromextcpd(f):
    extcpd = f["vnfd"]["ext-cpd"]
    finalextcpd = {}
    for items in extcpd:
        finalextcpd[items["id"]+"-vl"] = {}
        finalextcpd[items["id"]+"-vl"]["type"]="string"
        finalextcpd[items["id"]+"-vl"]["description"] = "Network for cpd "+str(items["id"])+" ext-cpd"
        finalextcpd[items["id"]+"-ipaddress"] = {}
        finalextcpd[items["id"]+"-ipaddress"]["type"]="string"
        finalextcpd[items["id"]+"-ipaddress"]["description"] = "Ip Address for cpd "+str(items["id"])+" ext-cpd"
        finalextcpd[items["id"]+"-ipaddress"]["read-only"] = bool("true")
        finalextcpd[items["id"]+"-ipaddress"]["value"] = "${"+str(items["int-cpd"]["vdu-id"])+"."+str(items["int-cpd"]["cpd"])+"-ipaddress}"
    return finalextcpd   
    
#Create Assembly Composition from cpd
def createAssemblyCompositionFromcpd(f,vdu,value):
    composeextcpd = {}
    extcpd = f["vnfd"]["ext-cpd"]
    for items in extcpd:
        composeextcpd["vm_instance_name"]={}
        composeextcpd["vm_instance_name"]["read-only"]=bool("true")
        if vdu == items["int-cpd"]["vdu-id"]:
            keyname = items["int-cpd"]["cpd"]
            composeextcpd[keyname+"-vl"] = {}
            composeextcpd[keyname+"-vl"]["type"]="string"
            composeextcpd[keyname+"-vl"]["description"] = "Network for cpd "+str(items["id"])+" int-cpd"
            if value == "assembly":
                composeextcpd[keyname+"-vl"]["value"] = "${"+items["id"]+"-vl}"
            composeextcpd[keyname+"-ipaddress"]={}
            composeextcpd[keyname+"-ipaddress"]["type"]="string"
            composeextcpd[keyname+"-ipaddress"]["description"] = "Ip Address for cpd "+str(items["id"])+" int-cpd"
            composeextcpd[keyname+"-ipaddress"]["read-only"] = bool("true")
    return composeextcpd

#Create quantity or cluster
def createAssemblyquantity(f,vdu):
    scaling_aspect_flag = False
    min_num_of_instances = number_of_instances = None
    df = f["vnfd"]["df"][0]
    for items in df["vdu-profile"]:
        if items["id"] == vdu:
            min_num_of_instances = df["vdu-profile"][0]["min-number-of-instances"]
            
    for i in df["instantiation-level"]:
        for j in i["vdu-level"]:
            if "vdu-id" in j and j["vdu-id"] == vdu:
                number_of_instances = j["number-of-instances"]

        for items in (i["vdu-level"]):
            for i in df["scaling-aspect"]:
                if "scaling-info" in items and i["aspect-delta-details"]["deltas"][0]["vdu-delta"][0]["id"] == vdu:
                    vdu_delta_instances = i["aspect-delta-details"]["deltas"][0]["vdu-delta"][0]["number-of-instances"]
                    scaling_aspect_flag = True
    
    for i in df["scaling-aspect"]:
        max_scale_level = (i["max-scale-level"])
        if i["aspect-delta-details"]["deltas"][0]["vdu-delta"][0]["id"] == vdu:
            num_of_instance_scaled = i["aspect-delta-details"]["deltas"][0]["vdu-delta"][0]["number-of-instances"]

    if scaling_aspect_flag:
        cluster = {}
        cluster["cluster"] = {}
        cluster["cluster"]["initial-quantity"] = {}
        cluster["cluster"]["minimum-nodes"] = {}
        cluster["cluster"]["maximum-nodes"] = {}
        cluster["cluster"]["scaling-increment"] = {}
        if min_num_of_instances == None or number_of_instances == None:
            cluster["cluster"]["initial-quantity"] = 1
        else:
            #print("Input should contain number-of-instances in instantiation-level")
            cluster["cluster"]["initial-quantity"] = 1
        if number_of_instances == None:
            cluster["cluster"]["minimum-nodes"]  = 1
        else:
            cluster["cluster"]["minimum-nodes"] = number_of_instances
        cluster["cluster"]["maximum-nodes"] = max_scale_level*vdu_delta_instances
        cluster["cluster"]["scaling-increment"] = vdu_delta_instances
        return(cluster)    
    else:
        quantity = {}
        if min_num_of_instances > number_of_instances:
            quantity["quantity"] = min_num_of_instances
            return(quantity)
        else:
            quantity["quantity"] = number_of_instances
            return(quantity)
    

#Create Assembly composition
def createAssemblyComposition(f,vdulist,deploymentLocation):  
    composition = {}
    cpdcomposition = createAssemblyPropertiesFromextcpd(f)
    for items in vdulist:
        #check if necessary
        composition[items]={}
        composition[items]["type"] = "$lmctl:/contains:/"+items+":/descriptor_name"
        composition[items]["meta-type"] = "vdu"
        df = createAssemblyquantity(f,items)
        composition[items].update(df)
        finalconf = {}
        for keys,val in f.items():
            for i in val["vdu"]:
                confProps = i["configurable-properties"]
                for key,val in confProps.items():
                    valueconf = {}
                    valueconf[key] = {}
                    if "vdu-id" in val:
                        valueconf[key]["type"] = "${"+str(val)+"}"
                    else:
                        valueconf[key]["type"] = "string"
                        valueconf[key]["value"] = "${"+str(val)[1:-1]+"}"
                    finalconf.update(valueconf)
        deploylocation={}
        deploylocation["deployment_location"] ={}
        if deploymentLocation == "common":
            deploylocation["deployment_location"]["value"] = "${"+"deployment_location}"
        else:
            deploylocation["deployment_location"]["value"]="${"+items+"_deployment_location}"
        value = "assembly"
        extcpd = createAssemblyCompositionFromcpd(f,items,value)
        finalconf.update(extcpd)
        finalconf.update(deploylocation)
        composition[items]["properties"] = finalconf
    return composition

#Create assembly operations
def createAssemblyOperations(f):
    operations = f["vnfd"]["lifecycle-management-script"]
    Rule = {}
    for items in operations:
        key = {}
        #key = str(items["id"]).split[1]
        key[items["id"].split(".")[1]] = {}
        key[items["id"].split(".")[1]]["source-operation"] = items["id"]
        Rule.update(key)
    return Rule
        
#Create the main assembly file
def createAssembly(f,vduList,deploymentLocation):
    vnfdid = f['vnfd']['id']
    vnfversion = f['vnfd']['version']
    provider = f['vnfd']['provider']
    productName = f['vnfd']['product-name']
    targetVnfm = f['vnfd']['vnfm-info']
    outjson = {}
    outjson["name"] = "assembly::"+vnfdid+"::"+str(vnfversion)
    outjson["description"] = "Provider:"+provider+"; Product Name:"+productName+" ;Target VNFM:"+targetVnfm
    confProps = f["vnfd"]["configurable-properties"]
    confprop = createAssemblyPropertiesFromConfProp(confProps,vduList,deploymentLocation)
    outjson["properties"] = confprop
    extcpdprop = createAssemblyPropertiesFromextcpd(f)
    confprop = outjson["properties"]
    confprop.update(extcpdprop)
    composition = createAssemblyComposition(f,vduList,deploymentLocation)
    outjson["composition"] = composition
    operations = createAssemblyOperations(f)
    outjson["operations"] = operations
    return outjson    

#Create Resource operation
def createResourceOperation(f,vdu):
    operationFlag = False
    for i in (f["vnfd"]["lifecycle-management-script"]):
        if i["id"].split(".")[0] == vdu:
            operationFlag = True
    if operationFlag:
        properties = (f["vnfd"]["lifecycle-management-script"][0]["script-input"])
        operations = {}
        operations["operations"]={}
        rule = ["AddRule","RemovelRule"]
        for i in rule :
            property = {}
            property[i] = {}
            property[i]["properties"]={}
            property[i]["properties"] = properties
            operations["operations"].update(property)
    else:
        operations = {}
        operations["operations"]={}
    return operations

#Create Resource Lifecycle
def createResourceLifecycle():
    lifecycledict = {}
    lifecycledict["lifecycle"] = {}
    drivers = ["ansible","Openstack"]
    lifecycleansible =["Install","Reconfigure"]
    lifecycleopenstack =["Create","Delete"]
    for i in drivers:
        if i == "ansible":
            for j in lifecycleansible:
                ansibledict ={}
                ansibledict[j] = {}
                ansibledict[j]["drivers"] = {}
                ansibledict[j]["drivers"][i] = {}
                ansibledict[j]["drivers"][i]["selector"] ={}
                ansibledict[j]["drivers"][i]["selector"]["infrastructure-type"] ={}
                ansibledict[j]["drivers"][i]["selector"]["infrastructure-type"]=["*"]
                lifecycledict["lifecycle"].update(ansibledict)
        if i == "Openstack":
            for k in lifecycleopenstack:  
                openstackdict = {}     
                openstackdict[k] = {}
                openstackdict[k]["drivers"] = {}
                openstackdict[k]["drivers"][i] = {}
                openstackdict[k]["drivers"][i]["selector"] ={}
                openstackdict[k]["drivers"][i]["selector"]["infrastructure-type"] ={}
                openstackdict[k]["drivers"][i]["selector"]["infrastructure-type"]=["Openstack"]
                lifecycledict["lifecycle"].update(openstackdict)
    return lifecycledict   

#Create main resource file
def createResource(f,vdu,vnfname):
    outresource = {}
    properties = {}
    for keys,val in f.items():
        for i in val["vdu"]:
            if "index" in i["configurable-properties"]:
                confProps = i["configurable-properties"]
    composition ={}
    version = f["vnfd"]["version"]
    outresource["name"]="resource::"+vdu+"-"+vnfname+"::"+str(version)
    outresource["meta-type"]="VDU"
    outresource["description"]="'A VDU: a VDU'"
    lifecycle = createResourceLifecycle()
    composition[vdu]={}
    finalconf = {}
    for key,val in confProps.items():
        valueconf = {}
        valueconf[key] = {}
        if "instance" in val:
            if key == "id" or key == "index":
                newkey = "instance_"+key
                valueconf[newkey] = valueconf.pop(key)
                valueconf[newkey]["type"] = "${"+str(val)[1:-1]+"}"
            else:
                valueconf[key]["type"] = "${"+str(val)[1:-1]+"}"
        else:
            valueconf[key]["type"] = "string"
        finalconf.update(valueconf)
    value = "resource"
    cpd = createAssemblyCompositionFromcpd(f,vdu,value)
    vdudesc = {}
    value = {}
    vdudesc["vdu-compute-desc"] = value
    vdudesc["vdu-compute-desc"]["value"] = {}
    vdudesc["vdu-compute-desc"]["type"] = "map"
    for i in f["vnfd"]["vdu"]:
        if vdu == i["id"]:
            desc_val = i["virtual-compute-desc"]
    for items in f["vnfd"]["virtual-compute-desc"]:
        if items["id"] == desc_val:
            vdudesc["vdu-compute-desc"]["value"].update(items)
    storagedesc = {}
    storagedesc["vdu-storage-desc"] = {}
    storagedesc["vdu-storage-desc"]["value"] = {}
    storagedesc["vdu-storage-desc"]["type"] = "list"
    storageList = []
    for i in f["vnfd"]["vdu"]:
        if vdu == i["id"]:
            desc_val = i["virtual-storage-desc"]
    for items in f["vnfd"]["virtual-storage-desc"]:
        for i in desc_val:
            if items["id"] == i:
                storageList.append(items)
    storagedesc["vdu-storage-desc"]["value"] = storageList
    properties.update(finalconf)
    properties.update(cpd)
    properties.update(vdudesc)
    properties.update(storagedesc)
    operation = createResourceOperation(f,vdu)
    outresource["properties"] = {}
    outresource["properties"].update(properties)
    outresource.update(lifecycle)
    outresource.update(operation)
    return outresource

#Create lmproject file  
def createLmproject(f,vduList,vnfname):
    project ={}
    project["contains"] = {}
    con = {}
    containslist = []
    for i in vduList:
        containsprop = {}
        containsprop["directory"] = i
        containsprop["type"] = "Resource"
        containsprop["resource-manager"] = "brent"
        containsprop["name"] = i
        containsprop = containsprop.copy()
        containslist.append(containsprop)
    project["contains"] = containslist
    project["schema"]= 2.0
    project["version"] = str(f['vnfd']['version'])
    project["type"]="Assembly"
    project["name"]=vnfname
    return project

#Create yaml output from json
def jsonToYaml(outputJsoncontent,outYamlPath):
    outyaml = yaml.safe_dump(yaml.load(json.dumps(outputJsoncontent), Loader=yaml.FullLoader), default_flow_style = False, sort_keys=False)#, Loader = yaml.FullLoader)
    out = os.path.normpath(os.path.join(outYamlPath))
    with open(out, "w") as outfile:
        outfile.write(outyaml)
        
def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputpath","-i", type=str, help="Input path for vnfd file. eg: /sol006-vnfd-handler/resources/input/packages/example/")
    parser.add_argument("--outputpath","-o", type=str, help="Output path for vnf package")
    parser.add_argument("--deploymentlocationtype","-dl", type=str, default="common", help="Provide the kind of deployment location. Possible values [common] [separate]. By default it takes value <common>")
    args = parser.parse_args()
    
    if args.outputpath == None or args.deploymentlocationtype == None:
        return "Output path/deployment Location type is not correct. Correct Usage:: sol006vnfdctl --inputpath <inputpath> --outputpath <outputpath> --deploymentlocationtype <common/separate>"
    elif type(args.outputpath)!= str or type(args.deploymentlocationtype) != str:
        return "Please provide output path and deployment location type value as string"
    elif not os.path.isdir(args.outputpath):
        return "Please provide a valid output path"
    elif not os.path.isdir(args.inputpath):
        return "Please provide the correct path for input Definition folder"
    else:
        inputDir = args.inputpath
        outputDir = args.outputpath
        deploymentlocation  = args.deploymentlocationtype 

    #Path initialization for json data file
    vnfdPath = os.path.normpath(os.path.join(inputDir + "/Definitions/vnfd.yaml"))
    
    #Delete previously created output file
    outDir = os.path.join(outputDir,"output")
    if os.path.exists(outDir):
        shutil.rmtree(outDir)

    #Convert yaml to json
    filecontent = yamlToJson(vnfdPath)

    vduList = getVduList(filecontent)
    vnfname = getVnfName(filecontent)
    createStructure(inputDir,outputDir,vnfname,vduList)

    #Create assembly output
    outputJson = createAssembly(filecontent,vduList,deploymentlocation)
    outDescriptorYaml = os.path.normpath(outputDir + "/" + vnfname + "/Descriptor/assembly.yaml")
    jsonToYaml(outputJson,outDescriptorYaml)

    #Create Resource files
    for items in vduList:
        resourceData  = createResource(filecontent,items,vnfname)
        outResourceYaml = os.path.normpath(outputDir+"/"+ vnfname+"/Contains/"+items+"/Definitions/lm/resource.yaml")
        jsonToYaml(resourceData,outResourceYaml)
    
    #Create lmctl file      
    lmdata = createLmproject(filecontent,vduList,vnfname)
    outlmctlyaml = os.path.normpath(outputDir + "/" + vnfname+"/lmproject.yaml")
    jsonToYaml(lmdata,outlmctlyaml)

    #Removing json files 
    filelist = glob.glob(os.path.join(outputDir, "*.json"))
    for f in filelist:
        os.remove(f)
    #return "Conversion completed!!"
    sys.stdout.write("Conversion completed!!")

main()
