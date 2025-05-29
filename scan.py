from openpyxl import Workbook
import os
import re

# renaming folder
def edit_folder():
    # for root, dirs, files in os.walk("."):
    #     if "Scan Logs" in root:
    #         for item in files:
    #             match = re.sub(r"CEB9", "FDCCI-CEB", item)
    #             old_file = os.path.join(root,item)
    #             new_file = os.path.join(root,match)
    #             os.rename(old_file, new_file)

    root = os.getcwd()
    for folder in os.listdir("."):

        new_name = f"FDCCI-CEB{folder}"
        os.rename(f"{root}/{folder}", f"{root}/{new_name}")

# get all file directory from the given folder
def get_files(folder):
    scan = []
    entry = []

    for root, dirs, files in os.walk(folder):
        if 'Entry Logs' in root:
            for file in files:
                if re.search(rf"Failed*|entry*", file):
                    entry.append(os.path.join(root,file))
        elif 'Scan Logs' in root:
            for file in files:
                scan.append(os.path.join(root, file))

    return { 'scan': scan, 'entry': entry }

# each file will be analzye base on the folder they are belong
def extract_result(files):

    records = {}

    device_pattern = re.compile(r"\w+-\w+\d+", re.IGNORECASE)
    user_pattern = re.compile(r'(A\w*|P\w*)_', re.IGNORECASE)

    def count_findings(file, keyword):
        with open(file, 'r') as file:
            pattern = re.compile(rf"{keyword}", re.IGNORECASE)
            count = 0
            for line in file:
                if pattern.search(line):
                    count += 1
            return count
        
    def get_infected_count(file):
        with open(file, 'r') as lines:
            pattern = re.compile(r"Infected files: [\d+]", re.IGNORECASE)
            for line in lines:
                if pattern.search(line):
                    match = pattern.search(line)
                    count = match.group().split()[2]
                    return count

    for key, dirs in files.items():
        for file in dirs:
            ext = os.path.splitext(file)[1]
            device_name = device_pattern.search(file).group()
            user = 'default'
            if ext == '.csv':
                if key == 'scan': 
                    count = count_findings(file, '1116')
                    
                elif key == 'entry': 
                    count = count_findings(file, '4625')        
            elif ext == '.txt':
                if key == 'scan':  
                    count = get_infected_count(file)
                    if int(count) > 0:
                        match = user_pattern.search(os.path.basename(file))
                        user = match.group()[:-1].lower()                        
                elif key == 'entry':
                    count = count_findings(file, 'authentication failure')
            
            if device_name in records:
                if key in records[device_name]:
                    records[device_name][key][user] = int(count)
                else:
                    records[device_name][key] = {user: int(count)}
            else:
                records[device_name] = {key: {user: int(count)}}
    
    return records


def generate_excel(data):
    remarks = {
        'scan': {
            'default': 'n/a',
            'ok': 'No infected files all are just false positive'
        },
        'entry': {
            'default': 'No issues',
            'ok': 'Incorrect Password input. No intrusion detected.'
        }
    }

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Log Scan Report"

    worksheet['A1'] = 'Hostname'
    worksheet['B1'] = 'Infected File Count'
    worksheet['C1'] = 'Infected File Remarks'
    worksheet['D1'] = 'Invalid Entry Count'
    worksheet['E1'] = 'Invalid Entry Remarks'


    sheet_data = []
    # format data
    for host in data:
        scan_count = sum([item for item in data[host]['scan'].values()])
        entry_count = data[host]['entry']['default']
        scan_remark = remarks['scan']['ok'] if scan_count > 0 else remarks['scan']['default']
        entry_remark = remarks['entry']['ok'] if entry_count > 0 else remarks['entry']['default']
        sheet_data.append([host, scan_count, scan_remark, entry_count, entry_remark ])

    sheet_data.sort()
    for item in sheet_data:
        worksheet.append(item)
    workbook.save("generated_excel.xlsx")

# execution function
def main():
    input_folder = input("Drag folder here: ")
    folder = re.sub(r"'","",input_folder)
    files = get_files(folder)
    result = extract_result(files)
    generate_excel(result)


if __name__ == '__main__':
    main()