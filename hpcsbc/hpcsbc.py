# ------------------------------------------------------------------------
#     HPCSBC (HPC Storage Benchmark Context)
# A tool to evaluate the performance of storage in secondary memory.
# ------------------------------------------------------------------------
# 
# by Fernando de Almeida Silva
# 
# https://www.grid5000.fr/w/Hardware#Clusters:
# site = [cluster1, cluster2, ...]
# Grenoble = [dahu, drac, troll, yeti, servan]
# Lille = [chiclet, chifflot]
# Luxembourg = [petitprince]
# Lyon = [neowise, nova, taurus, sagittaire, hercule, pyxis, orion, gemini, sirius]
# Nancy = [gros, grvingt, grisou, graoully, grappe, grele, graffiti, grimoire, grimani, graphique, grue, gruss, grouille, grat]
# Nantes = [ecotype, econome]
# Rennes = [paravance, parasilo, roazhon5, roazhon13, paranoia, abacus25, roazhon6, roazhon8, roazhon9, roazhon10, roazhon12, abacus22, roazhon11, abacus1, abacus2, abacus3, abacus4, abacus5, abacus8, abacus9, abacus10, abacus11, abacus12, abacus14, abacus16, abacus17, abacus18, abacus19, abacus20, abacus21, roazhon1, roazhon2, roazhon4]
# Sophia = [uvb]
# Toulouse = [estats, montcalm]
#
# updates: https://www.grid5000.fr/w/Hardware
# See nodes (authentication required): https://intranet.grid5000.fr/oar/[site]/drawgantt-svg/

import logging
from pathlib import Path
from datetime import datetime, timezone
from ftplib import FTP

import enoslib as en
import sys 

def send_file_ftp():
    # https://dlptest.com/ftp-test/
    ftp_server = 'ftp.dlptest.com'
    ftp_user = 'dlpuser'
    ftp_password = 'rNrKYTX9g7z3RgJRmxWuGHbeu'

    try:
        # Connect to the FTP server
        with FTP(ftp_server) as ftp:
            ftp.login(ftp_user, ftp_password)

            # Open the local file in binary read mode
            with open(file_name, 'rb') as file:
                # Send the file to the FTP server
                ftp.storbinary(f'STOR {file_name}', file)

            print(f"File '{file_name}' successfully sent to the FTP server.")

    except Exception as e:
        print(f"An error occurred while sending the file: {e}")   

def get_zulu_time():
    # Get current time in UTC
    current_time_utc = datetime.now(timezone.utc)
    zulu_time_day = current_time_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")
    return zulu_time_day[:23] + "Z"


en.init_logging(level=logging.INFO)
en.check()

job_name = Path(__file__).name


send = False
hasHDD = False
hasSSD = False
hasNvme = False

cluster_name = "neowise"
quant_nodes = 2

if len(sys.argv) >= 2:
    cluster_name = sys.argv[1]
    if int(sys.argv[2]) > 0:
        quant_nodes = int(sys.argv[2])

if (quant_nodes) == 1:
    conf = (
        en.G5kConf.from_settings(job_type="exotic", job_name=job_name, walltime="0:02:00")
        .add_machine(roles=["compute", "control"], cluster=cluster_name.lower(), nodes=1)
    )

if (quant_nodes) >= 2:
    conf = (
        en.G5kConf.from_settings(job_type="exotic", job_name=job_name, walltime="0:02:00")
        .add_machine(roles=["compute", "control"], cluster=cluster_name.lower(), nodes=1)
        .add_machine(roles=["compute"], cluster=cluster_name.lower(), nodes=(quant_nodes-1))
    )

# This will validate the configuration, but not reserve resources yet
provider = en.G5k(conf)

# Get actual resources
roles, networks = provider.init()

zulu_time = get_zulu_time()
file_name = f"{cluster_name}_Results_{zulu_time.replace(':', '').replace('.', '')}.csv"
content = "node; cluster; storage; message; work load and time; result; transfer rate;"

with open(file_name, 'w') as file:
    file.write(content)


# Display Zulu time and number of nodes
print("Zulu Time:", zulu_time)
print("Quant Nodes:", quant_nodes)

# test disk type 
results = en.run_command("df -h", roles=roles) 
for result in results:
    # host = result.host.replace(result.host, result.host.split('.', 1)[-1])
    host = result.host.replace(".grid5000.fr", "")
    host = host.replace(".grid5000.fr", "")
        
    # print(result.payload["stdout"])
    if "nvme" in result.payload["stdout"]:
        hasNvme = True
        print(host + " has Nvme!")
    if "/sd" in result.payload["stdout"]:
        hasSSD = True
        print(host + " has SSD!")


if hasSSD:
    # Check SSD performance on all hosts
    results = en.run_command("hdparm -t /dev/sd[a-b][0-9]*", roles=roles) 
    for result in results:    
        host = result.host.replace(".grid5000.fr", "")
        host = host.replace(".grid5000.fr", "")
        host = host.replace(".", ";")
        send = True

        result_message = result.payload['stdout']
        result_message = result_message.replace(":", ";")
        result_message = result_message.replace("=", ";")
        result_message = result_message.replace(";\n", "")
        result_message = result_message.replace("/sec", "/sec;")
        result_message = result_message.replace("/dev/", host + "; /dev/")
        result_message = result_message.replace("/sec;\n", "/sec;")
        result_message = result_message.replace(" Timing", "; Timing")

        print("")
        print(f"\n{result.host}: \n{result.payload['stdout']};")
        with open(file_name, 'a') as file:
            file.write(result_message)


if hasNvme:
    # Check NVMe performance on all hosts
    results = en.run_command("hdparm -t /dev/nvme[0-9]*[0-9]*[0-9]*", roles=roles) 
    for result in results:    
        host = result.host.replace(".grid5000.fr", "")
        host = host.replace(".grid5000.fr", "")
        host = host.replace(".", ";")
        send = True

        result_message = result.payload['stdout']
        result_message = result_message.replace(":", ";")
        result_message = result_message.replace("=", ";")
        result_message = result_message.replace(";\n", "")
        result_message = result_message.replace("/sec", "/sec;")
        result_message = result_message.replace("/dev/", host + "; /dev/")
        result_message = result_message.replace("/sec;\n", "/sec;")
        result_message = result_message.replace(" Timing", "; Timing")

        print("")
        print(f"\n{result.host}: \n{result.payload['stdout']};")
        with open(file_name, 'a') as file:
            file.write(result_message)            

            
if send:            
    # Send the file via FTP
    send_file_ftp()

# Release all Grid'5000 resources
provider.destroy()


